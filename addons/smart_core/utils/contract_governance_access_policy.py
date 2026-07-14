# -*- coding: utf-8 -*-
from __future__ import annotations

from typing import Any


def _safe_text(value: Any, fallback: str = "") -> str:
    text = str(value or "").strip()
    if text.lower() in {"undefined", "null"}:
        text = ""
    return text or fallback


def _as_dict(value: Any) -> dict:
    return dict(value) if isinstance(value, dict) else {}


def realign_access_policy_with_visible_fields(data: dict) -> None:
    fields_map = _as_dict(data.get("fields"))
    policy = _as_dict(data.get("access_policy"))
    if not policy:
        return

    visible = set()
    for name in (data.get("visible_fields") or []):
        field_name = _safe_text(name)
        if field_name and field_name in fields_map:
            visible.add(field_name)
    if not visible:
        visible = set(fields_map.keys())

    def _normalize_rows(rows: Any) -> list[dict]:
        out: list[dict] = []
        if not isinstance(rows, list):
            return out
        for row in rows:
            if not isinstance(row, dict):
                continue
            field_name = _safe_text(row.get("field"))
            if not field_name:
                continue
            if field_name != "__model__" and field_name not in visible:
                continue
            out.append(
                {
                    "field": field_name,
                    "model": _safe_text(row.get("model")),
                    "reason_code": _safe_text(row.get("reason_code")),
                }
            )
        return out

    blocked_rows = _normalize_rows(policy.get("blocked_fields"))
    degraded_rows = _normalize_rows(policy.get("degraded_fields"))
    mode = "allow"
    reason_code = ""
    message = ""
    if blocked_rows:
        mode = "block"
        first = blocked_rows[0]
        reason_code = _safe_text(first.get("reason_code"), "RELATION_READ_FORBIDDEN_CORE")
        if reason_code == "RELATION_READ_FORBIDDEN":
            reason_code = "RELATION_READ_FORBIDDEN_CORE"
        label = _safe_text(first.get("field") or first.get("model"), "unknown")
        message = f"core field access blocked: {label}"
    elif degraded_rows:
        mode = "degrade"
        first = degraded_rows[0]
        reason_code = _safe_text(first.get("reason_code"), "RELATION_READ_FORBIDDEN")
        label = _safe_text(first.get("field") or first.get("model"), "unknown")
        message = f"relation access degraded: {label}"

    policy["mode"] = mode
    policy["reason_code"] = reason_code
    policy["message"] = message
    policy["blocked_fields"] = blocked_rows
    policy["degraded_fields"] = degraded_rows
    data["access_policy"] = policy

    warnings = data.get("warnings") if isinstance(data.get("warnings"), list) else []
    warnings = [item for item in warnings if not (_safe_text(item).startswith("access_policy:"))]
    if mode in {"block", "degrade"}:
        marker = f"access_policy:{mode}:{reason_code or 'UNKNOWN'}"
        if marker not in warnings:
            warnings.append(marker)
    if warnings:
        data["warnings"] = warnings
    else:
        data.pop("warnings", None)
