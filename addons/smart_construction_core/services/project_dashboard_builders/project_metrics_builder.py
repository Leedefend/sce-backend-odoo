# -*- coding: utf-8 -*-
from __future__ import annotations

from .base import BaseProjectBlockBuilder


class ProjectMetricsBuilder(BaseProjectBlockBuilder):
    block_key = "block.project.metrics"
    block_type = "metric_row"
    title = "项目关键指标总览"
    required_groups = ()

    def build(self, project=None, context=None):
        visibility = self._visibility()
        if not visibility.get("allowed"):
            return self._envelope(state="forbidden", visibility=visibility, data={"items": []})
        if not project:
            return self._envelope(state="empty", visibility=visibility, data={"items": []})

        task_domain = self._project_domain("project.task", project)
        contract_domain = self._project_domain("construction.contract", project)
        cost_domain = self._project_domain("project.cost.ledger", project)
        payment_domain = self._project_domain("payment.request", project)

        task_total = self._safe_count("project.task", task_domain)
        contract_total = self._safe_count("construction.contract", contract_domain)
        cost_rows = self._safe_count("project.cost.ledger", cost_domain)
        payment_total = self._safe_count("payment.request", payment_domain)

        contract_amount_total = self._safe_read_group_sum_any("construction.contract", contract_domain, ["amount_total", "amount"])
        output_value = float(getattr(project, "dashboard_revenue_actual", 0.0) or 0.0)
        if not output_value:
            output_value = self._safe_read_group_sum_any("account.move.line", [("project_id", "=", int(project.id))], ["credit", "balance"])
        cost_spent = float(getattr(project, "cost_actual", 0.0) or 0.0)
        if not cost_spent:
            cost_spent = self._safe_read_group_sum_any("project.cost.ledger", cost_domain, ["amount", "actual_amount"])
        progress_rate = float(getattr(project, "actual_percent", 0.0) or 0.0)
        received_amount = self._safe_read_group_sum_any(
            "payment.request",
            payment_domain + [("type", "=", "receive"), ("state", "in", ["done", "approved", "approve"])],
            ["amount"],
        )
        risk_open_count = self._safe_count("project.risk", [("project_id", "=", int(project.id)), ("status", "!=", "closed")])
        profit_estimate = output_value - cost_spent
        payment_rate = self._safe_rate(received_amount, contract_amount_total)

        data = {
            "items": [
                {"key": "contract_amount", "label": "合同金额", "value": contract_amount_total, "unit": "元"},
                {"key": "output_value", "label": "已完成产值", "value": output_value, "unit": "元"},
                {"key": "progress_rate", "label": "完成率", "value": round(progress_rate, 2), "unit": "%"},
                {"key": "cost_spent", "label": "成本支出", "value": cost_spent, "unit": "元"},
                {"key": "profit_estimate", "label": "利润估算", "value": round(profit_estimate, 2), "unit": "元"},
                {"key": "payment_received", "label": "回款金额", "value": received_amount, "unit": "元"},
                {"key": "payment_rate", "label": "回款率", "value": payment_rate, "unit": "%"},
                {"key": "risk_open_count", "label": "风险事项", "value": risk_open_count, "unit": "项"},
                {"key": "task_total", "label": "任务总数", "value": task_total, "unit": "项"},
                {"key": "contract_total", "label": "合同数", "value": contract_total, "unit": "份"},
                {"key": "cost_rows", "label": "成本台账", "value": cost_rows, "unit": "行"},
                {"key": "payment_total", "label": "资金申请", "value": payment_total, "unit": "笔"},
            ],
            "kpi": {
                "contract_amount": contract_amount_total,
                "output_value": output_value,
                "progress_rate": round(progress_rate, 2),
                "cost_spent": cost_spent,
                "profit_estimate": round(profit_estimate, 2),
                "payment_received": received_amount,
                "payment_rate": payment_rate,
                "risk_open_count": risk_open_count,
            },
        }
        return self._envelope(state="ready", visibility=visibility, data=data)
