# -*- coding: utf-8 -*-
from __future__ import annotations

from .base import BaseProjectBlockBuilder


class ProjectCostBuilder(BaseProjectBlockBuilder):
    block_key = "block.project.cost"
    block_type = "record_summary"
    title = "成本控制"
    required_groups = ("smart_construction_core.group_sc_cap_cost_read",)

    def build(self, project=None, context=None):
        visibility = self._visibility()
        if not visibility.get("allowed"):
            return self._envelope(state="forbidden", visibility=visibility, data={"summary": {}})
        if not project:
            return self._envelope(state="empty", visibility=visibility, data={"summary": {}})

        budget_count = self._safe_count("project.budget", self._project_domain("project.budget", project))
        ledger_count = self._safe_count("project.cost.ledger", self._project_domain("project.cost.ledger", project))
        budget_target = float(getattr(project, "budget_total", 0.0) or 0.0)
        if not budget_target:
            budget_target = float(getattr(project, "budget_active_cost_target", 0.0) or 0.0)
        actual_cost = float(getattr(project, "cost_actual", 0.0) or 0.0)
        if not actual_cost:
            actual_cost = self._safe_read_group_sum_any(
                "project.cost.ledger",
                self._project_domain("project.cost.ledger", project),
                ["amount", "actual_amount"],
            )
        variance = round(actual_cost - budget_target, 2)
        variance_rate = self._safe_rate(variance, budget_target)
        completion_rate = self._safe_rate(actual_cost, budget_target)
        data = {
            "summary": {
                "budget_count": budget_count,
                "cost_ledger_count": ledger_count,
                "budget_target": budget_target,
                "actual_cost": actual_cost,
                "cost_variance": variance,
                "cost_variance_rate": variance_rate,
                "cost_completion_rate": completion_rate,
            },
            "empty_message": "当前项目暂无成本台账或预算目标，请先补齐成本基线。",
        }
        if budget_count <= 0 and ledger_count <= 0 and budget_target <= 0 and actual_cost <= 0:
            return self._envelope(state="empty", visibility=visibility, data=data)
        return self._envelope(state="ready", visibility=visibility, data=data)
