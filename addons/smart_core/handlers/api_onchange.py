# -*- coding: utf-8 -*-
from __future__ import annotations

from typing import Any, Dict, List

from odoo.exceptions import AccessError

from ..core.base_handler import BaseIntentHandler
from ..core.intent_execution_result import IntentExecutionResult
from ..utils.reason_codes import normalize_onchange_reason_code


class ApiOnchangeHandler(BaseIntentHandler):
    INTENT_TYPE = "api.onchange"
    DESCRIPTION = "Contract-driven onchange roundtrip"
    VERSION = "1.1.0"
    REQUIRED_GROUPS = ["smart_core.group_smart_core_data_operator"]
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

    def _normalize_patch(self, env_model, patch_raw: Any) -> Dict[str, Any]:
        if not isinstance(patch_raw, dict):
            return {}
        out: Dict[str, Any] = {}
        for key, value in patch_raw.items():
            name = str(key or "").strip()
            if not name or name not in env_model._fields:
                continue
            out[name] = value
        return out

    def _normalize_domain_patch(self, env_model, domain_raw: Any) -> Dict[str, Any]:
        if not isinstance(domain_raw, dict):
            return {}
        out: Dict[str, Any] = {}
        for key, value in domain_raw.items():
            name = str(key or "").strip()
            if not name or name not in env_model._fields:
                continue
            if isinstance(value, list):
                out[name] = value
        return out

    def _normalize_modifiers_patch(self, env_model, modifiers_raw: Any) -> Dict[str, Dict[str, Any]]:
        if not isinstance(modifiers_raw, dict):
            return {}
        out: Dict[str, Dict[str, Any]] = {}
        for key, bucket in modifiers_raw.items():
            name = str(key or "").strip()
            if not name or name not in env_model._fields:
                continue
            if not isinstance(bucket, dict):
                continue
            normalized: Dict[str, Any] = {}
            for marker in ("invisible", "readonly", "required", "domain"):
                if marker in bucket:
                    normalized[marker] = bucket.get(marker)
            if normalized:
                out[name] = normalized
        return out

    def _normalize_warning_list(self, warning: Any) -> List[Dict[str, str]]:
        warnings: List[Dict[str, str]] = []
        if isinstance(warning, dict):
            warnings.append(
                {
                    "title": str(warning.get("title") or "Onchange warning"),
                    "message": str(warning.get("message") or ""),
                    "reason_code": normalize_onchange_reason_code(warning.get("reason_code") or warning.get("code")),
                }
            )
            return warnings
        if isinstance(warning, list):
            for item in warning:
                if not isinstance(item, dict):
                    continue
                warnings.append(
                    {
                        "title": str(item.get("title") or "Onchange warning"),
                        "message": str(item.get("message") or ""),
                        "reason_code": normalize_onchange_reason_code(item.get("reason_code") or item.get("code")),
                    }
                )
        return warnings

    def _normalize_line_patches(self, env_model, rows_raw: Any) -> List[Dict[str, Any]]:
        if not isinstance(rows_raw, list):
            return []
        out: List[Dict[str, Any]] = []
        for item in rows_raw:
            if not isinstance(item, dict):
                continue
            field = str(item.get("field") or "").strip()
            if not field or field not in env_model._fields:
                continue
            row_patch = self._normalize_line_patch_values(env_model, field, item.get("patch"))
            row_modifiers = self._normalize_line_patch_modifiers(env_model, field, item.get("modifiers_patch"))
            warnings = self._normalize_warning_list(item.get("warnings"))
            row_state = self._normalize_row_state(item, row_patch, warnings)
            normalized: Dict[str, Any] = {
                "field": field,
                "row_key": str(item.get("row_key") or "").strip(),
                "row_id": int(item.get("row_id") or 0) if str(item.get("row_id") or "").strip() else 0,
                "patch": row_patch,
                "modifiers_patch": row_modifiers,
                "warnings": warnings,
                "row_state": row_state,
                "command_hint": self._command_hint_for_row_state(row_state),
            }
            # keep compatibility for future per-line domain support
            if isinstance(item.get("domain"), list):
                normalized["domain"] = item.get("domain")
            out.append(normalized)
        return out

    def _relation_field_names(self, env_model, field_name: str) -> List[str]:
        field_obj = env_model._fields.get(field_name)
        if not field_obj:
            return []
        ftype = str(getattr(field_obj, "type", "") or "").strip().lower()
        if ftype not in ("one2many", "many2many"):
            return []
        relation = str(getattr(field_obj, "comodel_name", "") or "").strip()
        if not relation or relation not in self.env:
            return []
        try:
            return list((self.env[relation]._fields or {}).keys())
        except Exception:
            return []

    def _normalize_line_patch_values(self, env_model, field_name: str, patch_raw: Any) -> Dict[str, Any]:
        if not isinstance(patch_raw, dict):
            return {}
        allowed = set(self._relation_field_names(env_model, field_name))
        if not allowed:
            return {}
        out: Dict[str, Any] = {}
        for key, value in patch_raw.items():
            name = str(key or "").strip()
            if not name or name not in allowed:
                continue
            out[name] = value
        return out

    def _normalize_line_patch_modifiers(self, env_model, field_name: str, modifiers_raw: Any) -> Dict[str, Dict[str, Any]]:
        if not isinstance(modifiers_raw, dict):
            return {}
        allowed = set(self._relation_field_names(env_model, field_name))
        if not allowed:
            return {}
        out: Dict[str, Dict[str, Any]] = {}
        for key, bucket in modifiers_raw.items():
            name = str(key or "").strip()
            if not name or name not in allowed:
                continue
            if not isinstance(bucket, dict):
                continue
            normalized: Dict[str, Any] = {}
            for marker in ("invisible", "readonly", "required", "domain"):
                if marker in bucket:
                    normalized[marker] = bucket.get(marker)
            if normalized:
                out[name] = normalized
        return out

    def _normalize_row_state(self, item: Dict[str, Any], row_patch: Dict[str, Any], warnings: List[Dict[str, str]]) -> str:
        raw = str(item.get("row_state") or "").strip().lower()
        if raw in ("create", "update", "remove", "keep"):
            return raw
        row_id_raw = item.get("row_id")
        row_id = int(row_id_raw or 0) if str(row_id_raw or "").strip() else 0
        if row_id <= 0 and row_patch:
            return "create"
        if row_id > 0 and row_patch:
            return "update"
        if row_id > 0 and not row_patch and not warnings:
            return "remove"
        return "keep"

    def _command_hint_for_row_state(self, row_state: str) -> List[int]:
        # x2many command heads in Odoo semantics:
        # create -> 0, update -> 1, remove/unlink -> 2/3, keep -> 4/6 (context-dependent)
        if row_state == "create":
            return [0]
        if row_state == "update":
            return [1]
        if row_state == "remove":
            return [2, 3]
        return [4, 6]

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
            return IntentExecutionResult(
                ok=True,
                data={
                    "schema_version": "v1",
                    "patch": {},
                    "modifiers_patch": {},
                    "line_patches": [],
                    "warnings": [],
                    "applied_fields": [],
                },
                meta={"model": model, "intent": self.INTENT_TYPE, "version": self.VERSION},
            )

        field_onchange = self._build_field_onchange_map(env_model)

        try:
            onchange_result = env_model.onchange(values, changed_fields, field_onchange)
        except Exception:
            onchange_result = {}

        if not isinstance(onchange_result, dict):
            onchange_result = {}

        patch = self._normalize_patch(env_model, onchange_result.get("value"))
        domain_patch = self._normalize_domain_patch(env_model, onchange_result.get("domain"))
        warnings = self._normalize_warning_list(onchange_result.get("warning"))
        line_patches = self._normalize_line_patches(env_model, onchange_result.get("line_patches"))

        # Prefer backend-supplied modifier patch if exists, then merge domain as supplement.
        modifiers_patch = self._normalize_modifiers_patch(env_model, onchange_result.get("modifiers_patch"))
        for field_name, field_domain in domain_patch.items():
            prev = modifiers_patch.get(field_name, {})
            prev["domain"] = field_domain
            modifiers_patch[field_name] = prev

        return IntentExecutionResult(
            ok=True,
            data={
                "schema_version": "v1",
                "patch": patch,
                "modifiers_patch": modifiers_patch,
                "line_patches": line_patches,
                "warnings": warnings,
                "applied_fields": changed_fields,
            },
            meta={"model": model, "intent": self.INTENT_TYPE, "version": self.VERSION},
        )
