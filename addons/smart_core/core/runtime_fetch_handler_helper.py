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
