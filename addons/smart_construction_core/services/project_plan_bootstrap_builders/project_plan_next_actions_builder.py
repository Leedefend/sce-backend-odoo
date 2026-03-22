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
        current_state = "plan_ready"
        current_state_label = "计划准备已就绪"
        next_step_label = "进入执行推进"
        reason_code = "PLAN_READY_FOR_EXECUTION"
        hint = "当前状态：计划准备已就绪。下一步：进入执行推进。"
        if task_total <= 0 and milestone_total <= 0:
            execution_state = "blocked"
            current_state = "plan_input_incomplete"
            current_state_label = "计划输入待补齐"
            next_step_label = "先补齐计划任务或里程碑"
            reason_code = "PLAN_INPUT_INCOMPLETE"
            hint = "当前状态：计划任务与里程碑尚未成形。下一步：先补齐计划输入，再进入执行推进。"

        actions = [
            {
                "key": "execution_enter",
                "label": "下一步：进入执行推进",
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
                    "current_state": current_state,
                    "current_state_label": current_state_label,
                    "next_step_label": next_step_label,
                },
            },
        )
