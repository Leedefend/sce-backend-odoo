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
        data = {
            "columns": ["payment_request_total"],
            "rows": [{"payment_request_total": total}],
            "quick_actions": [
                {"key": "open_payment_requests", "label": "查看付款申请", "intent": "ui.contract"},
                {"key": "open_settlement_orders", "label": "查看结算单", "intent": "ui.contract"},
            ],
        }
        return self._envelope(state="ready", visibility=visibility, data=data)
