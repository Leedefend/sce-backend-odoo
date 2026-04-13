# smart_core/controllers/intent_legacy_compat.py
# -*- coding: utf-8 -*-

from __future__ import annotations

from typing import Any, Dict


def apply_legacy_load_view_compat(normalized: Any, intent_name: str) -> Any:
    if intent_name != "load_view" or not isinstance(normalized, dict):
        return normalized

    data = normalized.get("data")
    if data:
        return normalized

    if not any(key in normalized for key in ("layout", "view_type", "model", "permissions", "fields")):
        return normalized

    legacy_data: Dict[str, Any] = {
        key: normalized.pop(key)
        for key in list(normalized.keys())
        if key not in {"ok", "data", "meta", "code", "error", "status"}
    }
    normalized["data"] = legacy_data
    return normalized
