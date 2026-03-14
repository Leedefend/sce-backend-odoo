# -*- coding: utf-8 -*-
from __future__ import annotations


class BaseProjectBlockBuilder:
    block_key = ""
    block_type = ""
    title = ""
    required_groups = ()

    def __init__(self, env):
        self.env = env

    def _model(self, model_name):
        try:
            return self.env[model_name]
        except Exception:
            return None

    def _model_has_fields(self, model_name, fields):
        model = self._model(model_name)
        if model is None:
            return False
        model_fields = getattr(model, "_fields", {})
        return all(name in model_fields for name in (fields or []))

    def _safe_count(self, model_name, domain=None):
        model = self._model(model_name)
        if model is None:
            return 0
        try:
            return int(model.search_count(domain or []))
        except Exception:
            return 0

    def _safe_read_group_sum(self, model_name, domain, sum_field):
        if not self._model_has_fields(model_name, [sum_field]):
            return 0.0
        model = self._model(model_name)
        if model is None:
            return 0.0
        try:
            rows = model.read_group(domain or [], [sum_field], [])
        except Exception:
            return 0.0
        if not rows:
            return 0.0
        try:
            return float(rows[0].get(sum_field) or 0.0)
        except Exception:
            return 0.0

    def _safe_read_group_sum_any(self, model_name, domain, candidate_fields):
        fields = [name for name in (candidate_fields or []) if isinstance(name, str) and name]
        for sum_field in fields:
            if not self._model_has_fields(model_name, [sum_field]):
                continue
            value = self._safe_read_group_sum(model_name, domain, sum_field)
            if value:
                return value
        return 0.0

    @staticmethod
    def _safe_rate(numerator, denominator):
        try:
            den = float(denominator or 0.0)
            if den <= 0:
                return 0.0
            return round((float(numerator or 0.0) / den) * 100.0, 2)
        except Exception:
            return 0.0

    def _project_domain(self, model_name, project):
        if not project or not self._model_has_fields(model_name, ["project_id"]):
            return []
        return [("project_id", "=", int(project.id))]

    def _visibility(self):
        for group_xmlid in self.required_groups or ():
            try:
                allowed = bool(self.env.user.has_group(group_xmlid))
            except Exception:
                allowed = False
            if not allowed:
                return {
                    "allowed": False,
                    "reason_code": "PERMISSION_DENIED",
                    "reason": "missing_group:%s" % group_xmlid,
                }
        return {"allowed": True, "reason_code": "OK", "reason": ""}

    def _envelope(self, *, state, visibility, data, error_code="", error_message=""):
        return {
            "block_key": self.block_key,
            "block_type": self.block_type,
            "title": self.title,
            "state": state,
            "visibility": visibility,
            "data": data if isinstance(data, dict) else {},
            "error": {
                "code": str(error_code or ""),
                "message": str(error_message or ""),
            },
        }

    def build(self, project=None, context=None):
        raise NotImplementedError
