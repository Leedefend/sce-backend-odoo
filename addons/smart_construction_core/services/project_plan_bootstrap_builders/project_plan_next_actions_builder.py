# -*- coding: utf-8 -*-
from __future__ import annotations

from odoo.addons.smart_construction_core.services.project_dashboard_builders.base import BaseProjectBlockBuilder


class ProjectPlanNextActionsBuilder(BaseProjectBlockBuilder):
    block_key = "block.project.plan_next_actions"
    block_type = "action_list"
    title = "计划下一步"
    required_groups = ()

    def build(self, project=None, context=None):
        visibility = self._visibility()
        empty_data = {"actions": [], "summary": {}}
        if not visibility.get("allowed"):
            return self._envelope(state="forbidden", visibility=visibility, data=empty_data)
        if not project:
            return self._envelope(state="empty", visibility=visibility, data=empty_data)

        task_total = self._safe_count("project.task", self._project_domain("project.task", project))
        milestone_total = self._safe_count("project.milestone", self._project_domain("project.milestone", project))
        execution_state = "available"
        reason_code = "PLAN_READY_FOR_EXECUTION"
        hint = "计划准备就绪，可进入执行场景。"
        if task_total <= 0 and milestone_total <= 0:
            execution_state = "blocked"
            reason_code = "PLAN_INPUT_INCOMPLETE"
            hint = "计划任务与里程碑尚未成形，暂不建议进入执行。"

        actions = [
            {
                "key": "execution_enter",
                "label": "进入项目执行",
                "hint": hint,
                "intent": "project.execution.enter",
                "params": {
                    "project_id": int(project.id),
                    "source": "project.plan_bootstrap.next_actions",
                },
                "state": execution_state,
                "reason_code": reason_code,
                "source": "phase_13_b1",
            }
        ]
        return self._envelope(
            state="ready",
            visibility=visibility,
            data={
                "actions": actions,
                "summary": {
                    "count": len(actions),
                    "available_count": len([row for row in actions if str(row.get("state") or "") == "available"]),
                    "blocked_count": len([row for row in actions if str(row.get("state") or "") == "blocked"]),
                },
            },
        )
