# -*- coding: utf-8 -*-
from __future__ import annotations

from odoo import fields

from .base import BaseProjectBlockBuilder


class ProjectRiskBuilder(BaseProjectBlockBuilder):
    block_key = "block.project.risk"
    block_type = "alert_panel"
    title = "风险提醒"
    required_groups = ()

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

        risk_total = self._safe_count("project.risk", [("project_id", "=", int(project.id))])
        risk_critical = self._safe_count("project.risk", [("project_id", "=", int(project.id)), ("risk_level", "in", ["high", "critical", "严重"])])
        risk_open = self._safe_count("project.risk", [("project_id", "=", int(project.id)), ("status", "not in", ["closed", "done"])])
        risk_score = min(100, (risk_critical * 25) + (risk_open * 10) + (len(alerts) * 8))
        risk_level = "high" if risk_score >= 70 else "medium" if risk_score >= 40 else "low"
        data = {
            "alerts": alerts,
            "summary": {
                "risk_total": risk_total,
                "risk_open": risk_open,
                "risk_critical": risk_critical,
                "risk_score": risk_score,
                "risk_level": risk_level,
            },
            "quick_actions": [
                {"key": "open_risk_list", "label": "查看风险清单", "intent": "ui.contract"},
            ],
        }
        return self._envelope(state="ready", visibility=visibility, data=data)
