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
        del context
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
                "key": "refresh_cost_list",
                "label": "继续：刷新成本记录",
                "hint": "已接入项目成本录入、成本记录和成本汇总。若刚录入完成，可刷新区块核对结果。",
                "intent": "cost.tracking.block.fetch",
                "params": {
                    "project_id": int(project.id),
                    "block_key": "cost_list",
                },
                "state": "available",
                "reason_code": "COST_SLICE_REFRESH_READY",
                "source": "fr3_prepared",
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
                    "current_state": "cost_tracking_prepared",
                    "current_state_label": "成本切片 Prepared",
                    "next_step_label": "录入或核对成本记录",
                    "record_count": move_count,
                },
            },
        )
