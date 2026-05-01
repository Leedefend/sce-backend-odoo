# -*- coding: utf-8 -*-
from __future__ import annotations

from odoo.addons.smart_construction_core.services.cost_tracking_native_adapter import CostTrackingNativeAdapter
from odoo.addons.smart_construction_core.services.project_dashboard_builders.base import BaseProjectBlockBuilder


class CostTrackingListBuilder(BaseProjectBlockBuilder):
    block_key = "block.cost.tracking_list"
    block_type = "record_list"
    title = "成本记录"
    required_groups = ()

    def build(self, project=None, context=None):
        del context
        visibility = self._visibility()
        empty_data = {"records": [], "summary": {}}
        if not visibility.get("allowed"):
            return self._envelope(state="forbidden", visibility=visibility, data=empty_data)
        if not project:
            return self._envelope(state="empty", visibility=visibility, data=empty_data)

        adapter = CostTrackingNativeAdapter(self.env)
        records = adapter.recent_moves(project, limit=20)
        state = "ready" if records else "empty"
        return self._envelope(
            state=state,
            visibility=visibility,
            data={
                "records": records,
                "summary": {
                    "count": len(records),
                    "state_fallback_text": "当前项目暂无成本记录。" if not records else "当前展示最近 20 条项目成本记录。",
                },
            },
        )
