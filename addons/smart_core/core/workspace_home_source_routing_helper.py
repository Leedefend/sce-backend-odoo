# -*- coding: utf-8 -*-
from __future__ import annotations

from datetime import datetime
from typing import Any, Callable, Dict, Iterable


def _to_text(value: Any) -> str:
    return str(value or "").strip()


def provider_token_set(
    hook_name: str,
    defaults: Iterable[str],
    *,
    keyword_overrides: Dict[str, Any] | None = None,
    provider: Any = None,
) -> tuple[str, ...]:
    base = tuple(_to_text(item).lower() for item in (defaults or []) if _to_text(item))
    override_bucket = keyword_overrides.get("token_sets") if isinstance(keyword_overrides, dict) else {}
    if isinstance(override_bucket, dict):
        override_tokens = override_bucket.get(hook_name)
        if isinstance(override_tokens, (list, tuple, set)):
            normalized_override = tuple(_to_text(item).lower() for item in override_tokens if _to_text(item))
            if normalized_override:
                return normalized_override
    if provider is None:
        return base
    fn = getattr(provider, hook_name, None)
    if not callable(fn):
        return base
    try:
        payload = fn()
    except Exception:
        payload = None
    if not isinstance(payload, (list, tuple, set)):
        return base
    normalized = tuple(_to_text(item).lower() for item in payload if _to_text(item))
    return normalized or base


def is_risk_semantic_action(
    source_key: str,
    row: Dict[str, Any],
    action: Dict[str, Any],
    *,
    keyword_overrides: Dict[str, Any] | None = None,
    provider: Any = None,
) -> bool:
    source_text = _to_text(source_key).lower()
    status_text = _to_text(action.get("status") or row.get("status") or row.get("state") or row.get("severity") or row.get("level")).lower()
    title_text = _to_text(action.get("title") or row.get("title") or row.get("name") or row.get("label")).lower()
    desc_text = _to_text(action.get("description") or row.get("description") or row.get("summary")).lower()
    scene_text = _to_text(action.get("scene_key") or row.get("scene_key") or row.get("scene")).lower()
    route_text = _to_text(action.get("route") or row.get("route")).lower()
    merged = " ".join([source_text, status_text, title_text, desc_text, scene_text, route_text])

    risk_tokens = provider_token_set(
        "build_risk_semantic_tokens",
        (
            "risk",
            "alert",
            "warning",
            "exception",
            "overdue",
            "blocked",
            "critical",
            "urgent",
            "payment",
            "cost",
            "contract",
            "delay",
            "风险",
            "预警",
            "异常",
            "逾期",
            "阻塞",
            "严重",
            "紧急",
            "付款",
            "成本",
            "合同",
            "延期",
        ),
        keyword_overrides=keyword_overrides,
        provider=provider,
    )
    return any(token in merged for token in risk_tokens)


def route_scene_by_source(
    source_key: str,
    *,
    workspace_scene_resolver: Callable[[str], str],
    keyword_overrides: Dict[str, Any] | None = None,
    provider: Any = None,
) -> str:
    text = _to_text(source_key).lower()
    override_routes = keyword_overrides.get("source_scene_routes") if isinstance(keyword_overrides, dict) else {}
    if isinstance(override_routes, dict):
        for token, target in override_routes.items():
            token_text = _to_text(token).lower()
            target_text = _to_text(target)
            if token_text and target_text and token_text in text:
                return workspace_scene_resolver(target_text)
    if provider is not None:
        fn = getattr(provider, "resolve_scene_by_source", None)
        if callable(fn):
            try:
                resolved = _to_text(fn(source_key))
                if resolved:
                    return resolved
            except Exception:
                pass
    if "risk" in text or "风险" in text:
        return workspace_scene_resolver("risk_center")
    if "task" in text or "任务" in text:
        return workspace_scene_resolver("task_center")
    if "cost" in text or "boq" in text or "成本" in text:
        return workspace_scene_resolver("cost_center")
    if "payment" in text or "finance" in text or "付款" in text or "财务" in text:
        return workspace_scene_resolver("default")
    if "project" in text or "项目" in text:
        return workspace_scene_resolver("project_list")
    return workspace_scene_resolver("default")


def parse_deadline(value: Any) -> datetime | None:
    text = _to_text(value)
    if not text:
        return None
    normalized = text.replace("Z", "+00:00")
    for candidate in (normalized, normalized.split(" ")[0]):
        try:
            return datetime.fromisoformat(candidate)
        except Exception:
            continue
    return None
