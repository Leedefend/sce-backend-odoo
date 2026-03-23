# -*- coding: utf-8 -*-
from __future__ import annotations

from odoo import fields

from odoo.addons.smart_construction_core.services.project_dashboard_builders.base import BaseProjectBlockBuilder


class PaymentSliceEntryFormBuilder(BaseProjectBlockBuilder):
    block_key = "block.payment.slice_entry_form"
    block_type = "entry_form"
    title = "付款录入"
    required_groups = ()

    def build(self, project=None, context=None):
        del context
        visibility = self._visibility()
        empty_data = {"form": {}, "summary": {}}
        if not visibility.get("allowed"):
            return self._envelope(state="forbidden", visibility=visibility, data=empty_data)
        if not project:
            return self._envelope(state="empty", visibility=visibility, data=empty_data)

        return self._envelope(
            state="ready",
            visibility=visibility,
            data={
                "form": {
                    "intent": "payment.record.create",
                    "defaults": {
                        "project_id": int(project.id),
                        "date": str(fields.Date.today()),
                        "amount": "",
                        "description": "",
                    },
                    "fields": [
                        {"name": "date", "label": "付款日期", "type": "date", "required": True},
                        {"name": "amount", "label": "金额", "type": "number", "required": True},
                        {"name": "description", "label": "说明", "type": "text", "required": True},
                    ],
                    "submit_label": "记录付款",
                },
                "summary": {
                    "state_fallback_text": "当前录入会创建 draft payment.request，并稳定挂到项目。",
                    "project_name": str(getattr(project, "display_name", "") or ""),
                },
            },
        )
