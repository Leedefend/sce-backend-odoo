# -*- coding: utf-8 -*-
from __future__ import annotations

from odoo.addons.smart_construction_core.services.project_dashboard_builders.base import BaseProjectBlockBuilder
from odoo.addons.smart_construction_core.services.project_execution_consistency_guard import (
    ProjectExecutionConsistencyGuard,
)
from odoo.addons.smart_construction_core.services.project_execution_state_machine import (
    ProjectExecutionStateMachine,
)
from odoo.addons.smart_construction_core.services.project_task_state_support import (
    ProjectTaskStateSupport,
)


class ProjectExecutionNextActionsBuilder(BaseProjectBlockBuilder):
    block_key = "block.project.execution_next_actions"
    block_type = "action_list"
    title = "执行下一步"
    required_groups = ()

    def build(self, project=None, context=None):
        visibility = self._visibility()
        empty_data = {"actions": [], "summary": {}}
        if not visibility.get("allowed"):
            return self._envelope(state="forbidden", visibility=visibility, data=empty_data)
        if not project:
            return self._envelope(state="empty", visibility=visibility, data=empty_data)

        current_state = ProjectExecutionStateMachine.normalize_state(getattr(project, "sc_execution_state", "ready"))
        action = ProjectExecutionStateMachine.action_payload(int(project.id), current_state)
        guard = ProjectExecutionConsistencyGuard(self.env)
        task_model = self._model("project.task")
        task_domain = self._project_domain("project.task", project)
        task_total = 0
        active_count = 0
        done_count = 0
        open_count = 0
        in_progress_count = 0
        followup_count = 0
        consistency_state = "blocked"
        consistency_reason_code = "EXECUTION_TASK_MISSING"
        if task_model is not None:
            try:
                task_total = int(task_model.search_count(task_domain))
                active_count = int(task_model.search_count(task_domain + ProjectTaskStateSupport.active_domain()))
                done_count = int(task_model.search_count(task_domain + ProjectTaskStateSupport.done_domain()))
                open_count = int(task_model.search_count(task_domain + ProjectTaskStateSupport.open_domain()))
                in_progress_count = int(task_model.search_count(task_domain + [("sc_state", "=", "in_progress")]))
            except Exception:
                task_total = 0
                active_count = 0
                done_count = 0
                open_count = 0
                in_progress_count = 0
        if task_total <= 0:
            action["state"] = "blocked"
            action["reason_code"] = "EXECUTION_TASK_MISSING"
            action["hint"] = "当前状态：执行任务缺失。下一步：先在 Odoo 项目任务中创建或准备任务。"
        else:
            pilot = guard.pilot_precheck(project)
            pilot_summary = pilot.get("summary") if isinstance(pilot.get("summary"), dict) else {}
            scope_ok, scope_reason_code, summary = guard.validate_scope(
                project,
                from_state=current_state,
                to_state=str(action.get("target_state") or current_state),
            )
            alignment_ok, alignment_reason_code, _ = guard.validate_state_alignment(project)
            pilot_ok = str(pilot_summary.get("overall_state") or "") == "ready"
            pilot_reason_code = str(pilot_summary.get("primary_reason_code") or "")
            pilot_message = str(pilot_summary.get("primary_message") or "")
            if not pilot_ok:
                action["state"] = "blocked"
                action["reason_code"] = pilot_reason_code or "PILOT_PRECHECK_BLOCKED"
                action["hint"] = pilot_message or "当前未通过试点前检查，请先处理阻断项。"
            elif not scope_ok:
                action["state"] = "blocked"
                action["reason_code"] = scope_reason_code
                action["hint"] = "当前超出 execution.advance 受控范围：仅支持单个开放任务推进。"
            elif not alignment_ok and current_state != "ready":
                action["state"] = "blocked"
                action["reason_code"] = alignment_reason_code
                action["hint"] = "当前 project/task 状态不一致，请先校正后再推进。"
            followup_count = int(summary.get("followup_activity_count") or 0)
            consistency_state = "consistent" if pilot_ok and scope_ok and (alignment_ok or current_state == "ready") else "blocked"
            consistency_reason_code = "" if consistency_state == "consistent" else (pilot_reason_code or scope_reason_code or alignment_reason_code)
            pilot_state = str(pilot_summary.get("overall_state") or "blocked")
            pilot_failed_count = int(pilot_summary.get("failed_count") or 0)
            pilot_primary_reason_code = pilot_reason_code
            pilot_primary_message = pilot_message
        if task_total <= 0:
            pilot_state = "blocked"
            pilot_failed_count = 1
            pilot_primary_reason_code = "EXECUTION_TASK_MISSING"
            pilot_primary_message = "请先创建项目根任务，并确保仅保留一个开放任务。"
        actions = [action]
        return self._envelope(
            state="ready",
            visibility=visibility,
            data={
                "actions": actions,
                "summary": {
                    "count": len(actions),
                    "ready_count": len([row for row in actions if str(row.get("state") or "") == "ready"]),
                    "blocked_count": len([row for row in actions if str(row.get("state") or "") == "blocked"]),
                    "current_state": current_state,
                    "current_state_label": ProjectExecutionStateMachine.STATE_LABEL.get(current_state, current_state),
                    "allowed_targets": list(ProjectExecutionStateMachine.allowed_targets(current_state)),
                    "next_step_label": str(action.get("label") or ""),
                    "task_total": task_total,
                    "task_open_count": open_count,
                    "task_active_count": active_count,
                    "task_in_progress_count": in_progress_count,
                    "task_done_count": done_count,
                    "followup_activity_count": followup_count,
                    "consistency_state": consistency_state,
                    "consistency_reason_code": consistency_reason_code,
                    "execution_scope": ProjectExecutionConsistencyGuard.SCOPE,
                    "pilot_precheck_state": pilot_state,
                    "pilot_failed_count": pilot_failed_count,
                    "pilot_primary_reason_code": pilot_primary_reason_code,
                    "pilot_primary_message": pilot_primary_message,
                },
            },
        )
