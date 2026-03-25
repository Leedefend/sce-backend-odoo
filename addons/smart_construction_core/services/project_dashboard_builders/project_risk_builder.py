# -*- coding: utf-8 -*-
from __future__ import annotations

from odoo import fields

from .base import BaseProjectBlockBuilder
from odoo.addons.smart_construction_core.services.project_task_state_support import (
    ProjectTaskStateSupport,
)


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
        progress_signals = {
            "task_overdue": 0,
            "task_blocked": 0,
            "milestone_delay": 0,
        }
        lifecycle_state = str(getattr(project, "lifecycle_state", "") or "").strip().lower()

        task_domain = self._project_domain("project.task", project)
        if self._model_has_fields("project.task", ["date_deadline"]):
            progress_signals["task_overdue"] = self._safe_count(
                "project.task",
                task_domain + [("date_deadline", "<", fields.Date.today())],
            )
        try:
            for task in self.env["project.task"].search(task_domain):
                if ProjectTaskStateSupport.normalize(getattr(task, "sc_state", "draft")) == "draft" and getattr(task, "readiness_status", "") == "blocked":
                    progress_signals["task_blocked"] += 1
        except Exception:
            progress_signals["task_blocked"] = 0

        milestone_domain = self._project_domain("project.milestone", project)
        if self._model_has_fields("project.milestone", ["status"]):
            progress_signals["milestone_delay"] = self._safe_count(
                "project.milestone",
                milestone_domain + [("status", "in", ["delay", "overdue", "blocked"])],
            )

        if progress_signals["task_overdue"] > 0:
            alerts.append(
                {
                    "level": "warning",
                    "code": "TASK_OVERDUE",
                    "title": "任务延期风险",
                    "value": progress_signals["task_overdue"],
                    "hint": "存在已逾期任务，请优先处理进度偏差。",
                    "source": "business",
                    "action_key": "open_task_list",
                }
            )
        if progress_signals["task_blocked"] > 0:
            alerts.append(
                {
                    "level": "warning",
                    "code": "TASK_BLOCKED",
                    "title": "任务阻塞风险",
                    "value": progress_signals["task_blocked"],
                    "hint": "存在阻塞任务，建议立即排除关键路径阻塞点。",
                    "source": "business",
                    "action_key": "open_task_list",
                }
            )
        if progress_signals["milestone_delay"] > 0:
            alerts.append(
                {
                    "level": "danger",
                    "code": "MILESTONE_DELAY",
                    "title": "里程碑延期风险",
                    "value": progress_signals["milestone_delay"],
                    "hint": "里程碑发生延期，建议复核关键路径并调整资源。",
                    "source": "business",
                    "action_key": "open_task_list",
                }
            )

        cost_count = self._safe_count("account.move", self._project_domain("account.move", project))
        payment_count = self._safe_count("payment.request", self._project_domain("payment.request", project))
        if lifecycle_state in {"in_progress", "closing", "warranty", "done"} and cost_count <= 0:
            alerts.append(
                {
                    "level": "warning",
                    "code": "EXECUTION_COST_MISSING",
                    "title": "执行中缺少成本记录",
                    "value": 0,
                    "hint": "项目已进入执行阶段，但尚未形成成本事实，建议优先录入成本。",
                    "source": "product_connection_layer",
                    "action_key": "open_cost_tracking",
                }
            )
        if lifecycle_state in {"in_progress", "closing", "warranty", "done"} and payment_count <= 0:
            alerts.append(
                {
                    "level": "warning",
                    "code": "EXECUTION_PAYMENT_MISSING",
                    "title": "执行中缺少付款记录",
                    "value": 0,
                    "hint": "项目已进入执行阶段，但尚未形成付款记录，建议补齐资金事实。",
                    "source": "product_connection_layer",
                    "action_key": "open_payment_tracking",
                }
            )
        if lifecycle_state in {"closing", "warranty", "done"} and (cost_count <= 0 or payment_count <= 0):
            alerts.append(
                {
                    "level": "danger",
                    "code": "SETTLEMENT_PRECONDITION_BLOCKED",
                    "title": "结算前置条件不足",
                    "value": 0,
                    "hint": "当前成本或付款事实不完整，暂不满足结算收口条件。",
                    "source": "product_connection_layer",
                    "action_key": "open_settlement_summary",
                }
            )

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
                        "hint": "流程待办已逾期，请尽快闭环。",
                        "source": "business",
                        "action_key": "open_task_list",
                    }
                )
        if not alerts:
            alerts.append(
                {
                    "level": "info",
                    "code": "NO_RISK_SIGNAL",
                    "title": "暂无高优先级风险提醒",
                    "value": 0,
                    "hint": "当前进度与风险状态稳定。",
                    "source": "capability_fallback",
                    "action_key": "open_risk_list",
                }
            )

        risk_total = self._safe_count("project.risk", [("project_id", "=", int(project.id))])
        risk_critical = self._safe_count("project.risk", [("project_id", "=", int(project.id)), ("risk_level", "in", ["high", "critical", "严重"])])
        risk_open = self._safe_count("project.risk", [("project_id", "=", int(project.id)), ("status", "not in", ["closed", "done"])])
        risk_score = min(
            100,
            (risk_critical * 25)
            + (risk_open * 10)
            + (progress_signals["task_overdue"] * 6)
            + (progress_signals["task_blocked"] * 8)
            + (progress_signals["milestone_delay"] * 10)
            + (len(alerts) * 4),
        )
        risk_level = "high" if risk_score >= 70 else "medium" if risk_score >= 40 else "low"
        data = {
            "alerts": alerts,
            "summary": {
                "risk_total": risk_total,
                "risk_open": risk_open,
                "risk_critical": risk_critical,
                "risk_score": risk_score,
                "risk_level": risk_level,
                "progress_task_overdue": progress_signals["task_overdue"],
                "progress_task_blocked": progress_signals["task_blocked"],
                "progress_milestone_delay": progress_signals["milestone_delay"],
            },
            "quick_actions": [
                {"key": "open_task_list", "label": "查看任务列表", "intent": "ui.contract"},
                {"key": "open_risk_list", "label": "查看风险清单", "intent": "ui.contract"},
            ],
        }
        return self._envelope(state="ready", visibility=visibility, data=data)
