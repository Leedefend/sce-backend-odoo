# -*- coding: utf-8 -*-
from __future__ import annotations

from typing import Any, Dict, List

from odoo.exceptions import AccessError

from ..core.base_handler import BaseIntentHandler


class ApiOnchangeHandler(BaseIntentHandler):
    INTENT_TYPE = "api.onchange"
    DESCRIPTION = "Contract-driven onchange roundtrip"
    REQUIRED_GROUPS = ["smart_core.group_sc_data_operator"]
    ACL_MODE = "explicit_check"

    def _err(self, code: int, message: str):
        return {"ok": False, "error": {"code": code, "message": message}, "code": code}

    def _collect_params(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        params: Dict[str, Any] = {}
        if isinstance(payload, dict):
            if isinstance(payload.get("params"), dict):
                params.update(payload.get("params") or {})
            if isinstance(payload.get("payload"), dict):
                params.update(payload.get("payload") or {})
        if isinstance(self.params, dict):
            params.update(self.params)
        return params

    def _normalize_values(self, env_model, values: Dict[str, Any]) -> Dict[str, Any]:
        if not isinstance(values, dict):
            return {}
        out: Dict[str, Any] = {}
        for key, val in values.items():
            if key in env_model._fields:
                out[key] = val
        return out

    def _normalize_changed_fields(self, env_model, fields_raw: Any) -> List[str]:
        if isinstance(fields_raw, str):
            fields_raw = [x.strip() for x in fields_raw.split(",") if x.strip()]
        if not isinstance(fields_raw, list):
            return []
        out: List[str] = []
        for item in fields_raw:
            name = str(item or "").strip()
            if not name or name not in env_model._fields:
                continue
            out.append(name)
        return out

    def _build_field_onchange_map(self, env_model) -> Dict[str, str]:
        # Odoo onchange RPC expects a mapping describing fields participating in onchange.
        methods = getattr(env_model, "_onchange_methods", {}) or {}
        if isinstance(methods, dict) and methods:
            return {str(key): "1" for key in methods.keys()}
        return {}

    def handle(self, payload=None, ctx=None):
        payload = payload or {}
        params = self._collect_params(payload)

        model = str(params.get("model") or "").strip()
        if not model:
            return self._err(400, "missing model")
        if model not in self.env:
            return self._err(404, "unknown model")

        context = params.get("context") if isinstance(params.get("context"), dict) else {}
        env_model = self.env[model].with_context(context)

        try:
            env_model.check_access_rights("read")
        except AccessError:
            return self._err(403, "permission denied")

        values = self._normalize_values(env_model, params.get("values") if isinstance(params.get("values"), dict) else {})
        changed_fields = self._normalize_changed_fields(env_model, params.get("changed_fields") or params.get("changed"))
        if not changed_fields:
            return {
                "ok": True,
                "data": {
                    "patch": {},
                    "modifiers_patch": {},
                    "warnings": [],
                    "applied_fields": [],
                },
                "meta": {"model": model},
            }

        field_onchange = self._build_field_onchange_map(env_model)

        try:
            onchange_result = env_model.onchange(values, changed_fields, field_onchange)
        except Exception:
            onchange_result = {}

        if not isinstance(onchange_result, dict):
            onchange_result = {}

        patch = onchange_result.get("value") if isinstance(onchange_result.get("value"), dict) else {}
        domain_patch = onchange_result.get("domain") if isinstance(onchange_result.get("domain"), dict) else {}
        warning = onchange_result.get("warning") if isinstance(onchange_result.get("warning"), dict) else {}

        warnings: List[Dict[str, str]] = []
        if warning:
            warnings.append(
                {
                    "title": str(warning.get("title") or "Onchange warning"),
                    "message": str(warning.get("message") or ""),
                }
            )

        # Domain-only patch can be consumed by frontend modifier engine (as supplemental hints).
        modifiers_patch = {key: {"domain": value} for key, value in domain_patch.items()}

        return {
            "ok": True,
            "data": {
                "patch": patch,
                "modifiers_patch": modifiers_patch,
                "warnings": warnings,
                "applied_fields": changed_fields,
            },
            "meta": {"model": model},
        }
