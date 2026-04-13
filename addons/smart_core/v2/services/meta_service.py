from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List


_ROOT = Path(__file__).resolve().parents[4]
_LEGACY_FIELDS_BASELINE = _ROOT / "artifacts" / "contract" / "rootfix" / "menu_278_admin.json"


class MetaService:
    def _load_legacy_project_fields(self) -> Dict[str, Any]:
        if not _LEGACY_FIELDS_BASELINE.exists():
            return {}
        try:
            payload = json.loads(_LEGACY_FIELDS_BASELINE.read_text(encoding="utf-8"))
        except Exception:
            return {}
        if not isinstance(payload, dict):
            return {}
        raw = payload.get("ui_contract_raw") if isinstance(payload.get("ui_contract_raw"), dict) else {}
        fields = raw.get("fields") if isinstance(raw.get("fields"), dict) else {}
        return fields

    def _generic_fields(self) -> Dict[str, Any]:
        return {
            "id": {"name": "id", "string": "ID", "type": "integer", "readonly": True, "required": False},
            "name": {"name": "name", "string": "Name", "type": "char", "readonly": False, "required": True},
            "create_date": {
                "name": "create_date",
                "string": "Created on",
                "type": "datetime",
                "readonly": True,
                "required": False,
            },
            "write_date": {
                "name": "write_date",
                "string": "Last Updated on",
                "type": "datetime",
                "readonly": True,
                "required": False,
            },
            "active": {"name": "active", "string": "Active", "type": "boolean", "readonly": False, "required": False},
        }

    def build_intent_catalog(self, registry_entries: Dict[str, Any]) -> Dict[str, Any]:
        intents = sorted(registry_entries.keys())
        intents_meta: Dict[str, Dict[str, Any]] = {}
        for name in intents:
            entry = registry_entries[name]
            intents_meta[name] = {
                "request_schema": getattr(entry, "request_schema", ""),
                "response_contract": getattr(entry, "response_contract", ""),
                "permission_mode": getattr(entry, "permission_mode", ""),
                "capability_code": getattr(entry, "capability_code", ""),
                "version": getattr(entry, "version", ""),
            }
        return {
            "intents": intents,
            "intents_meta": intents_meta,
            "intent_catalog": intents,
            "schema_version": "1.0.0",
            "source": "v2-shadow",
            "version": "v2",
        }

    def list_registry_catalog(self, registry_entries: Dict[str, Any]) -> Dict[str, Any]:
        out: List[Dict[str, Any]] = []
        for intent_name in sorted(registry_entries.keys()):
            entry = registry_entries[intent_name]
            out.append(
                {
                    "intent_name": intent_name,
                    "request_schema": getattr(entry, "request_schema", ""),
                    "response_contract": getattr(entry, "response_contract", ""),
                    "capability_code": getattr(entry, "capability_code", ""),
                    "permission_mode": getattr(entry, "permission_mode", ""),
                    "idempotent": bool(getattr(entry, "idempotent", False)),
                    "version": getattr(entry, "version", ""),
                }
            )
        return {
            "entries": out,
            "count": len(out),
            "version": "v2",
        }

    def describe_model_stub(self, model_name: str) -> Dict[str, Any]:
        normalized = str(model_name or "").strip()
        fields = self._generic_fields()
        if normalized == "project.project":
            project_fields = self._load_legacy_project_fields()
            if project_fields:
                fields = project_fields
        return {
            "model": normalized,
            "display_name": normalized or "unknown",
            "fields": fields,
            "capabilities": {
                "can_read": True,
                "can_write": False,
            },
            "source": "v2-shadow",
            "version": "v2",
        }

    def permission_check_stub(self, model_name: str, operation: str, user_id: int) -> Dict[str, Any]:
        normalized_model = str(model_name or "").strip()
        normalized_operation = str(operation or "read").strip().lower() or "read"
        is_authenticated = int(user_id or 0) > 0
        allowed = bool(is_authenticated and normalized_model)
        return {
            "model": normalized_model,
            "operation": normalized_operation,
            "allowed": allowed,
            "reason_code": "OK" if allowed else "PERMISSION_DENIED",
            "source": "v2-shadow",
            "version": "v2",
        }
