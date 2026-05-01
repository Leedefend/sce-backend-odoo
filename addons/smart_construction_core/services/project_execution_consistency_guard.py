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
    REQUIRED_PROJECT_FIELDS = (
        ("name", "项目名称"),
        ("project_code", "项目编码"),
        ("date_start", "计划开工日"),
        ("lifecycle_state", "生命周期状态"),
    )

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
            "root_task_count": 0,
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
            if "parent_id" not in getattr(task, "_fields", {}) or not getattr(task, "parent_id", False):
                counts["root_task_count"] += 1
        counts["followup_activity_count"] = len(self._followup_activities(project))
        counts["scope"] = self.SCOPE
        return counts

    def _required_project_field_summary(self, project) -> dict:
        missing = []
        for field_name, label in self.REQUIRED_PROJECT_FIELDS:
            if field_name not in getattr(project, "_fields", {}):
                continue
            value = getattr(project, field_name, False)
            if not value:
                missing.append({"field": field_name, "label": label})
        manager_assigned = False
        for field_name in ("user_id", "manager_id"):
            if field_name in getattr(project, "_fields", {}) and getattr(project, field_name, False):
                manager_assigned = True
                break
        if not manager_assigned:
            missing.append({"field": "manager_assignment", "label": "项目经理/负责人"})
        return {
            "missing": missing,
            "missing_fields": [str(item.get("field") or "") for item in missing],
        }

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

    def validate_followup_activity(self, project) -> tuple[bool, str, dict]:
        summary = self.summary(project)
        project_state = ProjectExecutionStateMachine.normalize_state(getattr(project, "sc_execution_state", "ready"))
        activity_count = int(summary.get("followup_activity_count") or 0)
        if activity_count > 1:
            return False, "EXECUTION_PROJECT_ACTIVITY_DRIFT", summary
        if project_state == "in_progress" and activity_count != 1:
            return False, "EXECUTION_PROJECT_ACTIVITY_DRIFT", summary
        if project_state == "done" and activity_count != 0:
            return False, "EXECUTION_PROJECT_ACTIVITY_DRIFT", summary
        return True, "", summary

    def pilot_precheck(self, project) -> dict:
        summary = self.summary(project)
        field_summary = self._required_project_field_summary(project)
        alignment_ok, alignment_reason_code, _ = self.validate_state_alignment(project)
        activity_ok, activity_reason_code, _ = self.validate_followup_activity(project)
        lifecycle_state = str(getattr(project, "lifecycle_state", "") or "").strip().lower()
        execution_state = ProjectExecutionStateMachine.normalize_state(getattr(project, "sc_execution_state", "ready"))
        open_count = int(summary.get("task_open_count") or 0)
        single_open_ok = (execution_state == "done" and open_count == 0) or open_count == 1
        checks = [
            {
                "key": "root_task",
                "label": "根任务已初始化",
                "status": "pass" if int(summary.get("root_task_count") or 0) >= 1 else "fail",
                "reason_code": "" if int(summary.get("root_task_count") or 0) >= 1 else "PILOT_ROOT_TASK_MISSING",
                "message": "已检测到项目根任务。"
                if int(summary.get("root_task_count") or 0) >= 1
                else "试点前必须至少存在一个项目根任务。",
            },
            {
                "key": "single_open_task",
                "label": "单开放任务约束",
                "status": "pass" if single_open_ok else "fail",
                "reason_code": "" if single_open_ok else "PILOT_SINGLE_OPEN_TASK_REQUIRED",
                "message": "当前满足 single_open_task_only。"
                if open_count == 1
                else "当前执行已完成，开放任务已归零。"
                if execution_state == "done" and open_count == 0
                else "试点版只允许 1 个开放任务，请收口到单任务后再推进。",
            },
            {
                "key": "execution_task_consistency",
                "label": "执行态与任务态一致",
                "status": "pass" if alignment_ok else "fail",
                "reason_code": "" if alignment_ok else alignment_reason_code,
                "message": "project.execution 与 project.task 状态一致。"
                if alignment_ok
                else "project.execution 与 project.task 状态不一致，需要先校正。",
            },
            {
                "key": "required_fields",
                "label": "关键字段完整",
                "status": "pass" if not field_summary["missing_fields"] else "fail",
                "reason_code": "" if not field_summary["missing_fields"] else "PILOT_REQUIRED_FIELDS_MISSING",
                "message": "试点必填字段已完整。"
                if not field_summary["missing_fields"]
                else "仍缺少关键字段：%s。"
                % "、".join(str(item.get("label") or item.get("field") or "") for item in field_summary["missing"]),
            },
            {
                "key": "activity_rule",
                "label": "Activity 规则一致",
                "status": "pass" if activity_ok else "fail",
                "reason_code": "" if activity_ok else activity_reason_code,
                "message": "mail.activity 跟进规则一致。"
                if activity_ok
                else "mail.activity 数量或状态与当前执行态不一致。",
            },
            {
                "key": "lifecycle_state",
                "label": "项目生命周期允许试点",
                "status": "pass" if lifecycle_state not in {"paused", "closed", "done", "closing", "warranty"} else "fail",
                "reason_code": ""
                if lifecycle_state not in {"paused", "closed", "done", "closing", "warranty"}
                else "PILOT_LIFECYCLE_STATE_BLOCKED",
                "message": "当前生命周期允许试点推进。"
                if lifecycle_state not in {"paused", "closed", "done", "closing", "warranty"}
                else "当前项目生命周期不允许作为 v0.1 首轮试点。",
            },
        ]
        failed = [item for item in checks if str(item.get("status") or "") != "pass"]
        primary = failed[0] if failed else {}
        return {
            "checks": checks,
            "summary": {
                **summary,
                "overall_state": "ready" if not failed else "blocked",
                "passed_count": len(checks) - len(failed),
                "failed_count": len(failed),
                "failed_reason_codes": [str(item.get("reason_code") or "") for item in failed if str(item.get("reason_code") or "")],
                "primary_reason_code": str(primary.get("reason_code") or ""),
                "primary_message": str(primary.get("message") or "试点前检查通过，可进入首轮试点。"),
                "missing_fields": list(field_summary["missing_fields"]),
                "single_open_task_only": True,
            },
        }

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
