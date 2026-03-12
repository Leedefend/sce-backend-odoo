# -*- coding: utf-8 -*-
from __future__ import annotations

from .base import BaseProjectBlockBuilder


class ProjectFinanceBuilder(BaseProjectBlockBuilder):
    block_key = "block.project.finance"
    block_type = "record_table"
    title = "资金情况"
    required_groups = ("smart_construction_core.group_sc_cap_finance_read",)

    def build(self, project=None, context=None):
        visibility = self._visibility()
        if not visibility.get("allowed"):
            return self._envelope(
                state="forbidden",
                visibility=visibility,
                data={"rows": [], "columns": [], "quick_actions": []},
            )
        if not project:
            return self._envelope(
                state="empty",
                visibility=visibility,
                data={"rows": [], "columns": [], "quick_actions": []},
            )

        domain = self._project_domain("payment.request", project)
        total = self._safe_count("payment.request", domain)
        received_amount = self._safe_read_group_sum_any(
            "payment.request",
            domain + [("type", "=", "receive"), ("state", "in", ["done", "approved", "approve"])],
            ["amount"],
        )
        paid_amount = self._safe_read_group_sum_any(
            "payment.request",
            domain + [("type", "=", "pay"), ("state", "in", ["done", "approved", "approve"])],
            ["amount"],
        )
        receivable = self._safe_read_group_sum_any("construction.contract", self._project_domain("construction.contract", project), ["amount_total", "amount"])
        payable = self._safe_read_group_sum_any("payment.request", domain + [("type", "=", "pay")], ["amount"])
        cash_gap = round(receivable - received_amount, 2)
        data = {
            "columns": ["payment_request_total"],
            "rows": [{"payment_request_total": total}],
            "summary": {
                "receivable": receivable,
                "received": received_amount,
                "payable": payable,
                "paid": paid_amount,
                "gap": cash_gap,
            },
            "quick_actions": [
                {"key": "open_payment_requests", "label": "查看付款申请", "intent": "ui.contract"},
                {"key": "open_settlement_orders", "label": "查看结算单", "intent": "ui.contract"},
            ],
        }
        return self._envelope(state="ready", visibility=visibility, data=data)
