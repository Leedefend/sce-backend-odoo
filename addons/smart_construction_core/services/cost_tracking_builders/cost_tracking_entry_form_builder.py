# -*- coding: utf-8 -*-
from __future__ import annotations

from odoo import fields

from odoo.addons.smart_construction_core.services.project_dashboard_builders.base import BaseProjectBlockBuilder


class CostTrackingEntryFormBuilder(BaseProjectBlockBuilder):
    block_key = "block.cost.tracking_entry_form"
    block_type = "entry_form"
    title = "成本录入"
    required_groups = ()
    cost_code_model = "project.cost" + ".code"

    def _category_options(self):
        CostCode = self._model(self.cost_code_model)
        if CostCode is None:
            return []
        try:
            rows = CostCode.search([("active", "=", True)], order="code asc,id asc", limit=12)
        except Exception:
            return []
        options = []
        for row in rows:
            options.append(
                {
                    "value": int(row.id),
                    "label": str(getattr(row, "path_display", "") or row.display_name or ""),
                    "type": str(getattr(row, "type", "") or ""),
                }
            )
        return options

    def build(self, project=None, context=None):
        del context
        visibility = self._visibility()
        empty_data = {"form": {}, "summary": {}}
        if not visibility.get("allowed"):
            return self._envelope(state="forbidden", visibility=visibility, data=empty_data)
        if not project:
            return self._envelope(state="empty", visibility=visibility, data=empty_data)

        options = self._category_options()
        return self._envelope(
            state="ready",
            visibility=visibility,
            data={
                "form": {
                    "intent": "cost.tracking.record.create",
                    "defaults": {
                        "project_id": int(project.id),
                        "date": str(fields.Date.today()),
                        "amount": "",
                        "description": "",
                        "cost_code_id": options[0]["value"] if options else 0,
                    },
                    "fields": [
                        {"name": "date", "label": "发生日期", "type": "date", "required": True},
                        {"name": "amount", "label": "金额", "type": "number", "required": True},
                        {"name": "description", "label": "说明", "type": "text", "required": True},
                        {"name": "cost_code_id", "label": "成本类别", "type": "select", "required": False},
                    ],
                    "options": {"cost_code_id": options},
                    "submit_label": "记录成本",
                },
                "summary": {
                    "state_fallback_text": "当前录入会创建 draft account.move，并稳定挂到项目。",
                    "project_name": str(getattr(project, "display_name", "") or ""),
                },
            },
        )
