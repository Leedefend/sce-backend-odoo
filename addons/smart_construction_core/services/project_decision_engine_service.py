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

    def analyze(self, project):
        return self.env["sc.evidence.risk.engine"].analyze(project)

    def decide(self, project):
        return self.env["sc.evidence.action.engine"].decide(project)
