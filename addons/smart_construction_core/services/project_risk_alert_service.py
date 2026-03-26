# -*- coding: utf-8 -*-
from __future__ import annotations

from odoo.addons.smart_construction_core.services.project_decision_engine_service import (
    ProjectDecisionEngineService,
)


class ProjectRiskAlertService:
    def __init__(self, env):
        self.env = env
        self._decision_engine = ProjectDecisionEngineService(env)

    def _model(self, model_name):
        try:
            return self.env[model_name]
        except Exception:
            return None

    def _count(self, model_name, domain):
        model = self._model(model_name)
        if model is None:
            return 0
        try:
            return int(model.search_count(domain))
        except Exception:
            return 0

    def _project_domain(self, model_name, project):
        model = self._model(model_name)
        if model is None:
            return []
        fields = getattr(model, "_fields", {})
        if "project_id" not in fields:
            return []
        return [("project_id", "=", int(project.id))]

    def build(self, project):
        if not project:
            return [
                {
                    "level": "info",
                    "code": "PROJECT_CONTEXT_MISSING",
                    "title": "当前没有可用项目",
                    "message": "当前没有可用项目，无法形成风险判断。",
                    "impact": "驾驶舱无法提供有效的项目决策建议。",
                    "recommended_action": "先创建项目或切换到一个已有项目。",
                    "action": "projects.intake",
                }
            ]

        decision = self._decision_engine.decide(project)
        facts = decision.get("facts") or {}
        signals = facts.get("signals") or {}
        lifecycle_state = str(facts.get("lifecycle_state") or "").strip().lower()
        task_count = int(facts.get("task_count") or 0)
        cost_count = int(facts.get("cost_count") or 0)
        payment_count = int(facts.get("payment_count") or 0)
        primary_action = str(decision.get("primary_action_key") or "").strip()

        alerts = []
        if signals.get("no_tasks"):
            alerts.append(
                {
                    "level": "warning",
                    "code": "EXECUTION_TASK_MISSING",
                    "title": "执行中缺少任务事实",
                    "message": "项目执行中但还没有任务记录。",
                    "impact": "系统无法判断执行推进状态，后续成本和付款动作缺少执行依据。",
                    "recommended_action": "先进入执行推进，补齐至少一项任务记录。",
                    "action": primary_action if primary_action == "project_execution_enter" else "project.execution.enter",
                    "affects_action": "project_execution_enter",
                }
            )
        if signals.get("no_cost"):
            alerts.append(
                {
                    "level": "warning",
                    "code": "EXECUTION_COST_MISSING",
                    "title": "执行中缺少成本事实",
                    "message": "项目执行中但未录入成本。",
                    "impact": "经营基线尚未建立，付款和结算判断会失真。",
                    "recommended_action": "优先进入成本记录，补齐首笔成本事实。",
                    "action": primary_action if primary_action == "cost_tracking_enter" else "cost.tracking.enter",
                    "affects_action": "cost_tracking_enter",
                }
            )
        if signals.get("payment_exceeds_cost"):
            alerts.append(
                {
                    "level": "warning",
                    "code": "PAYMENT_EXCEEDS_COST",
                    "title": "付款记录超过成本事实",
                    "message": "付款记录已超过成本记录，请检查资金事实。",
                    "impact": "资金侧判断可能异常，影响经营结果可信度。",
                    "recommended_action": "进入付款记录，核对支付事实与成本口径。",
                    "action": primary_action if primary_action == "settlement_enter" else "payment.enter",
                    "affects_action": "settlement_enter",
                }
            )
        if signals.get("settlement_blocked"):
            alerts.append(
                {
                    "level": "blocking",
                    "code": "SETTLEMENT_PAYMENT_MISSING",
                    "title": "结算前付款事实不足",
                    "message": "结算前尚未形成付款事实，暂不满足结算条件。",
                    "impact": "项目暂时不能稳定进入结算收口。",
                    "recommended_action": "先补齐付款事实，再进入结算结果检查。",
                    "action": primary_action if primary_action == "payment_enter" else "payment.enter",
                    "affects_action": "payment_enter",
                }
            )
        if signals.get("no_payment"):
            alerts.append(
                {
                    "level": "warning",
                    "code": "PAYMENT_MISSING",
                    "title": "执行中缺少付款事实",
                    "message": "当前项目已有成本事实，但尚未形成付款记录。",
                    "impact": "项目不能稳定进入资金闭环，后续结算判断会延后。",
                    "recommended_action": "继续进入付款记录，补齐首笔付款事实。",
                    "action": primary_action if primary_action == "payment_enter" else "payment.enter",
                    "affects_action": "payment_enter",
                }
            )
        if not alerts:
            alerts.append(
                {
                    "level": "info",
                    "code": "NO_DECISION_RISK",
                    "title": "当前未发现显著风险",
                    "message": "当前未发现阻断主线的显著风险。",
                    "impact": "项目可按推荐动作继续推进。",
                    "recommended_action": "继续按照驾驶舱推荐动作推进主线。",
                    "action": "project.dashboard",
                    "affects_action": primary_action or "project_execution_enter",
                }
            )
        return alerts
