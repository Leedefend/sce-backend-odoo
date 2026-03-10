# -*- coding: utf-8 -*-
from __future__ import annotations

from odoo import fields

from .base import BaseProjectBlockBuilder


class ProjectRiskBuilder(BaseProjectBlockBuilder):
    block_key = "block.project.risk"
    block_type = "alert_panel"
    title = "风险提醒"
    required_groups = ("smart_construction_core.group_sc_cap_project_read",)

    def build(self, project=None, context=None):
        visibility = self._visibility()
        if not visibility.get("allowed"):
            return self._envelope(state="forbidden", visibility=visibility, data={"alerts": [], "quick_actions": []})
        if not project:
            return self._envelope(state="empty", visibility=visibility, data={"alerts": [], "quick_actions": []})

        alerts = []
        if self._model_has_fields("mail.activity", ["res_model", "res_id", "date_deadline"]):
            overdue_domain = [
                ("res_model", "=", "project.project"),
                ("res_id", "=", int(project.id)),
                ("date_deadline", "<", fields.Date.today()),
            ]
            overdue_count = self._safe_count("mail.activity", overdue_domain)
            if overdue_count > 0:
                alerts.append(
                    {
                        "level": "warning",
                        "code": "ACTIVITY_OVERDUE",
                        "title": "存在逾期待办",
                        "value": overdue_count,
                    }
                )
        if not alerts:
            alerts.append(
                {
                    "level": "info",
                    "code": "NO_RISK_SIGNAL",
                    "title": "暂无高优先级风险提醒",
                    "value": 0,
                }
            )
        data = {
            "alerts": alerts,
            "quick_actions": [
                {"key": "open_risk_list", "label": "查看风险清单", "intent": "ui.contract"},
            ],
        }
        return self._envelope(state="ready", visibility=visibility, data=data)
