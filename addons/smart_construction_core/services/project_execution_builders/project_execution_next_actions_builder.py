# -*- coding: utf-8 -*-
from __future__ import annotations

from odoo.addons.smart_construction_core.services.project_dashboard_builders.base import BaseProjectBlockBuilder
from odoo.addons.smart_construction_core.services.project_execution_state_machine import (
    ProjectExecutionStateMachine,
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
        task_model = self._model("project.task")
        task_domain = self._project_domain("project.task", project)
        task_total = 0
        active_count = 0
        done_count = 0
        if task_model is not None:
            try:
                task_total = int(task_model.search_count(task_domain))
                active_count = int(task_model.search_count(task_domain + [("sc_state", "in", ["ready", "in_progress"])]))
                done_count = int(task_model.search_count(task_domain + [("sc_state", "=", "done")]))
            except Exception:
                task_total = 0
                active_count = 0
                done_count = 0
        if task_total <= 0:
            action["state"] = "blocked"
            action["reason_code"] = "EXECUTION_TASK_MISSING"
            action["hint"] = "当前状态：执行任务缺失。下一步：先在 Odoo 项目任务中创建或准备任务。"
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
                    "task_active_count": active_count,
                    "task_done_count": done_count,
                },
            },
        )
