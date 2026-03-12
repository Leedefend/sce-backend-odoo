# -*- coding: utf-8 -*-
from __future__ import annotations

from .base import BaseProjectBlockBuilder


class ProjectContractBuilder(BaseProjectBlockBuilder):
    block_key = "block.project.contract"
    block_type = "record_table"
    title = "合同执行"
    required_groups = ("smart_construction_core.group_sc_cap_contract_read",)

    def build(self, project=None, context=None):
        visibility = self._visibility()
        if not visibility.get("allowed"):
            return self._envelope(state="forbidden", visibility=visibility, data={"rows": [], "columns": []})
        if not project:
            return self._envelope(state="empty", visibility=visibility, data={"rows": [], "columns": []})

        domain = self._project_domain("construction.contract", project)
        out_domain = domain + [("type", "=", "out")]
        in_domain = domain + [("type", "=", "in")]
        count = self._safe_count("construction.contract", domain)
        out_count = self._safe_count("construction.contract", out_domain)
        in_count = self._safe_count("construction.contract", in_domain)
        amount_field = "amount_total" if self._model_has_fields("construction.contract", ["amount_total"]) else ""
        total_amount = self._safe_read_group_sum("construction.contract", out_domain, amount_field) if amount_field else 0.0
        subcontract_total = self._safe_read_group_sum("construction.contract", in_domain, amount_field) if amount_field else 0.0
        executed_amount = self._safe_read_group_sum_any(
            "construction.contract",
            out_domain + [("state", "in", ["running", "in_progress", "done", "approved", "effective"])],
            ["amount_total", "amount"],
        )
        change_amount = self._safe_read_group_sum_any("construction.contract", out_domain, ["amount_change", "change_amount"])
        performance_rate = self._safe_rate(executed_amount, total_amount)
        data = {
            "columns": ["contract_count", "contract_amount_total"],
            "column_labels": {
                "contract_count": "合同数量",
                "contract_amount_total": "收入合同总额",
            },
            "rows": [
                {
                    "contract_count": count,
                    "contract_amount_total": total_amount,
                }
            ],
            "summary": {
                "contract_total": total_amount,
                "executed_amount": executed_amount,
                "change_amount": change_amount,
                "performance_rate": performance_rate,
                "subcontract_total": subcontract_total,
                "contract_count_income": out_count,
                "contract_count_expense": in_count,
            },
            "empty_message": "当前项目暂无合同执行数据，请先补齐收入/支出合同。",
        }
        if count <= 0 and total_amount <= 0 and subcontract_total <= 0:
            return self._envelope(state="empty", visibility=visibility, data=data)
        return self._envelope(state="ready", visibility=visibility, data=data)
