# -*- coding: utf-8 -*-
from __future__ import annotations

from odoo.addons.smart_construction_core.services.payment_slice_native_adapter import PaymentSliceNativeAdapter
from odoo.addons.smart_construction_core.services.project_dashboard_builders.base import BaseProjectBlockBuilder


class PaymentSliceNextActionsBuilder(BaseProjectBlockBuilder):
    block_key = "block.payment.slice_next_actions"
    block_type = "action_list"
    title = "付款下一步"
    required_groups = ()

    def build(self, project=None, context=None):
        del context
        visibility = self._visibility()
        empty_data = {"actions": [], "summary": {}}
        if not visibility.get("allowed"):
            return self._envelope(state="forbidden", visibility=visibility, data=empty_data)
        if not project:
            return self._envelope(state="empty", visibility=visibility, data=empty_data)

        summary = PaymentSliceNativeAdapter(self.env).summary(project)
        actions = [
            {
                "key": "refresh_payment_list",
                "label": "继续：刷新付款记录",
                "hint": "已接入付款录入、付款记录和付款汇总。若刚录入完成，可刷新区块核对结果。",
                "intent": "payment.block.fetch",
                "params": {
                    "project_id": int(project.id),
                    "block_key": "payment_list",
                },
                "state": "available",
                "reason_code": "PAYMENT_SLICE_REFRESH_READY",
                "source": "fr4_prepared",
            }
        ]
        return self._envelope(
            state="ready",
            visibility=visibility,
            data={
                "actions": actions,
                "summary": {
                    "count": len(actions),
                    "available_count": 1,
                    "planned_count": 0,
                    "current_state": "payment_slice_prepared",
                    "current_state_label": "付款切片 Prepared",
                    "next_step_label": "录入或核对付款记录",
                    "record_count": int(summary.get("request_count") or 0),
                },
            },
        )
