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

        evidence_summary = self._evidence_summary(project)
        contract_domain = self._project_domain("construction.contract", project)
        contract_out_domain = contract_domain + [("type", "=", "out")]
        contract_in_domain = contract_domain + [("type", "=", "in")]
        total = int(evidence_summary.get("payment_count") or 0)
        received_amount = float(evidence_summary.get("receive_done_total") or 0.0)
        paid_amount = float(evidence_summary.get("pay_done_total") or 0.0)
        receive_pending = float(evidence_summary.get("receive_pending_total") or 0.0)
        pay_pending = float(evidence_summary.get("pay_pending_total") or 0.0)
        receivable = self._safe_read_group_sum_any("construction.contract", contract_out_domain, ["amount_total", "amount"])
        payable = self._safe_read_group_sum_any("construction.contract", contract_in_domain, ["amount_total", "amount"])
        cash_gap = round(receivable - received_amount, 2)
        net_cash = round(received_amount - paid_amount, 2)
        data = {
            "columns": ["payment_request_total"],
            "column_labels": {
                "payment_request_total": "资金证据总数",
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
            "summary_metrics": [
                self._trace_metric(
                    project=project,
                    key="payment_total",
                    label="已付款",
                    value=paid_amount,
                    unit="元",
                    evidence_type="payment",
                ),
                self._trace_metric(
                    project=project,
                    key="settlement_total",
                    label="已结算",
                    value=float(evidence_summary.get("settlement_total") or 0.0),
                    unit="元",
                    evidence_type="settlement",
                ),
            ],
            "empty_message": "当前项目暂无资金申请或合同资金数据，请先补齐资金链路。",
            "quick_actions": [
                {"key": "open_payment_requests", "label": "查看付款申请", "intent": "ui.contract"},
                {"key": "open_settlement_orders", "label": "查看结算单", "intent": "ui.contract"},
            ],
        }
        if total <= 0 and receivable <= 0 and payable <= 0 and received_amount <= 0 and paid_amount <= 0:
            return self._envelope(state="empty", visibility=visibility, data=data)
        return self._envelope(state="ready", visibility=visibility, data=data)
