# -*- coding: utf-8 -*-
from __future__ import annotations

from typing import Any, Dict, List, Tuple

from .binding_schema import normalize_binding_payload
from .policy_schema import normalize_policy_payload


REQUIRED_IDENTITY_KEYS = ("key", "name", "domain", "type")
ALLOWED_TYPES = {
    "entry",
    "read",
    "execute",
    "governance",
    "operation",
    "export",
    "admin",
    "native_menu_entry",
    "native_window_action",
    "native_server_action",
    "native_report_action",
    "native_model_access",
    "native_view_binding",
    "platform_entry",
    "platform_operation",
}


def _to_text(value: Any, default: str = "") -> str:
    text = str(value or "").strip()
    return text or default


def _to_bool(value: Any, default: bool = False) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.strip().lower() in {"1", "true", "yes", "on"}
    if isinstance(value, (int, float)):
        return bool(value)
    return default


def _to_text_list(value: Any) -> List[str]:
    if not isinstance(value, list):
        return []
    out: List[str] = []
    for item in value:
        text = _to_text(item)
        if text and text not in out:
            out.append(text)
    return out


def _normalize_identity(payload: Any) -> Dict[str, Any]:
    if not isinstance(payload, dict):
        return {}
    normalized_type = _to_text(payload.get("type"))
    identity = {
        "key": _to_text(payload.get("key")),
        "name": _to_text(payload.get("name")),
        "domain": _to_text(payload.get("domain")),
        "type": normalized_type if normalized_type in ALLOWED_TYPES else "entry",
        "version": _to_text(payload.get("version"), "v1"),
    }
    return identity


def _normalize_ownership(payload: Any, *, source_module: str) -> Dict[str, str]:
    if not isinstance(payload, dict):
        payload = {}
    owner_module = _to_text(payload.get("owner_module"), "smart_core")
    source_text = _to_text(payload.get("source_module"), source_module)
    source_kind = _to_text(payload.get("source_kind"), "contribution")
    return {
        "owner_module": owner_module,
        "source_module": source_text,
        "source_kind": source_kind,
    }


def _normalize_ui(payload: Any) -> Dict[str, Any]:
    if not isinstance(payload, dict):
        payload = {}
    return {
        "label": _to_text(payload.get("label") or payload.get("name")),
        "hint": _to_text(payload.get("hint")),
        "group_key": _to_text(payload.get("group_key")),
        "icon": _to_text(payload.get("icon")),
        "sequence": int(payload.get("sequence") or 100),
        "tags": _to_text_list(payload.get("tags")),
    }


def _normalize_runtime(payload: Any) -> Dict[str, Any]:
    if not isinstance(payload, dict):
        payload = {}
    return {
        "supports_entry": _to_bool(payload.get("supports_entry"), True),
        "supports_execute": _to_bool(payload.get("supports_execute"), False),
        "supports_batch": _to_bool(payload.get("supports_batch"), False),
        "safe_fallback": _to_text(payload.get("safe_fallback")),
    }


def _normalize_audit(payload: Any) -> Dict[str, Any]:
    if not isinstance(payload, dict):
        payload = {}
    return {
        "audit_enabled": _to_bool(payload.get("audit_enabled"), True),
        "policy_trace_enabled": _to_bool(payload.get("policy_trace_enabled"), True),
        "owner_trace": _to_text(payload.get("owner_trace")),
    }


def normalize_capability_row(row: Any, *, source_module: str) -> Dict[str, Any] | None:
    if not isinstance(row, dict):
        return None
    identity = _normalize_identity(row.get("identity") if isinstance(row.get("identity"), dict) else row)
    if not identity.get("key"):
        return None
    normalized = {
        "identity": identity,
        "ownership": _normalize_ownership(row.get("ownership"), source_module=source_module),
        "ui": _normalize_ui(row.get("ui")),
        "binding": normalize_binding_payload(row.get("binding")),
        "runtime": _normalize_runtime(row.get("runtime")),
        "audit": _normalize_audit(row.get("audit")),
    }
    normalized.update(normalize_policy_payload(row))
    normalized["tags"] = _to_text_list(row.get("tags"))
    return normalized


def validate_capability_row(row: Dict[str, Any]) -> List[str]:
    errors: List[str] = []
    identity = row.get("identity") if isinstance(row, dict) else {}
    if not isinstance(identity, dict):
        return ["identity missing"]
    for key in REQUIRED_IDENTITY_KEYS:
        if not str(identity.get(key) or "").strip():
            errors.append(f"identity.{key} missing")
    if str(identity.get("type") or "").strip() not in ALLOWED_TYPES:
        errors.append("identity.type invalid")

    ownership = row.get("ownership") if isinstance(row.get("ownership"), dict) else {}
    if not str(ownership.get("owner_module") or "").strip():
        errors.append("ownership.owner_module missing")
    if not str(ownership.get("source_module") or "").strip():
        errors.append("ownership.source_module missing")

    release = row.get("release") if isinstance(row.get("release"), dict) else {}
    if not str(release.get("tier") or "").strip():
        errors.append("release.tier missing")

    lifecycle = row.get("lifecycle") if isinstance(row.get("lifecycle"), dict) else {}
    if not str(lifecycle.get("status") or "").strip():
        errors.append("lifecycle.status missing")
    return errors


def validate_and_normalize_rows(rows: Any, *, source_module: str) -> Tuple[List[Dict[str, Any]], List[str]]:
    out: List[Dict[str, Any]] = []
    errors: List[str] = []
    if not isinstance(rows, list):
        return out, errors
    for index, row in enumerate(rows):
        normalized = normalize_capability_row(row, source_module=source_module)
        if not isinstance(normalized, dict):
            errors.append(f"row[{index}] invalid")
            continue
        row_errors = validate_capability_row(normalized)
        if row_errors:
            errors.extend([f"row[{index}] {item}" for item in row_errors])
            continue
        out.append(normalized)
    return out, errors
