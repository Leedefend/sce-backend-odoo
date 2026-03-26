# -*- coding: utf-8 -*-
from __future__ import annotations

from odoo import api, models


class EvidenceActionEngineService(models.AbstractModel):
    _name = "sc.evidence.action.engine"
    _description = "Smart Construction Evidence Action Engine"

    DECISION_SOURCE = "evidence_action_engine_v1"

    @staticmethod
    def _action_label(action_key):
        labels = {
            "start_execution": "开始项目执行",
            "project_execution_enter": "进入执行推进",
            "cost_tracking_enter": "进入成本记录",
            "payment_enter": "进入付款记录",
            "settlement_enter": "查看结算结果",
        }
        return labels.get(str(action_key or ""), str(action_key or ""))

    @staticmethod
    def _action_intent(action_key):
        intents = {
            "start_execution": "project.connection.transition",
            "project_execution_enter": "project.execution.enter",
            "cost_tracking_enter": "cost.tracking.enter",
            "payment_enter": "payment.enter",
            "settlement_enter": "settlement.enter",
        }
        return intents.get(str(action_key or ""), "ui.contract")

    def _build_action(self, *, action_key, reason, risk_codes, evidence_refs):
        return {
            "action_key": str(action_key or ""),
            "label": self._action_label(action_key),
            "intent": self._action_intent(action_key),
            "reason": str(reason or ""),
            "risk_codes": list(risk_codes or []),
            "evidence_refs": list(evidence_refs or []),
        }

    @api.model
    def decide(self, project):
        facts = self.env["sc.evidence.risk.engine"].analyze(project)
        signals = facts.get("signals") or {}
        explainable_risks = facts.get("risks") or []

        def _risk_refs(code):
            refs = []
            for risk in explainable_risks:
                if str(risk.get("risk_code") or "") != str(code or ""):
                    continue
                refs.extend(risk.get("evidence_refs") or [])
            return refs

        if signals.get("settlement_completed"):
            primary_key = "settlement_enter"
            reason = "当前项目已形成完整结算证据，建议查看结算结果与项目总结。"
            rule = "settlement_completed"
            primary_risk_codes = ["settlement_completed"]
            primary_evidence_refs = [
                {
                    "business_model": "project.project",
                    "business_id": int(getattr(project, "id", 0) or 0),
                    "evidence_type": "settlement",
                }
            ]
        elif signals.get("is_draft"):
            primary_key = "start_execution"
            reason = "当前项目已完成立项，但尚未进入执行阶段。"
            rule = "draft_to_execution"
            primary_risk_codes = ["draft_project"]
            primary_evidence_refs = []
        elif signals.get("no_tasks"):
            primary_key = "project_execution_enter"
            reason = "当前项目已进入执行阶段，但还没有形成进度证据。"
            rule = "execution_tasks_missing"
            primary_risk_codes = ["no_tasks"]
            primary_evidence_refs = _risk_refs("no_tasks")
        elif signals.get("no_cost"):
            primary_key = "cost_tracking_enter"
            reason = "当前项目已有执行动作，但尚未形成成本证据。"
            rule = "execution_cost_missing"
            primary_risk_codes = ["no_cost"]
            primary_evidence_refs = _risk_refs("no_cost")
        elif signals.get("no_payment"):
            primary_key = "payment_enter"
            reason = "当前项目已有成本证据，但尚未形成付款证据。"
            rule = "payment_missing"
            primary_risk_codes = ["no_payment"]
            primary_evidence_refs = _risk_refs("no_payment")
        elif signals.get("payment_exceeds_cost"):
            primary_key = "settlement_enter"
            reason = "当前项目付款证据已超过成本证据，建议进入结算结果复核经营口径。"
            rule = "payment_exceeds_cost"
            primary_risk_codes = ["payment_exceeds_cost"]
            primary_evidence_refs = _risk_refs("payment_exceeds_cost")
        elif signals.get("ready_for_settlement"):
            primary_key = "settlement_enter"
            reason = "当前项目已具备成本与付款证据，建议进入结算结果检查收口条件。"
            rule = "settlement_ready"
            primary_risk_codes = ["settlement_ready"]
            primary_evidence_refs = [
                {
                    "business_model": "project.project",
                    "business_id": int(getattr(project, "id", 0) or 0),
                    "evidence_type": "settlement",
                }
            ]
        else:
            primary_key = "project_execution_enter"
            reason = "当前项目可以继续从执行推进进入主线。"
            rule = "execution_default"
            primary_risk_codes = []
            primary_evidence_refs = []

        priority_scores = {
            "start_execution": 100 if primary_key == "start_execution" else 0,
            "project_execution_enter": 95 if primary_key == "project_execution_enter" else (80 if signals.get("no_tasks") else 20),
            "cost_tracking_enter": 95 if primary_key == "cost_tracking_enter" else (70 if signals.get("no_cost") else 10),
            "payment_enter": 95 if primary_key == "payment_enter" else (60 if signals.get("no_payment") else 5),
            "settlement_enter": 95 if primary_key == "settlement_enter" else (90 if signals.get("settlement_completed") else (50 if signals.get("ready_for_settlement") else 0)),
        }

        available_action_keys = {"project_execution_enter"}
        if signals.get("is_draft"):
            available_action_keys.add("start_execution")
        if facts.get("lifecycle_state") in {"in_progress", "closing", "warranty", "done"}:
            available_action_keys.add("cost_tracking_enter")
        if int(facts.get("cost_count") or 0) > 0 and facts.get("lifecycle_state") in {"in_progress", "closing", "warranty", "done"}:
            available_action_keys.add("payment_enter")
        if signals.get("ready_for_settlement") or signals.get("payment_exceeds_cost") or signals.get("settlement_completed"):
            available_action_keys.add("settlement_enter")

        explainable_actions = [
            self._build_action(
                action_key=action_key,
                reason=reason if action_key == primary_key else "",
                risk_codes=primary_risk_codes if action_key == primary_key else [],
                evidence_refs=primary_evidence_refs if action_key == primary_key else [],
            )
            for action_key in sorted(available_action_keys)
        ]
        primary_action = {}
        for action in explainable_actions:
            if action.get("action_key") == primary_key:
                primary_action = action
                break

        return {
            "primary_action_key": primary_key,
            "reason": reason,
            "decision_rule": rule,
            "decision_source": self.DECISION_SOURCE,
            "priority_scores": priority_scores,
            "available_action_keys": available_action_keys,
            "actions": explainable_actions,
            "primary_action": primary_action,
            "facts": facts,
        }
