# -*- coding: utf-8 -*-
from __future__ import annotations

from typing import Any


def parse_runtime_fetch_params(payload, params) -> dict[str, Any]:
    row = payload or params or {}
    if isinstance(row, dict) and isinstance(row.get("params"), dict):
        return row.get("params") or {}
    return row if isinstance(row, dict) else {}


def build_runtime_fetch_meta(intent: str, context: dict[str, Any] | None) -> dict[str, str]:
    return {
        "intent": str(intent or "").strip(),
        "trace_id": str((context or {}).get("trace_id") or ""),
    }


def build_runtime_fetch_error_response(
    *,
    intent: str,
    context: dict[str, Any] | None,
    code: str,
    message: str,
    suggested_action: str,
) -> dict[str, Any]:
    return {
        "ok": False,
        "error": {
            "code": str(code or "").strip(),
            "message": str(message or ""),
            "suggested_action": str(suggested_action or "").strip(),
        },
        "meta": build_runtime_fetch_meta(intent, context),
    }


def build_runtime_fetch_success_response(
    *,
    intent: str,
    context: dict[str, Any] | None,
    data: dict[str, Any] | None,
) -> dict[str, Any]:
    return {
        "ok": True,
        "data": data if isinstance(data, dict) else {},
        "meta": build_runtime_fetch_meta(intent, context),
    }


def resolve_runtime_fetch_page_key(params: dict[str, Any] | None) -> str:
    row = params if isinstance(params, dict) else {}
    return str(row.get("page_key") or row.get("key") or "").strip().lower()


def resolve_runtime_fetch_collection_keys(params: dict[str, Any] | None) -> list[str]:
    row = params if isinstance(params, dict) else {}
    raw_keys = row.get("keys")
    return raw_keys if isinstance(raw_keys, list) else []


def build_runtime_fetch_page_payload(page_key: str, page_contract: Any) -> dict[str, Any]:
    return {
        "page_key": str(page_key or "").strip().lower(),
        "page_contract": page_contract,
    }


def build_runtime_fetch_collections_payload(collections: dict[str, Any] | None) -> dict[str, Any]:
    rows = collections if isinstance(collections, dict) else {}
    return {
        "collections": rows,
        "keys": sorted(list(rows.keys())),
        "count": len(rows),
    }
