from __future__ import annotations

from typing import Any, Dict, List


def build_registry_catalog_contract(result: Dict[str, Any]) -> Dict[str, Any]:
    entries = result.get("entries") or []
    if not isinstance(entries, list):
        entries = []
    normalized: List[Dict[str, Any]] = []
    for item in entries:
        if not isinstance(item, dict):
            continue
        normalized.append(
            {
                "intent_name": str(item.get("intent_name") or ""),
                "request_schema": str(item.get("request_schema") or ""),
                "response_contract": str(item.get("response_contract") or ""),
                "capability_code": str(item.get("capability_code") or ""),
                "permission_mode": str(item.get("permission_mode") or ""),
                "idempotent": bool(item.get("idempotent")),
                "version": str(item.get("version") or ""),
            }
        )
    return {
        "entries": normalized,
        "count": int(result.get("count") or len(normalized)),
        "version": str(result.get("version") or "v2"),
    }


def build_describe_model_contract(result: Dict[str, Any]) -> Dict[str, Any]:
    capabilities = result.get("capabilities") or {}
    if not isinstance(capabilities, dict):
        capabilities = {}
    fields = result.get("fields") or []
    if not isinstance(fields, list):
        fields = []
    return {
        "model": str(result.get("model") or ""),
        "display_name": str(result.get("display_name") or ""),
        "fields": fields,
        "capabilities": {
            "can_read": bool(capabilities.get("can_read")),
            "can_write": bool(capabilities.get("can_write")),
        },
        "source": str(result.get("source") or "v2-shadow"),
        "version": str(result.get("version") or "v2"),
    }


def build_permission_check_contract(result: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "model": str(result.get("model") or ""),
        "operation": str(result.get("operation") or "read"),
        "allowed": bool(result.get("allowed")),
        "reason_code": str(result.get("reason_code") or "UNKNOWN"),
        "source": str(result.get("source") or "v2-shadow"),
        "version": str(result.get("version") or "v2"),
    }


def build_intent_catalog_contract(result: Dict[str, Any]) -> Dict[str, Any]:
    intents = result.get("intents") or []
    if not isinstance(intents, list):
        intents = []
    intents_meta = result.get("intents_meta") or {}
    if not isinstance(intents_meta, dict):
        intents_meta = {}
    intent_catalog = result.get("intent_catalog") or intents
    if not isinstance(intent_catalog, list):
        intent_catalog = intents
    return {
        "intents": [str(name) for name in intents],
        "intents_meta": intents_meta,
        "intent_catalog": [str(name) for name in intent_catalog],
        "schema_version": str(result.get("schema_version") or "1.0.0"),
        "source": str(result.get("source") or "v2-shadow"),
        "version": str(result.get("version") or "v2"),
    }
