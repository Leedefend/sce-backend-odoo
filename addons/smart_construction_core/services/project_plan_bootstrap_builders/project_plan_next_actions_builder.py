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
        empty_data = {"actions": [], "summary": {"count": 0}}
        if not visibility.get("allowed"):
            return self._envelope(state="forbidden", visibility=visibility, data=empty_data)
        if not project:
            return self._envelope(state="empty", visibility=visibility, data=empty_data)

        task_count = self._safe_count("project.task", self._project_domain("project.task", project))
        action_state = "available" if task_count > 0 else "blocked"
        reason_code = "PROJECT_PLAN_READY" if task_count > 0 else "PROJECT_PLAN_TASK_MISSING"
        actions = [
            {
                "key": "project_execution_enter",
                "label": "进入项目执行",
                "hint": "计划任务准备完成后进入执行场景。",
                "action_kind": "guidance",
                "target_scene": "project.execution",
                "intent": "project.execution.enter",
                "priority": 10,
                "params": {"project_id": int(project.id), "source": "project.plan.next_actions"},
                "state": action_state,
                "reason_code": reason_code,
                "source": "project_plan_bootstrap",
            }
        ]
        return self._envelope(
            state="ready",
            visibility=visibility,
            data={
                "actions": actions,
                "summary": {
                    "count": len(actions),
                    "available_count": len([row for row in actions if row.get("state") == "available"]),
                    "blocked_count": len([row for row in actions if row.get("state") == "blocked"]),
                    "task_count": task_count,
                },
            },
        )
