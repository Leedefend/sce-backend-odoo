# -*- coding: utf-8 -*-
from __future__ import annotations

from odoo.addons.smart_construction_core.services.cost_tracking_native_adapter import CostTrackingNativeAdapter
from odoo.addons.smart_construction_core.services.project_dashboard_builders.base import BaseProjectBlockBuilder


class CostTrackingNextActionsBuilder(BaseProjectBlockBuilder):
    block_key = "block.cost.tracking_next_actions"
    block_type = "action_list"
    title = "成本下一步"
    required_groups = ()

    def build(self, project=None, context=None):
        visibility = self._visibility()
        empty_data = {"actions": [], "summary": {}}
        if not visibility.get("allowed"):
            return self._envelope(state="forbidden", visibility=visibility, data=empty_data)
        if not project:
            return self._envelope(state="empty", visibility=visibility, data=empty_data)

        summary = CostTrackingNativeAdapter(self.env).summary(project)
        move_count = int(summary.get("move_count") or 0)
        actions = [
            {
                "key": "open_native_account_moves",
                "label": "继续：核对原生成本凭证",
                "hint": "当前切片只读复用 account.move，不在编排层写入财务事实。",
                "intent": "ui.contract",
                "params": {
                    "project_id": int(project.id),
                    "source": "cost.tracking.next_actions",
                },
                "state": "available" if move_count > 0 else "planned",
                "reason_code": "COST_NATIVE_READONLY_SLICE",
                "source": "phase_17_a",
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
                    "planned_count": len([row for row in actions if str(row.get("state") or "") == "planned"]),
                    "current_state": "cost_native_tracking",
                    "current_state_label": "成本原生跟踪",
                    "next_step_label": "核对原生凭证",
                },
            },
        )
