# -*- coding: utf-8 -*-
from __future__ import annotations

from odoo.addons.smart_construction_core.services.cost_tracking_native_adapter import CostTrackingNativeAdapter
from odoo.addons.smart_construction_core.services.project_dashboard_builders.base import BaseProjectBlockBuilder


class CostTrackingSummaryBuilder(BaseProjectBlockBuilder):
    block_key = "block.cost.tracking_summary"
    block_type = "fact_summary"
    title = "成本汇总"
    required_groups = ()

    def build(self, project=None, context=None):
        del context
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
            data={
                "summary": {
                    "project_id": int(summary.get("project_id") or 0),
                    "carrier_model": str(summary.get("carrier_model") or "project.cost.ledger"),
                    "total_cost_amount": float(summary.get("total_cost_amount") or 0.0),
                    "record_count": int(summary.get("ledger_count") or summary.get("move_count") or 0),
                    "draft_record_count": int(summary.get("draft_move_count") or 0),
                    "posted_record_count": int(summary.get("posted_move_count") or 0),
                    "currency_name": str(summary.get("currency_name") or ""),
                    "scope": "project_cost_ledger_first_with_account_move_fallback",
                    "latest_move_date": str(summary.get("latest_move_date") or ""),
                }
            },
        )
