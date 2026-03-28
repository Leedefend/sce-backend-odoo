# -*- coding: utf-8 -*-
from __future__ import annotations

from datetime import datetime
from typing import Any, Callable, Dict


def _to_text(value: Any) -> str:
    return str(value or "").strip()


def _to_int(value: Any) -> int:
    try:
        number = int(value)
        return number if number >= 0 else 0
    except Exception:
        return 0


def workspace_v1_copy(defaults: Dict[str, str], provider: Any = None) -> Dict[str, str]:
    out = dict(defaults or {})
    if provider is None:
        return out
    fn = getattr(provider, "build_v1_copy_overrides", None)
    if not callable(fn):
        return out
    try:
        payload = fn()
    except Exception:
        payload = None
    if not isinstance(payload, dict):
        return out
    for key, value in payload.items():
        normalized_key = _to_text(key)
        normalized_value = _to_text(value)
        if normalized_key and normalized_value:
            out[normalized_key] = normalized_value
    return out


def impact_score(row: Dict[str, Any]) -> int:
    amount_raw = (
        row.get("amount")
        or row.get("amount_total")
        or row.get("contract_amount")
        or row.get("budget")
        or row.get("value")
        or 0
    )
    try:
        amount = float(amount_raw)
    except Exception:
        amount = 0.0
    project_count = _to_int(row.get("project_count") or row.get("affected_projects") or row.get("scope_count") or 0)
    score = 0
    if amount >= 100000000:
        score += 30
    elif amount >= 10000000:
        score += 22
    elif amount >= 1000000:
        score += 14
    elif amount > 0:
        score += 8
    if project_count >= 5:
        score += 12
    elif project_count >= 2:
        score += 8
    elif project_count >= 1:
        score += 4
    return min(40, score)


def urgency_score(
    *,
    row: Dict[str, Any],
    title: str,
    source_key: str,
    status_text: str,
    role_code: str = "",
    source_kind: str = "business",
    keyword_overrides: Dict[str, Any] | None = None,
    ranking_profile_builder: Callable[[str], Dict[str, int]],
    provider_token_set_builder: Callable[[str, tuple[str, ...], Dict[str, Any] | None], tuple[str, ...]],
    urgent_capability_checker: Callable[[str, str], bool],
    deadline_parser: Callable[[Any], datetime | None],
) -> int:
    profile = ranking_profile_builder(role_code)
    severity_weight = _to_int(profile.get("severity_weight") or 0)
    deadline_weight = _to_int(profile.get("deadline_weight") or 0)
    pending_weight = _to_int(profile.get("pending_weight") or 0)
    source_weight = _to_int(profile.get("source_weight") or 0)
    impact_weight = _to_int(profile.get("impact_weight") or 0)

    score = 0
    merged = f"{status_text} {title} {_to_text(source_key)}".lower()
    critical_tokens = provider_token_set_builder(
        "build_critical_status_tokens",
        ("critical", "urgent", "overdue", "严重", "紧急", "逾期", "高"),
        keyword_overrides,
    )
    warning_tokens = provider_token_set_builder(
        "build_warning_status_tokens",
        ("warning", "high", "关注", "预警", "待处理"),
        keyword_overrides,
    )
    if any(token in merged for token in critical_tokens):
        score += severity_weight
    elif any(token in merged for token in warning_tokens):
        score += max(20, int(severity_weight * 0.58))
    if urgent_capability_checker(title, source_key):
        score += max(8, int(severity_weight * 0.33))

    deadline = (
        deadline_parser(row.get("due_date"))
        or deadline_parser(row.get("deadline"))
        or deadline_parser(row.get("planned_date"))
        or deadline_parser(row.get("date_deadline"))
    )
    if deadline is not None:
        now_dt = datetime.now(deadline.tzinfo) if deadline.tzinfo else datetime.now()
        days = (deadline - now_dt).total_seconds() / 86400
        if days < 0:
            score += deadline_weight
        elif days <= 1:
            score += max(18, int(deadline_weight * 0.72))
        elif days <= 3:
            score += max(12, int(deadline_weight * 0.45))
        elif days <= 7:
            score += max(6, int(deadline_weight * 0.22))

    score += min(pending_weight, _to_int(row.get("count") or row.get("pending_count")))
    score += min(impact_weight, impact_score(row))
    if _to_text(source_kind) == "business":
        score += source_weight
    return score
