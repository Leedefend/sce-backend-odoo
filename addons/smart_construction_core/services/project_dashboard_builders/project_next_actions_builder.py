# -*- coding: utf-8 -*-
from __future__ import annotations

from .base import BaseProjectBlockBuilder


class ProjectNextActionsBuilder(BaseProjectBlockBuilder):
    block_key = "block.project.next_actions"
    block_type = "action_list"
    title = "下一步动作"
    required_groups = ()

    def build(self, project=None, context=None):
        visibility = self._visibility()
        if not visibility.get("allowed"):
            return self._envelope(state="forbidden", visibility=visibility, data={"actions": [], "summary": {}})
        if not project:
            return self._envelope(state="empty", visibility=visibility, data={"actions": [], "summary": {}})

        actions = [
            {
                "key": "plan_bootstrap_enter",
                "label": "下一步：进入计划准备",
                "hint": "当前状态：已完成立项并进入驾驶舱。下一步：核对计划输入并进入计划准备。",
                "intent": "project.plan_bootstrap.enter",
                "params": {
                    "project_id": int(project.id),
                    "source": "project.dashboard.next_actions",
                },
                "state": "available",
                "reason_code": "PLAN_BOOTSTRAP_READY",
                "source": "phase_13_a",
            }
        ]

        next_action_service = self.env["sc.project.next_action.service"]
        try:
            rule_actions = next_action_service.get_next_actions(project, limit=3) or []
        except Exception:
            rule_actions = []
        for index, item in enumerate(rule_actions, start=1):
            if not isinstance(item, dict):
                continue
            actions.append(
                {
                    "key": str(item.get("action_ref") or f"project_rule_action_{index}"),
                    "label": str(item.get("name") or f"项目动作 {index}"),
                    "hint": str(item.get("hint") or ""),
                    "intent": "ui.contract",
                    "params": {
                        "project_id": int(project.id),
                        "source": "project.dashboard.next_actions.rule",
                    },
                    "state": "available",
                    "reason_code": "PROJECT_RULE_ACTION",
                    "source": str(item.get("action_type") or "rule"),
                }
            )

        return self._envelope(
            state="ready",
            visibility=visibility,
            data={
                "actions": actions,
                "summary": {
                    "count": len(actions),
                    "planned_count": len([row for row in actions if str(row.get("state") or "") == "planned"]),
                    "current_state": "dashboard_review",
                    "current_state_label": "已进入项目驾驶舱",
                    "next_step_label": "进入计划准备",
                },
            },
        )
