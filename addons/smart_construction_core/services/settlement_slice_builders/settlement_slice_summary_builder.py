# -*- coding: utf-8 -*-
from __future__ import annotations

from odoo.addons.smart_construction_core.services.project_dashboard_builders.base import BaseProjectBlockBuilder


class SettlementSliceSummaryBuilder(BaseProjectBlockBuilder):
    block_key = "block.settlement.slice_summary"
    block_type = "fact_summary"
    title = "结算结果"
    required_groups = ()

    def build(self, project=None, context=None):
        del context
        visibility = self._visibility()
        empty_data = {"summary": {}}
        if not visibility.get("allowed"):
            return self._envelope(state="forbidden", visibility=visibility, data=empty_data)
        if not project:
            return self._envelope(state="empty", visibility=visibility, data=empty_data)

        from odoo.addons.smart_construction_core.services.settlement_slice_service import SettlementSliceService

        summary = SettlementSliceService(self.env).summary(project)
        return self._envelope(
            state="ready",
            visibility=visibility,
            data={
                "summary": {
                    "project_id": int(summary.get("project_id") or 0),
                    "carrier_models": list(summary.get("carrier_models") or []),
                    "total_cost": float(summary.get("total_cost") or 0.0),
                    "total_payment": float(summary.get("total_payment") or 0.0),
                    "delta": float(summary.get("delta") or 0.0),
                    "currency_name": str(summary.get("currency_name") or ""),
                    "cost_record_count": int(summary.get("cost_record_count") or 0),
                    "payment_record_count": int(summary.get("payment_record_count") or 0),
                    "scope": "project_cost_and_payment_read_only_summary",
                    "as_of_date": str(summary.get("as_of_date") or ""),
                }
            },
        )
