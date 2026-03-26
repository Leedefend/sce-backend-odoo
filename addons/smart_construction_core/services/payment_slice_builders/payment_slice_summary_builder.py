# -*- coding: utf-8 -*-
from __future__ import annotations

from odoo.addons.smart_construction_core.services.payment_slice_native_adapter import PaymentSliceNativeAdapter
from odoo.addons.smart_construction_core.services.project_dashboard_builders.base import BaseProjectBlockBuilder


class PaymentSliceSummaryBuilder(BaseProjectBlockBuilder):
    block_key = "block.payment.slice_summary"
    block_type = "fact_summary"
    title = "付款汇总"
    required_groups = ()

    def build(self, project=None, context=None):
        del context
        visibility = self._visibility()
        empty_data = {"summary": {}}
        if not visibility.get("allowed"):
            return self._envelope(state="forbidden", visibility=visibility, data=empty_data)
        if not project:
            return self._envelope(state="empty", visibility=visibility, data=empty_data)

        summary = PaymentSliceNativeAdapter(self.env).summary(project)
        return self._envelope(
            state="ready",
            visibility=visibility,
            data={
                "summary": {
                    "project_id": int(summary.get("project_id") or 0),
                    "carrier_model": str(summary.get("carrier_model") or "payment.request"),
                    "total_payment_amount": float(summary.get("total_payment_amount") or 0.0),
                    "record_count": int(summary.get("request_count") or 0),
                    "draft_record_count": int(summary.get("draft_request_count") or 0),
                    "approved_record_count": int(summary.get("approved_request_count") or 0),
                    "executed_record_count": int(summary.get("ledger_count") or 0),
                    "executed_payment_amount": float(summary.get("executed_payment_amount") or 0.0),
                    "currency_name": str(summary.get("currency_name") or ""),
                    "scope": "project_linked_payment_request_only",
                    "latest_request_date": str(summary.get("latest_request_date") or ""),
                    "latest_paid_at": str(summary.get("latest_paid_at") or ""),
                }
            },
        )
