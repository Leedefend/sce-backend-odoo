# -*- coding: utf-8 -*-
from __future__ import annotations

from odoo.addons.smart_construction_core.services.project_dashboard_builders.base import BaseProjectBlockBuilder


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

        task_total = self._safe_count("project.task", self._project_domain("project.task", project))
        blocked_count = 0
        if self._model_has_fields("project.task", ["kanban_state"]):
            blocked_count = self._safe_count(
                "project.task",
                self._project_domain("project.task", project) + [("kanban_state", "=", "blocked")],
            )
        state = "ready"
        reason_code = "EXECUTION_ADVANCE_READY"
        hint = "执行条件已满足，可推进执行。"
        if task_total <= 0:
            state = "blocked"
            reason_code = "EXECUTION_TASKS_MISSING"
            hint = "当前无执行任务，暂不可推进。"
        elif blocked_count > 0:
            state = "blocked"
            reason_code = "EXECUTION_TASKS_BLOCKED"
            hint = "存在阻塞任务，请先处理阻塞项。"

        actions = [
            {
                "key": "execution_advance",
                "label": "推进执行",
                "hint": hint,
                "intent": "project.execution.advance",
                "params": {
                    "project_id": int(project.id),
                    "source": "project.execution.next_actions",
                },
                "state": state,
                "reason_code": reason_code,
                "source": "phase_13_c1",
            }
        ]
        return self._envelope(
            state="ready",
            visibility=visibility,
            data={
                "actions": actions,
                "summary": {
                    "count": len(actions),
                    "ready_count": len([row for row in actions if str(row.get("state") or "") == "ready"]),
                    "blocked_count": len([row for row in actions if str(row.get("state") or "") == "blocked"]),
                },
            },
        )
