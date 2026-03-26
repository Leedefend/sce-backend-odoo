# -*- coding: utf-8 -*-
from __future__ import annotations

from .base import BaseProjectBlockBuilder
from odoo.addons.smart_construction_core.services.project_task_state_support import (
    ProjectTaskStateSupport,
)


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
        evidence_summary = self._evidence_summary(project)

        task_total = self._safe_count("project.task", task_domain)
        contract_total = self._safe_count("construction.contract", contract_domain)
        cost_rows = int(evidence_summary.get("cost_count") or 0)
        payment_total = int(evidence_summary.get("payment_count") or 0)

        contract_amount_total = self._safe_read_group_sum_any("construction.contract", contract_domain, ["amount_total", "amount"])
        reported_output = 0.0
        for field_name in ("output_value_actual", "output_value_reported", "output_value"):
            if hasattr(project, field_name):
                reported_output = float(getattr(project, field_name, 0.0) or 0.0)
                if reported_output:
                    break
        cost_spent = float(evidence_summary.get("cost_total") or 0.0)
        progress_rate = float(getattr(project, "actual_percent", 0.0) or 0.0)
        if not progress_rate:
            progress_rate = float(getattr(project, "progress_rate_latest", 0.0) or 0.0)
        if not progress_rate and task_total > 0:
            done = self._safe_count("project.task", task_domain + ProjectTaskStateSupport.done_domain())
            progress_rate = self._safe_rate(done, task_total)
        contract_executed_amount = self._safe_read_group_sum_any(
            "construction.contract",
            contract_domain + [("state", "in", ["running", "in_progress", "done", "approved", "effective"])],
            ["amount_total", "amount"],
        )
        contract_execution_rate = self._safe_rate(contract_executed_amount, contract_amount_total)
        if not progress_rate and contract_execution_rate:
            progress_rate = contract_execution_rate
        received_amount = float(evidence_summary.get("receive_done_total") or 0.0)
        revenue_target = float(getattr(project, "budget_active_revenue_target", 0.0) or 0.0)
        base_amount = contract_amount_total or revenue_target
        progress_output = (base_amount * progress_rate / 100.0) if (base_amount and progress_rate) else 0.0
        output_value = reported_output or progress_output
        risk_open_count = self._safe_count("project.risk", [("project_id", "=", int(project.id)), ("status", "!=", "closed")])
        profit_estimate = output_value - cost_spent
        payment_rate = self._safe_rate(received_amount, contract_amount_total)

        data = {
            "items": [
                {"key": "contract_amount", "label": "合同金额", "value": contract_amount_total, "unit": "元"},
                {"key": "output_value", "label": "已完成产值", "value": output_value, "unit": "元"},
                {"key": "progress_rate", "label": "完成率", "value": round(progress_rate, 2), "unit": "%"},
                {
                    "key": "cost_spent",
                    "label": "成本支出",
                    "value": cost_spent,
                    "unit": "元",
                    "trace_action": self._trace_action(project, "cost"),
                },
                {"key": "profit_estimate", "label": "利润估算", "value": round(profit_estimate, 2), "unit": "元"},
                {"key": "payment_received", "label": "回款金额", "value": received_amount, "unit": "元"},
                {"key": "payment_rate", "label": "回款率", "value": payment_rate, "unit": "%"},
                {
                    "key": "risk_open_count",
                    "label": "风险事项",
                    "value": risk_open_count,
                    "unit": "项",
                    "trace_action": self._trace_action(project, "risk"),
                },
                {"key": "task_total", "label": "任务总数", "value": task_total, "unit": "项"},
                {"key": "contract_total", "label": "合同数", "value": contract_total, "unit": "份"},
                {"key": "cost_rows", "label": "成本台账", "value": cost_rows, "unit": "行"},
                {
                    "key": "payment_total",
                    "label": "资金证据",
                    "value": payment_total,
                    "unit": "笔",
                    "trace_action": self._trace_action(project, "payment"),
                },
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
