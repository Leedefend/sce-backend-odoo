# -*- coding: utf-8 -*-
from __future__ import annotations

from odoo.addons.smart_construction_core.services.cost_tracking_native_adapter import CostTrackingNativeAdapter
from odoo.addons.smart_construction_core.services.project_dashboard_builders.base import BaseProjectBlockBuilder


class CostTrackingSummaryBuilder(BaseProjectBlockBuilder):
    block_key = "block.cost.tracking_summary"
    block_type = "fact_summary"
    title = "成本跟踪摘要"
    required_groups = ()

    def build(self, project=None, context=None):
        visibility = self._visibility()
        empty_data = {"summary": {}}
        if not visibility.get("allowed"):
            return self._envelope(state="forbidden", visibility=visibility, data=empty_data)
        if not project:
            return self._envelope(state="empty", visibility=visibility, data=empty_data)

        adapter = CostTrackingNativeAdapter(self.env)
        summary = adapter.summary(project)
        return self._envelope(
            state="ready",
            visibility=visibility,
            data={"summary": summary},
        )
