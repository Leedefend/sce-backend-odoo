# -*- coding: utf-8 -*-
from __future__ import annotations


class ProjectDecisionEngineService:
    DECISION_SOURCE = "rule_engine_v1"
    PAYMENT_REQUEST_TYPES = ("pay",)

    def __init__(self, env):
        self.env = env

    def _model(self, model_name):
        try:
            return self.env[model_name]
        except Exception:
            return None

    def _project_domain(self, model_name, project):
        model = self._model(model_name)
        if model is None:
            return []
        fields = getattr(model, "_fields", {})
        if "project_id" not in fields:
            return []
        return [("project_id", "=", int(project.id))]

    def _payment_request_domain(self, project):
        domain = self._project_domain("payment.request", project)
        model = self._model("payment.request")
        if model is None:
            return domain
        if "type" not in getattr(model, "_fields", {}):
            return domain
        return domain + [("type", "in", list(self.PAYMENT_REQUEST_TYPES))]

    def _count(self, model_name, project):
        model = self._model(model_name)
        if model is None or not project:
            return 0
        try:
            domain = self._payment_request_domain(project) if model_name == "payment.request" else self._project_domain(model_name, project)
            return int(model.search_count(domain))
        except Exception:
            return 0

    def _sum_first_field(self, model_name, project, field_names):
        model = self._model(model_name)
        if model is None or not project:
            return 0.0
        domain = self._payment_request_domain(project) if model_name == "payment.request" else self._project_domain(model_name, project)
        for field_name in field_names:
            if field_name not in getattr(model, "_fields", {}):
                continue
            try:
                rows = model.read_group(domain, [field_name], [])
            except Exception:
                continue
            if not rows:
                continue
            try:
                return float(rows[0].get(field_name) or 0.0)
            except Exception:
                return 0.0
        return 0.0

    @staticmethod
    def _fallback_analyze_payload(project):
        lifecycle_state = str(getattr(project, "lifecycle_state", "") or "").strip().lower() if project else ""
        project_id = int(getattr(project, "id", 0) or 0) if project else 0
        return {
            "lifecycle_state": lifecycle_state,
            "task_count": 0,
            "cost_count": 0,
            "payment_count": 0,
            "settlement_count": 0,
            "settlement_done_count": 0,
            "cost_total": 0.0,
            "payment_total": 0.0,
            "progress_percent": 0.0,
            "signals": {
                "is_draft": lifecycle_state == "draft",
                "ready_for_settlement": False,
                "payment_exceeds_cost": False,
                "settlement_completed": False,
            },
            "risk_count": 0,
            "risk_codes": [],
            "risks": [],
            "evidence_summary": {},
            "project_id": project_id,
            "decision_fallback": "risk_engine_unavailable",
        }

    def _fallback_decide_payload(self, project):
        facts = self._fallback_analyze_payload(project)
        primary_key = "project_execution_enter"
        return {
            "primary_action_key": primary_key,
            "reason": "risk/action engine unavailable, fallback decision applied",
            "decision_rule": "fallback_unavailable_engine",
            "decision_source": self.DECISION_SOURCE,
            "priority_scores": {primary_key: 100},
            "available_action_keys": [primary_key],
            "actions": [
                {
                    "action_key": primary_key,
                    "label": "进入执行推进",
                    "intent": "project.execution.enter",
                    "reason": "fallback action",
                    "risk_codes": [],
                    "evidence_refs": [],
                }
            ],
            "primary_action": {
                "action_key": primary_key,
                "label": "进入执行推进",
                "intent": "project.execution.enter",
                "reason": "fallback action",
                "risk_codes": [],
                "evidence_refs": [],
            },
            "facts": facts,
        }

    def analyze(self, project):
        risk_engine = self._model("sc.evidence.risk.engine")
        if risk_engine is None:
            return self._fallback_analyze_payload(project)
        try:
            return risk_engine.analyze(project)
        except Exception:
            return self._fallback_analyze_payload(project)

    def decide(self, project):
        action_engine = self._model("sc.evidence.action.engine")
        if action_engine is None:
            return self._fallback_decide_payload(project)
        try:
            return action_engine.decide(project)
        except Exception:
            return self._fallback_decide_payload(project)
