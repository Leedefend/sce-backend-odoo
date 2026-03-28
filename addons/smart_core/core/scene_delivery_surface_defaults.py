# -*- coding: utf-8 -*-
from __future__ import annotations

from typing import Any


def to_bool(value: Any, default: bool = False) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        text = value.strip().lower()
        if text in {"1", "true", "yes", "on"}:
            return True
        if text in {"0", "false", "no", "off"}:
            return False
    return default


def normalize_surface(value: Any) -> str:
    text = str(value or "").strip().lower()
    return text or "default"


def coerce_surface_input(value: Any) -> str:
    text = str(value or "").strip().lower()
    if text in {"", "false", "none", "null", "0"}:
        return ""
    return text


def is_internal_surface(surface: str) -> bool:
    value = normalize_surface(surface)
    return value in {"internal", "internal_ops", "ops_internal", "debug"}


def is_demo_surface(surface: str) -> bool:
    value = normalize_surface(surface)
    return value in {"demo", "showcase"}


def normalize_surfaces(raw: Any) -> list[str]:
    if not isinstance(raw, list):
        return []
    out = []
    seen = set()
    for item in raw:
        key = normalize_surface(item)
        if not key or key in seen:
            continue
        seen.add(key)
        out.append(key)
    return out
