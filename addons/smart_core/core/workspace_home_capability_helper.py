# -*- coding: utf-8 -*-
from __future__ import annotations

from typing import Any, Dict


def _to_text(value: Any) -> str:
    return str(value or "").strip()


def capability_state(cap: Dict[str, Any]) -> str:
    state = _to_text(cap.get("state")).upper()
    if state in {"READY", "LOCKED", "PREVIEW"}:
        return state
    capability_state_value = _to_text(cap.get("capability_state")).lower()
    if capability_state_value in {"allow", "readonly"}:
        return "READY"
    if capability_state_value in {"deny"}:
        return "LOCKED"
    if capability_state_value in {"pending", "coming_soon"}:
        return "PREVIEW"
    return "READY"


def metric_level(value: int, amber: int, red: int) -> str:
    if value >= red:
        return "red"
    if value >= amber:
        return "amber"
    return "green"


def is_urgent_capability(title: str, key: str) -> bool:
    merged = f"{_to_text(title)} {_to_text(key)}".lower()
    keywords = ("risk", "approval", "payment", "settlement", "风险", "审批", "付款", "结算")
    return any(keyword in merged for keyword in keywords)
