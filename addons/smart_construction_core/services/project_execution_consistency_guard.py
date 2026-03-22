# -*- coding: utf-8 -*-
from __future__ import annotations

from odoo.addons.smart_construction_core.services.project_execution_state_machine import (
    ProjectExecutionStateMachine,
)
from odoo.addons.smart_construction_core.services.project_task_state_support import (
    ProjectTaskStateSupport,
)


class ProjectExecutionConsistencyGuard:
    FOLLOWUP_SUMMARY = "执行推进跟进"
    SCOPE = "single_open_task_only"

    def __init__(self, env):
        self.env = env

    def _project_tasks(self, project):
        task_model = self.env["project.task"] if "project.task" in self.env else None
        if task_model is None or not project:
            return self.env["project.task"].browse([])
        return task_model.search([("project_id", "=", int(project.id))], order="priority desc, id asc")

    def _followup_activities(self, project):
        activity_model = self.env["mail.activity"] if "mail.activity" in self.env else None
        if activity_model is None or not project:
            return self.env["mail.activity"].browse([])
        return activity_model.sudo().search(
            [
                ("res_model", "=", "project.project"),
                ("res_id", "=", int(project.id)),
                ("summary", "=", self.FOLLOWUP_SUMMARY),
            ],
            order="id asc",
        )

    def summary(self, project) -> dict:
        tasks = self._project_tasks(project)
        counts = {
            "task_total": len(tasks),
            "task_open_count": 0,
            "task_ready_count": 0,
            "task_in_progress_count": 0,
            "task_done_count": 0,
            "task_cancelled_count": 0,
        }
        for task in tasks:
            state = ProjectTaskStateSupport.normalize(getattr(task, "sc_state", "draft"))
            if ProjectTaskStateSupport.is_open(state):
                counts["task_open_count"] += 1
            if state == "ready":
                counts["task_ready_count"] += 1
            elif state == "in_progress":
                counts["task_in_progress_count"] += 1
            elif state == "done":
                counts["task_done_count"] += 1
            elif state == "cancelled":
                counts["task_cancelled_count"] += 1
        counts["followup_activity_count"] = len(self._followup_activities(project))
        counts["scope"] = self.SCOPE
        return counts

    def validate_scope(self, project, *, from_state: str, to_state: str) -> tuple[bool, str, dict]:
        summary = self.summary(project)
        open_count = int(summary.get("task_open_count") or 0)
        in_progress_count = int(summary.get("task_in_progress_count") or 0)
        if from_state == "done":
            return True, "", summary
        if int(summary.get("task_total") or 0) <= 0:
            return False, "EXECUTION_TASK_MISSING", summary
        if to_state in {"ready", "in_progress"} and open_count > 1:
            return False, "EXECUTION_SCOPE_MULTI_OPEN_TASKS_UNSUPPORTED", summary
        if to_state == "done":
            if in_progress_count <= 0:
                return False, "EXECUTION_TASK_NOT_IN_PROGRESS", summary
            if in_progress_count > 1 or open_count > 1:
                return False, "EXECUTION_SCOPE_MULTI_OPEN_TASKS_UNSUPPORTED", summary
        return True, "", summary

    def validate_state_alignment(self, project) -> tuple[bool, str, dict]:
        summary = self.summary(project)
        project_state = ProjectExecutionStateMachine.normalize_state(getattr(project, "sc_execution_state", "ready"))
        open_count = int(summary.get("task_open_count") or 0)
        in_progress_count = int(summary.get("task_in_progress_count") or 0)
        if int(summary.get("task_total") or 0) <= 0:
            return False, "EXECUTION_TASK_MISSING", summary
        if project_state == "ready" and in_progress_count > 0:
            return False, "EXECUTION_PROJECT_TASK_STATE_DRIFT", summary
        if project_state == "in_progress" and in_progress_count != 1:
            return False, "EXECUTION_PROJECT_TASK_STATE_DRIFT", summary
        if project_state == "done" and open_count > 0:
            return False, "EXECUTION_PROJECT_TASK_STATE_DRIFT", summary
        return True, "", summary

    def reconcile_followup_activity(self, project, *, project_state: str | None = None) -> tuple[bool, str, dict]:
        if not project or not hasattr(project, "activity_schedule"):
            return True, "", self.summary(project)
        project_state = ProjectExecutionStateMachine.normalize_state(
            project_state or getattr(project, "sc_execution_state", "ready")
        )
        activities = self._followup_activities(project)
        summary = self.summary(project)
        expected_count = (
            1 if project_state in {"ready", "in_progress", "blocked"} and int(summary.get("task_open_count") or 0) > 0 else 0
        )
        if expected_count <= 0:
            try:
                if activities:
                    activities.unlink()
            except Exception:
                return False, "EXECUTION_PROJECT_ACTIVITY_DRIFT", self.summary(project)
            return True, "", self.summary(project)

        activity_type = self.env.ref("mail.mail_activity_data_todo", raise_if_not_found=False)
        if not activity_type:
            return False, "EXECUTION_PROJECT_ACTIVITY_DRIFT", summary
        user_id = int(getattr(getattr(project, "user_id", None), "id", 0) or self.env.user.id or 0)
        if user_id <= 0:
            return False, "EXECUTION_PROJECT_ACTIVITY_DRIFT", summary
        try:
            if len(activities) <= 0:
                project.sudo().activity_schedule(
                    activity_type_id=int(activity_type.id),
                    summary=self.FOLLOWUP_SUMMARY,
                    note="执行状态为“%s”，请继续按任务推进。"
                    % ProjectExecutionStateMachine.STATE_LABEL.get(project_state, project_state),
                    user_id=user_id,
                )
            elif len(activities) > 1:
                activities[1:].unlink()
        except Exception:
            return False, "EXECUTION_PROJECT_ACTIVITY_DRIFT", self.summary(project)
        return True, "", self.summary(project)
