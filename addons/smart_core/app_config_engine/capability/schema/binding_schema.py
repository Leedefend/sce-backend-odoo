# -*- coding: utf-8 -*-
from __future__ import annotations

from typing import Any, Dict


def normalize_binding_payload(payload: Any) -> Dict[str, Dict[str, Any]]:
    if not isinstance(payload, dict):
        return {}
    normalized: Dict[str, Dict[str, Any]] = {}
    for key in ("scene", "intent", "contract", "exposure"):
        value = payload.get(key)
        if isinstance(value, dict):
            normalized[key] = dict(value)
    return normalized
