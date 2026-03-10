# -*- coding: utf-8 -*-
from __future__ import annotations

from .base import BaseProjectBlockBuilder


class ProjectMetricsBuilder(BaseProjectBlockBuilder):
    block_key = "block.project.metrics"
    block_type = "metric_row"
    title = "项目关键指标总览"
    required_groups = ("smart_construction_core.group_sc_cap_project_read",)

    def build(self, project=None, context=None):
        visibility = self._visibility()
        if not visibility.get("allowed"):
            return self._envelope(state="forbidden", visibility=visibility, data={"items": []})
        if not project:
            return self._envelope(state="empty", visibility=visibility, data={"items": []})

        task_total = self._safe_count("project.task", self._project_domain("project.task", project))
        contract_total = self._safe_count("construction.contract", self._project_domain("construction.contract", project))
        cost_rows = self._safe_count("project.cost.ledger", self._project_domain("project.cost.ledger", project))
        payment_total = self._safe_count("payment.request", self._project_domain("payment.request", project))

        data = {
            "items": [
                {"key": "task_total", "label": "任务总数", "value": task_total, "unit": "项"},
                {"key": "contract_total", "label": "合同数", "value": contract_total, "unit": "份"},
                {"key": "cost_rows", "label": "成本台账", "value": cost_rows, "unit": "行"},
                {"key": "payment_total", "label": "付款申请", "value": payment_total, "unit": "笔"},
            ]
        }
        return self._envelope(state="ready", visibility=visibility, data=data)
