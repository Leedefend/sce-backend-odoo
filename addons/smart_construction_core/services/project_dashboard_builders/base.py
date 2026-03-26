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

    def _evidence_summary(self, project):
        return self.env["sc.evidence.summary.service"].summary_for_project(project)

    @staticmethod
    def _trace_action(project, evidence_type):
        return {
            "intent": "business.evidence.trace",
            "payload": {
                "business_model": "project.project",
                "business_id": int(getattr(project, "id", 0) or 0),
                "evidence_type": str(evidence_type or ""),
            },
        }

    def _trace_metric(self, *, project, key, label, value, unit="", evidence_type=""):
        return {
            "key": str(key or ""),
            "label": str(label or ""),
            "value": value,
            "unit": str(unit or ""),
            "trace_action": self._trace_action(project, evidence_type),
        }

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

    def _project_context(self, project):
        if not project:
            return {
                "project_id": 0,
                "project_name": "",
                "stage": "",
                "stage_label": "",
                "milestone": "",
                "milestone_label": "",
                "status": "",
            }
        stage = str(getattr(project, "lifecycle_state", "") or "").strip()
        milestone = str(getattr(project, "sc_execution_state", "") or "").strip()
        stage_label = ""
        milestone_label = ""
        try:
            stage_label = str(getattr(getattr(project, "stage_id", None), "display_name", "") or "")
        except Exception:
            stage_label = ""
        try:
            milestone_label = str(getattr(project, "sc_execution_state_label", "") or "")
        except Exception:
            milestone_label = ""
        return {
            "project_id": int(getattr(project, "id", 0) or 0),
            "project_name": str(getattr(project, "display_name", "") or getattr(project, "name", "") or ""),
            "stage": stage,
            "stage_label": stage_label or stage,
            "milestone": milestone,
            "milestone_label": milestone_label or milestone,
            "status": str(getattr(project, "health_state", "") or getattr(project, "state", "") or ""),
        }

    def _next_action(
        self,
        *,
        project,
        key,
        label,
        action_kind,
        target_scene,
        intent,
        priority,
        hint="",
        params=None,
        state="available",
        reason_code="",
        source="",
        recommended=False,
        reason="",
        decision_source="",
        decision_rule="",
        advances_to_stage="",
        priority_score=0,
    ):
        payload = dict(params or {})
        project_context = self._project_context(project)
        if project_context.get("project_id") and "project_context" not in payload:
            payload["project_context"] = project_context
        if project_context.get("project_id") and "project_id" not in payload:
            payload["project_id"] = project_context["project_id"]
        return {
            "key": str(key or ""),
            "label": str(label or ""),
            "hint": str(hint or ""),
            "action_kind": str(action_kind or "guidance"),
            "target_scene": str(target_scene or ""),
            "intent": str(intent or ""),
            "priority": int(priority or 0),
            "params": payload,
            "state": str(state or "available"),
            "reason_code": str(reason_code or ""),
            "source": str(source or ""),
            "recommended": bool(recommended),
            "reason": str(reason or ""),
            "decision_source": str(decision_source or ""),
            "decision_rule": str(decision_rule or ""),
            "advances_to_stage": str(advances_to_stage or ""),
            "priority_score": int(priority_score or 0),
        }

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
