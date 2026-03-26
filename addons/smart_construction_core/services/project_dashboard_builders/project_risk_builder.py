# -*- coding: utf-8 -*-
from __future__ import annotations

from odoo import fields

from .base import BaseProjectBlockBuilder
from odoo.addons.smart_construction_core.services.project_task_state_support import (
    ProjectTaskStateSupport,
)
from odoo.addons.smart_construction_core.services.project_risk_alert_service import (
    ProjectRiskAlertService,
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
        decision_alert_service = ProjectRiskAlertService(self.env)
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
                    "impact": "关键路径推进可能继续滞后，并影响后续成本与付款节奏。",
                    "recommended_action": "优先进入执行推进，处理延期任务并更新计划状态。",
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
                    "impact": "执行推进可能停滞，驾驶舱推荐动作会持续受阻。",
                    "recommended_action": "先排除阻塞任务，再继续成本、付款和结算主线。",
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
                    "impact": "项目收口时间会被推迟，后续经营动作的时间窗被压缩。",
                    "recommended_action": "优先复核关键路径和里程碑状态，必要时重新安排资源。",
                    "source": "business",
                    "action_key": "open_task_list",
                }
            )

        decision_alerts = decision_alert_service.build(project)
        for item in decision_alerts:
            row = item if isinstance(item, dict) else {}
            code = str(row.get("code") or "").strip()
            if code and any(str(existing.get("code") or "").strip() == code for existing in alerts):
                continue
            level = str(row.get("level") or "info").strip().lower()
            alerts.append(
                {
                    "level": "danger" if level == "blocking" else level,
                    "code": code or "DECISION_ALERT",
                    "title": str(row.get("title") or row.get("message") or "风险提醒").strip(),
                    "value": 0,
                    "hint": str(row.get("message") or "").strip(),
                    "impact": str(row.get("impact") or "").strip() or "当前问题会影响主线推进，请优先处理。",
                    "recommended_action": str(row.get("recommended_action") or "").strip() or "按驾驶舱推荐动作继续推进。",
                    "source": "decision_layer_v1",
                    "action_key": str(row.get("action") or "").strip() or "open_risk_list",
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
                    "impact": "流程闭环节奏被拖慢，用户待办与项目事实会继续脱节。",
                    "recommended_action": "优先处理逾期待办，再返回项目驾驶舱继续主线动作。",
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
                    "impact": "当前没有阻断主线的显著问题，可以按推荐动作继续推进。",
                    "recommended_action": "直接按照驾驶舱推荐动作继续推进项目。",
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
