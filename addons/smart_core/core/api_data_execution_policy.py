# -*- coding: utf-8 -*-
from __future__ import annotations

from typing import Any


def _nested_get(mapping: dict[str, Any], key: str, default: Any = None) -> Any:
    if key in mapping:
        return mapping.get(key, default)
    for nested_key in ("payload", "params", "data", "args"):
        nested = mapping.get(nested_key)
        if isinstance(nested, dict) and key in nested:
            return nested.get(key, default)
    return default


def client_requested_sudo(params: dict[str, Any]) -> bool:
    if not isinstance(params, dict):
        return False
    value = _nested_get(params, "sudo", False)
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return bool(value)
    if isinstance(value, str):
        return value.strip().lower() in ("1", "true", "yes", "y", "on")
    return False


def resolve_api_data_sudo(params: dict[str, Any]) -> bool:
    """api.data must not let client payloads choose an elevated ORM environment."""
    return False
