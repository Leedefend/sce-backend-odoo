# -*- coding: utf-8 -*-
from __future__ import annotations

from typing import Any


def parse_bool(value: Any, default: bool = False) -> bool:
    if value is None:
        return default
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return bool(value)
    if isinstance(value, str):
        text = value.strip().lower()
        if text in ("1", "true", "yes", "y", "on"):
            return True
        if text in ("0", "false", "no", "n", "off", ""):
            return False
    return default


def parse_positive_int(value: Any, *, allow_empty: bool = False):
    if value is None:
        if allow_empty:
            return None, None
        return None, "missing"
    if isinstance(value, str) and not value.strip():
        if allow_empty:
            return None, None
        return None, "missing"
    if value is False and allow_empty:
        return None, None
    if isinstance(value, bool):
        return None, "invalid"
    try:
        parsed = int(value)
    except Exception:
        return None, "invalid"
    if parsed <= 0:
        return None, "invalid"
    return parsed, None


def parse_non_negative_int(value: Any, *, allow_empty: bool = False):
    if value is None:
        if allow_empty:
            return None, None
        return None, "missing"
    if isinstance(value, str) and not value.strip():
        if allow_empty:
            return None, None
        return None, "missing"
    if value is False and allow_empty:
        return None, None
    if isinstance(value, bool):
        return None, "invalid"
    try:
        parsed = int(value)
    except Exception:
        return None, "invalid"
    if parsed < 0:
        return None, "invalid"
    return parsed, None
