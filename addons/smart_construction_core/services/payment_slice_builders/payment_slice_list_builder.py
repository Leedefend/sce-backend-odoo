# -*- coding: utf-8 -*-
from __future__ import annotations

from odoo.addons.smart_construction_core.services.payment_slice_native_adapter import PaymentSliceNativeAdapter
from odoo.addons.smart_construction_core.services.project_dashboard_builders.base import BaseProjectBlockBuilder


class PaymentSliceListBuilder(BaseProjectBlockBuilder):
    block_key = "block.payment.slice_list"
    block_type = "record_list"
    title = "付款记录"
    required_groups = ()

    def build(self, project=None, context=None):
        del context
        visibility = self._visibility()
        empty_data = {"records": [], "summary": {}}
        if not visibility.get("allowed"):
            return self._envelope(state="forbidden", visibility=visibility, data=empty_data)
        if not project:
            return self._envelope(state="empty", visibility=visibility, data=empty_data)

        records = PaymentSliceNativeAdapter(self.env).recent_requests(project, limit=20)
        if not records:
            return self._envelope(
                state="empty",
                visibility=visibility,
                data={
                    "records": [],
                    "summary": {
                        "record_count": 0,
                        "empty_hint": "当前项目还没有付款记录。",
                    },
                },
            )
        return self._envelope(
            state="ready",
            visibility=visibility,
            data={
                "records": records,
                "summary": {
                    "record_count": len(records),
                    "empty_hint": "",
                },
            },
        )
