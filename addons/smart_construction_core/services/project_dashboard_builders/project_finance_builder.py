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
        contract_domain = self._project_domain("construction.contract", project)
        contract_out_domain = contract_domain + [("type", "=", "out")]
        contract_in_domain = contract_domain + [("type", "=", "in")]
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
        receive_pending = self._safe_read_group_sum_any(
            "payment.request",
            domain + [("type", "=", "receive"), ("state", "in", ["draft", "submitted", "pending", "confirm"])],
            ["amount"],
        )
        pay_pending = self._safe_read_group_sum_any(
            "payment.request",
            domain + [("type", "=", "pay"), ("state", "in", ["draft", "submitted", "pending", "confirm"])],
            ["amount"],
        )
        receivable = self._safe_read_group_sum_any("construction.contract", contract_out_domain, ["amount_total", "amount"])
        payable = self._safe_read_group_sum_any("construction.contract", contract_in_domain, ["amount_total", "amount"])
        cash_gap = round(receivable - received_amount, 2)
        net_cash = round(received_amount - paid_amount, 2)
        data = {
            "columns": ["payment_request_total"],
            "column_labels": {
                "payment_request_total": "资金申请总数",
            },
            "rows": [{"payment_request_total": total}],
            "summary": {
                "receivable": receivable,
                "received": received_amount,
                "receive_pending": receive_pending,
                "payable": payable,
                "paid": paid_amount,
                "pay_pending": pay_pending,
                "gap": cash_gap,
                "net_cash": net_cash,
            },
            "empty_message": "当前项目暂无资金申请或合同资金数据，请先补齐资金链路。",
            "quick_actions": [
                {"key": "open_payment_requests", "label": "查看付款申请", "intent": "ui.contract"},
                {"key": "open_settlement_orders", "label": "查看结算单", "intent": "ui.contract"},
            ],
        }
        if total <= 0 and receivable <= 0 and payable <= 0 and received_amount <= 0 and paid_amount <= 0:
            return self._envelope(state="empty", visibility=visibility, data=data)
        return self._envelope(state="ready", visibility=visibility, data=data)
