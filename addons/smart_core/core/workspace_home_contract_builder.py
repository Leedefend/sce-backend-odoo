# -*- coding: utf-8 -*-
from __future__ import annotations

from collections import Counter
from datetime import datetime
from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path
from typing import Any, Dict, Iterable, List, Tuple
from urllib.parse import parse_qs, urlparse

from odoo import fields

from .workspace_home_shell_helper import (
    build_workspace_scene_aliases,
    merge_workspace_mapping_overrides,
    resolve_workspace_keyword_overrides,
    resolve_workspace_scene,
)
from .workspace_home_read_model_helper import (
    as_record_list,
    extract_business_collections,
    scene_from_route,
)
from .workspace_home_loader_helper import (
    load_workspace_data_provider,
    load_workspace_scene_engine,
    resolve_action_target,
)
from .workspace_home_capability_helper import (
    capability_state,
    is_urgent_capability,
    metric_level,
)
from .workspace_home_source_routing_helper import (
    is_risk_semantic_action,
    parse_deadline,
    provider_token_set,
    route_scene_by_source,
)
from .workspace_home_ranking_helper import (
    impact_score,
    urgency_score,
    workspace_v1_copy,
)

def _load_semantics_registry() -> Dict[str, Any]:
    registry_path = Path(__file__).with_name("orchestration_semantics.py")
    try:
        spec = spec_from_file_location("smart_core_orchestration_semantics_workspace_home", registry_path)
        if spec is None or spec.loader is None:
            raise RuntimeError("spec unavailable")
        module = module_from_spec(spec)
        spec.loader.exec_module(module)
        return {
            "BLOCK_TYPES": tuple(getattr(module, "BLOCK_TYPES", ()) or ()),
            "STATE_TONES": tuple(getattr(module, "STATE_TONES", ()) or ()),
            "PROGRESS_STATES": tuple(getattr(module, "PROGRESS_STATES", ()) or ()),
        }
    except Exception:
        return {}


_SEM = _load_semantics_registry()
BLOCK_TYPES = _SEM.get("BLOCK_TYPES") or (
    "hero_metric",
    "metric_row",
    "todo_list",
    "alert_panel",
    "progress_summary",
    "entry_grid",
    "accordion_group",
    "record_summary",
    "activity_feed",
)
STATE_TONES = _SEM.get("STATE_TONES") or ("success", "warning", "danger", "info", "neutral")
PROGRESS_STATES = _SEM.get("PROGRESS_STATES") or ("overdue", "blocked", "pending", "running", "completed")
_ACTION_TARGET_RESOLVER = None
_DATA_PROVIDER_MODULE = None
_SCENE_ENGINE_MODULE = None


def _workspace_scene_aliases() -> Dict[str, str]:
    return build_workspace_scene_aliases(_load_data_provider())


def _workspace_scene(name: str) -> str:
    return resolve_workspace_scene(name, _workspace_scene_aliases())


def _resolve_workspace_keyword_overrides(data: Dict[str, Any]) -> Dict[str, Any]:
    return resolve_workspace_keyword_overrides(data)


def _workspace_layout_texts(defaults: Dict[str, str]) -> Dict[str, str]:
    return merge_workspace_mapping_overrides(
        defaults,
        _load_data_provider(),
        override_builder="build_layout_texts_overrides",
    )


def _workspace_layout_actions(defaults: Dict[str, str]) -> Dict[str, str]:
    return merge_workspace_mapping_overrides(
        defaults,
        _load_data_provider(),
        override_builder="build_layout_actions_overrides",
    )


def _workspace_hero_payload(*, has_business_signal: bool, gap_level: str, updated_at: str, partial_notice: str) -> Dict[str, Any]:
    defaults = {
        "title": "工作台",
        "lead": "先做什么、状态如何、下一步去哪：围绕今日行动推进工作闭环。",
        "product_tags": ["工作协同", "状态洞察", "系统提醒"],
        "updated_at": updated_at,
        "status_notice": partial_notice,
        "status_detail": (
            "当前业务明细不足，主区已回退到系统就绪入口。"
            if not has_business_signal
            else "当前角色可见业务数据偏少，建议核对数据权限与分配策略。"
            if gap_level == "limited"
            else ""
        ),
    }
    provider = _load_data_provider()
    if provider is None:
        return defaults
    fn = getattr(provider, "build_workspace_hero_payload", None)
    if not callable(fn):
        return defaults
    try:
        payload = fn(
            has_business_signal=bool(has_business_signal),
            gap_level=_to_text(gap_level),
            updated_at=_to_text(updated_at),
            partial_notice=_to_text(partial_notice),
        )
    except Exception:
        payload = None
    if not isinstance(payload, dict):
        return defaults
    merged = dict(defaults)
    for key in ("title", "lead", "updated_at", "status_notice", "status_detail"):
        text = _to_text(payload.get(key))
        if text:
            merged[key] = text
    tags = payload.get("product_tags")
    if isinstance(tags, list):
        normalized = [_to_text(item) for item in tags if _to_text(item)]
        if normalized:
            merged["product_tags"] = normalized
    return merged


def _workspace_risk_summary_text(risk_red: int) -> str:
    provider = _load_data_provider()
    if provider is not None:
        fn = getattr(provider, "build_risk_summary_text", None)
        if callable(fn):
            try:
                text = _to_text(fn(risk_red=int(risk_red or 0)))
                if text:
                    return text
            except Exception:
                pass
    if risk_red >= 3:
        return "存在高优先告警，请先处理系统提醒事项。"
    if risk_red >= 1:
        return "存在需要跟进的告警，建议今日内完成处理。"
    return "当前未出现严重告警，建议保持日常巡检节奏。"


def _workspace_ops_payload(*, has_business_signal: bool, risk_business_count: int, today_business_count: int) -> Dict[str, Any]:
    provider = _load_data_provider()
    if provider is not None:
        fn = getattr(provider, "build_ops_payload", None)
        if callable(fn):
            try:
                payload = fn(
                    has_business_signal=bool(has_business_signal),
                    risk_business_count=int(risk_business_count or 0),
                    today_business_count=int(today_business_count or 0),
                )
                if isinstance(payload, dict):
                    bars = payload.get("bars") if isinstance(payload.get("bars"), dict) else {}
                    kpi = payload.get("kpi") if isinstance(payload.get("kpi"), dict) else {}
                    return {
                        "bars": {
                            "contract": _to_int(bars.get("contract")),
                            "output": _to_int(bars.get("output")),
                        },
                        "kpi": {
                            "cost_rate": _to_int(kpi.get("cost_rate")),
                            "payment_rate": _to_int(kpi.get("payment_rate")),
                            "cost_rate_delta": _to_int(kpi.get("cost_rate_delta")),
                            "payment_rate_delta": _to_int(kpi.get("payment_rate_delta")),
                            "output_trend_delta": _to_int(kpi.get("output_trend_delta")),
                        },
                    }
            except Exception:
                pass
    return {
        "bars": {
            "contract": max(0, min(100, 100 - (risk_business_count * 10))) if has_business_signal else 0,
            "output": max(0, min(100, 100 - (today_business_count * 8))) if has_business_signal else 0,
        },
        "kpi": {
            "cost_rate": max(0, min(100, 100 - (risk_business_count * 12))) if has_business_signal else 0,
            "payment_rate": max(0, min(100, 100 - (today_business_count * 6))) if has_business_signal else 0,
            "cost_rate_delta": 0,
            "payment_rate_delta": 0,
            "output_trend_delta": 0,
        },
    }


def _workspace_risk_payload(
    *,
    summary: str,
    risk_red: int,
    risk_amber: int,
    risk_green: int,
    risk_d30: int,
    risk_d7: int,
    risk_now: int,
    risk_max: int,
    risk_actions: List[Dict[str, Any]],
    permission_denied: int,
) -> Dict[str, Any]:
    defaults = {
        "summary": summary,
        "buckets": {"red": int(risk_red or 0), "amber": int(risk_amber or 0), "green": int(risk_green or 0)},
        "tone": "danger" if risk_red > 0 else "warning" if risk_amber > 0 else "success",
        "progress": "blocked" if risk_red > 0 else "running",
        "trend": [
            {"label": "30天前", "value": int(risk_d30 or 0), "percent": round((risk_d30 / risk_max) * 100)},
            {"label": "7天前", "value": int(risk_d7 or 0), "percent": round((risk_d7 / risk_max) * 100)},
            {"label": "当前", "value": int(risk_now or 0), "percent": round((risk_now / risk_max) * 100)},
        ],
        "sources": [
            {"label": "业务告警动作", "count": len([row for row in risk_actions if _to_text(row.get("source")) == "business"])},
            {"label": "能力兜底动作", "count": len([row for row in risk_actions if _to_text(row.get("source")) != "business"])},
            {"label": "权限限制", "count": int(permission_denied or 0)},
        ],
        "actions": list(risk_actions or []),
    }
    provider = _load_data_provider()
    if provider is None:
        return defaults
    fn = getattr(provider, "build_risk_payload", None)
    if not callable(fn):
        return defaults
    try:
        payload = fn(
            defaults=defaults,
            summary=_to_text(summary),
            risk_red=int(risk_red or 0),
            risk_amber=int(risk_amber or 0),
            risk_green=int(risk_green or 0),
            risk_actions=list(risk_actions or []),
            permission_denied=int(permission_denied or 0),
        )
    except Exception:
        payload = None
    if not isinstance(payload, dict):
        return defaults
    merged = dict(defaults)
    text = _to_text(payload.get("summary"))
    if text:
        merged["summary"] = text
    buckets = payload.get("buckets")
    if isinstance(buckets, dict):
        merged["buckets"] = {
            "red": _to_int(buckets.get("red")),
            "amber": _to_int(buckets.get("amber")),
            "green": _to_int(buckets.get("green")),
        }
    tone = _to_text(payload.get("tone"))
    if tone in STATE_TONES:
        merged["tone"] = tone
    progress = _to_text(payload.get("progress"))
    if progress in PROGRESS_STATES:
        merged["progress"] = progress
    trend = payload.get("trend")
    if isinstance(trend, list) and trend:
        normalized_trend: List[Dict[str, Any]] = []
        for row in trend:
            if not isinstance(row, dict):
                continue
            normalized_trend.append(
                {
                    "label": _to_text(row.get("label")) or "-",
                    "value": _to_int(row.get("value")),
                    "percent": _to_int(row.get("percent")),
                }
            )
        if normalized_trend:
            merged["trend"] = normalized_trend
    sources = payload.get("sources")
    if isinstance(sources, list) and sources:
        normalized_sources: List[Dict[str, Any]] = []
        for row in sources:
            if not isinstance(row, dict):
                continue
            normalized_sources.append(
                {
                    "label": _to_text(row.get("label")) or "-",
                    "count": _to_int(row.get("count")),
                }
            )
        if normalized_sources:
            merged["sources"] = normalized_sources
    actions = payload.get("actions")
    if isinstance(actions, list):
        merged["actions"] = actions
    return merged


def _workspace_ops_meta(*, has_business_signal: bool) -> Dict[str, str]:
    defaults = {
        "tone": "info",
        "progress": "running",
        "data_state": "business" if has_business_signal else "fallback",
    }
    provider = _load_data_provider()
    if provider is None:
        return defaults
    fn = getattr(provider, "build_ops_meta", None)
    if not callable(fn):
        return defaults
    try:
        payload = fn(defaults=defaults, has_business_signal=bool(has_business_signal))
    except Exception:
        payload = None
    if not isinstance(payload, dict):
        return defaults
    merged = dict(defaults)
    tone = _to_text(payload.get("tone"))
    if tone in STATE_TONES:
        merged["tone"] = tone
    progress = _to_text(payload.get("progress"))
    if progress in PROGRESS_STATES:
        merged["progress"] = progress
    data_state = _to_text(payload.get("data_state"))
    if data_state in ("business", "fallback", "mixed"):
        merged["data_state"] = data_state
    return merged


def _shared_action_target(action_key: str, page_key: str) -> Dict[str, Any]:
    global _ACTION_TARGET_RESOLVER
    payload, resolver = resolve_action_target(
        action_key,
        page_key,
        cached_resolver=_ACTION_TARGET_RESOLVER,
        base_path=Path(__file__),
    )
    if callable(resolver):
        _ACTION_TARGET_RESOLVER = resolver
    return payload


def _load_data_provider():
    global _DATA_PROVIDER_MODULE
    module = load_workspace_data_provider(cached_module=_DATA_PROVIDER_MODULE, base_path=Path(__file__))
    _DATA_PROVIDER_MODULE = module
    return None if module is False else module


def _load_scene_engine_module():
    global _SCENE_ENGINE_MODULE
    module = load_workspace_scene_engine(cached_module=_SCENE_ENGINE_MODULE, base_path=Path(__file__))
    _SCENE_ENGINE_MODULE = module
    return None if module is False else module


def _to_text(value: Any) -> str:
    text = str(value or "").strip()
    return text


def _to_int(value: Any) -> int:
    try:
        number = int(value)
        return number if number >= 0 else 0
    except Exception:
        return 0


def _capability_state(cap: Dict[str, Any]) -> str:
    return capability_state(cap)


def _scene_from_route(route: str) -> str:
    return scene_from_route(route)


def _metric_level(value: int, amber: int, red: int) -> str:
    return metric_level(value, amber, red)


def _is_urgent_capability(title: str, key: str) -> bool:
    return is_urgent_capability(title, key)


def _as_record_list(payload: Any) -> List[Dict[str, Any]]:
    return as_record_list(payload)


def _extract_business_collections(data: Dict[str, Any]) -> Dict[str, List[Dict[str, Any]]]:
    return extract_business_collections(data)


def _provider_token_set(
    hook_name: str,
    defaults: Iterable[str],
    keyword_overrides: Dict[str, Any] | None = None,
) -> Tuple[str, ...]:
    return provider_token_set(
        hook_name,
        defaults,
        keyword_overrides=keyword_overrides,
        provider=_load_data_provider(),
    )


def _is_risk_semantic_action(
    source_key: str,
    row: Dict[str, Any],
    action: Dict[str, Any],
    keyword_overrides: Dict[str, Any] | None = None,
) -> bool:
    return is_risk_semantic_action(
        source_key,
        row,
        action,
        keyword_overrides=keyword_overrides,
        provider=_load_data_provider(),
    )


def _route_scene_by_source(source_key: str, keyword_overrides: Dict[str, Any] | None = None) -> str:
    return route_scene_by_source(
        source_key,
        workspace_scene_resolver=_workspace_scene,
        keyword_overrides=keyword_overrides,
        provider=_load_data_provider(),
    )


def _parse_deadline(value: Any) -> datetime | None:
    return parse_deadline(value)


def _role_ranking_profile(role_code: str) -> Dict[str, int]:
    provider = _load_data_provider()
    if provider is not None:
        fn = getattr(provider, "build_role_ranking_profile", None)
        if callable(fn):
            try:
                payload = fn(_to_text(role_code).lower())
                if isinstance(payload, dict):
                    return {
                        "severity_weight": _to_int(payload.get("severity_weight") or 0),
                        "deadline_weight": _to_int(payload.get("deadline_weight") or 0),
                        "pending_weight": _to_int(payload.get("pending_weight") or 0),
                        "source_weight": _to_int(payload.get("source_weight") or 0),
                        "impact_weight": _to_int(payload.get("impact_weight") or 0),
                    }
            except Exception:
                pass

    role = _to_text(role_code).lower()
    if role == "finance":
        return {
            "severity_weight": 55,
            "deadline_weight": 45,
            "pending_weight": 12,
            "source_weight": 10,
            "impact_weight": 22,
        }
    if role == "owner":
        return {
            "severity_weight": 65,
            "deadline_weight": 35,
            "pending_weight": 8,
            "source_weight": 8,
            "impact_weight": 28,
        }
    return {
        "severity_weight": 60,
        "deadline_weight": 40,
        "pending_weight": 15,
        "source_weight": 12,
        "impact_weight": 20,
    }


def _workspace_expected_collections(role_code: str) -> List[str]:
    provider = _load_data_provider()
    if provider is not None:
        fn = getattr(provider, "build_expected_collections", None)
        if callable(fn):
            try:
                payload = fn(_to_text(role_code).lower())
                if isinstance(payload, list):
                    normalized = [_to_text(item) for item in payload if _to_text(item)]
                    if normalized:
                        return normalized
            except Exception:
                pass

    default_by_role = {
        "pm": ["today_actions", "alerts", "tasks"],
        "finance": ["today_actions", "alerts", "records"],
        "owner": ["today_actions", "alerts", "tasks"],
    }
    return default_by_role.get(_to_text(role_code).lower(), ["today_actions", "alerts"])


def _workspace_v1_zone_order(role_code: str) -> List[str]:
    provider = _load_data_provider()
    if provider is not None:
        fn = getattr(provider, "build_v1_zone_order", None)
        if callable(fn):
            try:
                payload = fn()
                if isinstance(payload, dict) and payload:
                    order = payload.get(_to_text(role_code).lower())
                    if isinstance(order, list):
                        normalized = [_to_text(item) for item in order if _to_text(item)]
                        if normalized:
                            return normalized
            except Exception:
                pass

    default_order = {
        "pm": ["today_focus", "analysis", "quick_entries", "hero"],
        "finance": ["analysis", "today_focus", "quick_entries", "hero"],
        "owner": ["analysis", "today_focus", "hero", "quick_entries"],
    }
    return list(default_order.get(_to_text(role_code).lower(), default_order["owner"]))


def _workspace_v1_focus_map(role_code: str) -> List[str]:
    provider = _load_data_provider()
    if provider is not None:
        fn = getattr(provider, "build_v1_focus_map", None)
        if callable(fn):
            try:
                payload = fn()
                if isinstance(payload, dict) and payload:
                    ordered = payload.get(_to_text(role_code).lower())
                    if isinstance(ordered, list):
                        normalized = [_to_text(item) for item in ordered if _to_text(item)]
                        if normalized:
                            return normalized
            except Exception:
                pass

    defaults = {
        "pm": ["todo_list_today", "risk_alert_panel", "metric_row_core", "progress_summary_ops"],
        "finance": ["todo_list_today", "risk_alert_panel", "progress_summary_ops", "metric_row_core"],
        "owner": ["todo_list_today", "risk_alert_panel", "metric_row_core", "progress_summary_ops"],
    }
    return list(defaults.get(_to_text(role_code).lower(), defaults["owner"]))


def _workspace_v1_copy(defaults: Dict[str, str]) -> Dict[str, str]:
    return workspace_v1_copy(defaults, _load_data_provider())


def _impact_score(row: Dict[str, Any]) -> int:
    return impact_score(row)


def _urgency_score(
    row: Dict[str, Any],
    title: str,
    source_key: str,
    status_text: str,
    role_code: str = "",
    source_kind: str = "business",
    keyword_overrides: Dict[str, Any] | None = None,
) -> int:
    return urgency_score(
        row=row,
        title=title,
        source_key=source_key,
        status_text=status_text,
        role_code=role_code,
        source_kind=source_kind,
        keyword_overrides=keyword_overrides,
        ranking_profile_builder=_role_ranking_profile,
        provider_token_set_builder=lambda hook_name, defaults, overrides=None: _provider_token_set(
            hook_name,
            defaults,
            keyword_overrides=overrides,
        ),
        urgent_capability_checker=_is_urgent_capability,
        deadline_parser=_parse_deadline,
    )


def _to_business_action(
    source_key: str,
    row: Dict[str, Any],
    index: int,
    role_code: str = "",
    source_kind: str = "business",
    keyword_overrides: Dict[str, Any] | None = None,
) -> Dict[str, Any]:
    title = _to_text(row.get("title") or row.get("name") or row.get("label") or row.get("display_name"))
    if not title:
        title = f"待处理事项 {index + 1}"
    description = _to_text(row.get("description") or row.get("summary") or row.get("hint") or "进入场景继续处理业务")
    scene_key = _to_text(
        row.get("scene_key")
        or row.get("scene")
        or _route_scene_by_source(source_key, keyword_overrides=keyword_overrides)
    )
    route = _to_text(row.get("route")) or f"/s/{scene_key}"
    status_text = _to_text(row.get("status") or row.get("state") or row.get("level") or row.get("severity")).lower()
    urgent_keywords = _provider_token_set(
        "build_urgent_keywords",
        ("urgent", "high", "critical", "overdue", "严重", "紧急", "逾期", "高"),
        keyword_overrides=keyword_overrides,
    )
    is_urgent = any(word in status_text for word in urgent_keywords) or _is_urgent_capability(title, source_key)
    urgency_score = _urgency_score(
        row=row,
        title=title,
        source_key=source_key,
        status_text=status_text,
        role_code=role_code,
        source_kind=source_kind,
        keyword_overrides=keyword_overrides,
    )
    impact_score = _impact_score(row)
    return {
        "id": _to_text(row.get("id") or row.get("key") or f"{source_key}-{index + 1}"),
        "title": title,
        "description": description,
        "status": "urgent" if is_urgent else "normal",
        "tone": "danger" if is_urgent else "info",
        "progress": "pending",
        "count": _to_int(row.get("count") or row.get("pending_count") or 0),
        "ready": True,
        "entry_key": _to_text(row.get("entry_key") or row.get("key") or source_key),
        "scene_key": scene_key,
        "route": route,
        "menu_id": _to_int(row.get("menu_id")),
        "action_id": _to_int(row.get("action_id")),
        "source": source_kind,
        "source_detail": _to_text(row.get("source_detail")) or ("factual_record" if source_kind == "business" else "capability_template"),
        "urgency_score": urgency_score,
        "impact_score": impact_score,
    }


def _build_business_today_actions(
    data: Dict[str, Any],
    role_code: str = "",
    keyword_overrides: Dict[str, Any] | None = None,
) -> List[Dict[str, Any]]:
    collections = _extract_business_collections(data)
    candidates: List[Dict[str, Any]] = []
    preferred_sources = [
        "today_actions",
        "tasks",
        "project_actions",
        "task_items",
        "payment_requests",
        "risk_actions",
        "risk",
        "project_tasks",
    ]
    ordered_sources: List[str] = []
    for key in preferred_sources:
        if key in collections:
            ordered_sources.append(key)
    for key in collections:
        if key not in ordered_sources:
            ordered_sources.append(key)
    for source_key in ordered_sources:
        rows = collections.get(source_key, [])
        for idx, row in enumerate(rows[:6]):
            candidates.append(
                _to_business_action(
                    source_key,
                    row,
                    idx,
                    role_code=role_code,
                    source_kind="business",
                    keyword_overrides=keyword_overrides,
                )
            )
    candidates.sort(key=lambda item: (-_to_int(item.get("urgency_score")), 0 if item.get("status") == "urgent" else 1))
    dedup: List[Dict[str, Any]] = []
    seen: set = set()
    for item in candidates:
        marker = (_to_text(item.get("title")), _to_text(item.get("scene_key")))
        if marker in seen:
            continue
        seen.add(marker)
        dedup.append(item)
        if len(dedup) >= 6:
            break
    return dedup


def _build_capability_today_actions(ready_caps: Iterable[Dict[str, Any]], role_code: str = "") -> List[Dict[str, Any]]:
    provider = _load_data_provider()
    if provider is not None:
        fn = getattr(provider, "build_today_actions", None)
        if callable(fn):
            payload = fn(ready_caps)
            if isinstance(payload, list):
                normalized: List[Dict[str, Any]] = []
                for row in payload:
                    if not isinstance(row, dict):
                        continue
                    candidate = dict(row)
                    source_kind = _to_text(candidate.get("source"))
                    if source_kind not in {"business", "capability_fallback"}:
                        source_kind = "capability_fallback"
                        candidate["source"] = source_kind
                    title = _to_text(candidate.get("title") or candidate.get("name") or candidate.get("label"))
                    source_key = _to_text(candidate.get("entry_key") or candidate.get("id") or "today_actions")
                    status_text = _to_text(candidate.get("status") or candidate.get("state") or candidate.get("level") or candidate.get("severity"))
                    candidate["urgency_score"] = _urgency_score(
                        row=candidate,
                        title=title,
                        source_key=source_key,
                        status_text=status_text,
                        role_code=role_code,
                        source_kind=source_kind,
                    )
                    candidate["impact_score"] = _impact_score(candidate)
                    normalized.append(candidate)
                return normalized
    actions: List[Dict[str, Any]] = []
    for cap in list(ready_caps)[:6]:
        payload = cap.get("default_payload") if isinstance(cap.get("default_payload"), dict) else {}
        route = _to_text(payload.get("route"))
        scene_key = _scene_from_route(route)
        title = _to_text(cap.get("ui_label") or cap.get("name") or cap.get("key"))
        actions.append(
            {
                "id": _to_text(cap.get("key")) or title,
                "title": title or "进入能力",
                "description": _to_text(cap.get("ui_hint")) or "进入能力继续处理业务",
                "status": "urgent" if _is_urgent_capability(title, _to_text(cap.get("key"))) else "normal",
                "tone": "danger" if _is_urgent_capability(title, _to_text(cap.get("key"))) else "info",
                "progress": "pending",
                "count": 0,
                "ready": True,
                "entry_key": _to_text(cap.get("key")),
                "scene_key": scene_key,
                "route": route,
                "menu_id": _to_int(payload.get("menu_id")),
                "action_id": _to_int(payload.get("action_id")),
                "source": "capability_fallback",
                "urgency_score": _urgency_score(
                    row={"count": 0},
                    title=title,
                    source_key=_to_text(cap.get("key")),
                    status_text="urgent" if _is_urgent_capability(title, _to_text(cap.get("key"))) else "normal",
                    role_code=role_code,
                    source_kind="capability_fallback",
                ),
                "impact_score": 0,
            }
        )
    return actions


def _build_today_actions(
    data: Dict[str, Any],
    ready_caps: Iterable[Dict[str, Any]],
    role_code: str = "",
    keyword_overrides: Dict[str, Any] | None = None,
) -> List[Dict[str, Any]]:
    business_actions = _build_business_today_actions(
        data,
        role_code=role_code,
        keyword_overrides=keyword_overrides,
    )
    if len(business_actions) >= 4:
        return business_actions[:4]

    if business_actions:
        fallback_candidates = _build_capability_today_actions(ready_caps, role_code=role_code)
        fallback = [
            row for row in fallback_candidates
            if _to_text(row.get("source")) != "business"
        ]
        merged = list(business_actions)
        for item in fallback:
            marker = (
                _to_text(item.get("title")),
                _to_text(item.get("scene_key")),
                _to_text(item.get("entry_key")),
            )
            if any((
                _to_text(existing.get("title")),
                _to_text(existing.get("scene_key")),
                _to_text(existing.get("entry_key")),
            ) == marker for existing in merged):
                continue
            merged.append(item)
            if len(merged) >= 4:
                break
        return merged[:4]

    merged: List[Dict[str, Any]] = []
    seen: set = set()
    ordered = business_actions + _build_capability_today_actions(ready_caps, role_code=role_code)
    ordered.sort(key=lambda item: (-_to_int(item.get("urgency_score")), 0 if _to_text(item.get("source")) == "business" else 1))
    for item in ordered:
        marker = (
            _to_text(item.get("title")),
            _to_text(item.get("scene_key")),
            _to_text(item.get("entry_key")),
        )
        if marker in seen:
            continue
        seen.add(marker)
        merged.append(item)
        if len(merged) >= 4:
            break
    return merged


def _build_business_visibility_diagnosis(data: Dict[str, Any], role_code: str) -> Dict[str, Any]:
    collections = _extract_business_collections(data)
    collection_counts = {str(key): len(rows) for key, rows in collections.items()}
    total_rows = sum(collection_counts.values())
    expected = _workspace_expected_collections(role_code)
    missing_expected = [key for key in expected if _to_int(collection_counts.get(key)) <= 0]

    likely_cause = "healthy"
    gap_level = "healthy"
    if total_rows <= 0:
        likely_cause = "no_business_rows_detected"
        gap_level = "critical"
    elif missing_expected:
        likely_cause = "role_scope_or_demo_assignment_gap"
        gap_level = "limited"

    return {
        "role_code": role_code,
        "business_rows_total": total_rows,
        "collection_counts": collection_counts,
        "expected_collections": expected,
        "missing_expected": missing_expected,
        "gap_level": gap_level,
        "likely_cause": likely_cause,
    }


def _build_risk_actions(
    data: Dict[str, Any],
    locked_caps: Iterable[Dict[str, Any]],
    role_code: str = "",
    keyword_overrides: Dict[str, Any] | None = None,
) -> List[Dict[str, Any]]:
    collections = _extract_business_collections(data)
    preferred = ["risk_actions", "risk", "risk_events", "alerts", "today_actions"]
    actions: List[Dict[str, Any]] = []
    for source_key in preferred:
        rows = collections.get(source_key, [])
        for idx, row in enumerate(rows[:6]):
            action = _to_business_action(
                source_key,
                row,
                idx,
                role_code=role_code,
                source_kind="business",
                keyword_overrides=keyword_overrides,
            )
            if not _is_risk_semantic_action(
                source_key,
                row,
                action,
                keyword_overrides=keyword_overrides,
            ):
                continue
            action["scene_key"] = _workspace_scene("risk_center")
            action["route"] = f"/s/{action['scene_key']}"
            action["source"] = "business"
            action["status"] = "urgent"
            action["tone"] = "danger"
            actions.append(action)
    if actions:
        actions.sort(key=lambda item: -_to_int(item.get("urgency_score")))
        return actions[:3]

    provider = _load_data_provider()
    if provider is not None:
        signal_builder = getattr(provider, "build_today_actions", None)
        if callable(signal_builder):
            signal_payload = signal_builder(list(data.get("capabilities") or []))
            signal_actions: List[Dict[str, Any]] = []
            for idx, row in enumerate(signal_payload[:6] if isinstance(signal_payload, list) else []):
                if not isinstance(row, dict):
                    continue
                action = _to_business_action(
                    "today_actions",
                    row,
                    idx,
                    role_code=role_code,
                    source_kind="business",
                    keyword_overrides=keyword_overrides,
                )
                if not _is_risk_semantic_action(
                    "today_actions",
                    row,
                    action,
                    keyword_overrides=keyword_overrides,
                ):
                    continue
                action["scene_key"] = _workspace_scene("risk_center")
                action["route"] = f"/s/{action['scene_key']}"
                action["source"] = "business"
                action["source_detail"] = "semantic_template"
                action["status"] = "urgent"
                action["tone"] = "danger"
                signal_actions.append(action)
            if signal_actions:
                signal_actions.sort(key=lambda item: -_to_int(item.get("urgency_score")))
                deduped: List[Dict[str, Any]] = []
                seen: set = set()
                for item in signal_actions:
                    marker = (_to_text(item.get("title")), _to_text(item.get("entry_key")))
                    if marker in seen:
                        continue
                    seen.add(marker)
                    deduped.append(item)
                    if len(deduped) >= 3:
                        break
                if deduped:
                    return deduped

    fallback: List[Dict[str, Any]] = []
    for cap in list(locked_caps)[:2]:
        fallback.append(
            {
                "id": _to_text(cap.get("key")),
                "title": _to_text(cap.get("ui_label") or cap.get("name") or cap.get("key")) or "受限能力",
                "description": _to_text(cap.get("reason")) or "当前账号尚未开通该能力。",
                "entry_key": _to_text(cap.get("key")),
                "scene_key": _workspace_scene("risk_center"),
                "route": f"/s/{_workspace_scene('risk_center')}",
                "source": "capability_fallback",
                "source_detail": "capability_template",
                "urgency_score": _urgency_score(
                    row={"count": 1},
                    title=_to_text(cap.get("ui_label") or cap.get("name") or cap.get("key")) or "受限能力",
                    source_key=_to_text(cap.get("key")),
                    status_text="warning",
                    role_code=role_code,
                    source_kind="capability_fallback",
                ),
                "impact_score": 0,
            }
        )
    return fallback[:2]


def _build_extraction_stats(data: Dict[str, Any], today_actions: List[Dict[str, Any]], risk_actions: List[Dict[str, Any]]) -> Dict[str, Any]:
    collections = _extract_business_collections(data)
    total_rows = sum(len(rows) for rows in collections.values())
    today_business = len([row for row in today_actions if _to_text(row.get("source")) == "business"])
    risk_business = len([row for row in risk_actions if _to_text(row.get("source")) == "business"])
    today_factual = len([row for row in today_actions if _to_text(row.get("source")) == "business" and _to_text(row.get("source_detail")) == "factual_record"])
    risk_factual = len([row for row in risk_actions if _to_text(row.get("source")) == "business" and _to_text(row.get("source_detail")) == "factual_record"])
    today_total = len(today_actions)
    risk_total = len(risk_actions)
    today_rate = round((today_business / today_total) * 100, 2) if today_total else 0.0
    risk_rate = round((risk_business / risk_total) * 100, 2) if risk_total else 0.0
    today_factual_rate = round((today_factual / today_total) * 100, 2) if today_total else 0.0
    risk_factual_rate = round((risk_factual / risk_total) * 100, 2) if risk_total else 0.0
    source_kind = "business" if (today_business > 0 or risk_business > 0 or total_rows > 0) else "fallback"
    fallback_reason = "" if source_kind == "business" else "no_business_rows_detected"
    return {
        "business_collections": len(collections),
        "business_rows_total": total_rows,
        "today_actions_total": today_total,
        "today_actions_business": today_business,
        "today_actions_factual": today_factual,
        "today_actions_fallback": max(0, today_total - today_business),
        "today_actions_business_rate": today_rate,
        "today_actions_factual_rate": today_factual_rate,
        "risk_actions_total": risk_total,
        "risk_actions_business": risk_business,
        "risk_actions_factual": risk_factual,
        "risk_actions_fallback": max(0, risk_total - risk_business),
        "risk_actions_business_rate": risk_rate,
        "risk_actions_factual_rate": risk_factual_rate,
        "source_kind": source_kind,
        "fallback_reason": fallback_reason,
        "extraction_hit_rate": round((today_rate + risk_rate) / 2, 2),
        "factual_extraction_hit_rate": round((today_factual_rate + risk_factual_rate) / 2, 2),
    }


def _build_metric_sets(ready_count: int, locked_count: int, preview_count: int, scene_count: int, today_action_count: int, risk_action_count: int) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    business_metrics = [
        {
            "key": "biz.today_actions",
            "label": "今日待处理事项",
            "value": str(today_action_count),
            "level": _metric_level(today_action_count, 3, 6),
            "tone": _tone_from_level(_metric_level(today_action_count, 3, 6)),
            "progress": "pending" if today_action_count > 0 else "completed",
            "delta": "行动优先",
            "hint": "基于任务、待办、关键事项等动作聚合。",
        },
        {
            "key": "biz.risk_actions",
            "label": "高优先关键事项",
            "value": str(risk_action_count),
            "level": _metric_level(risk_action_count, 1, 3),
            "tone": _tone_from_level(_metric_level(risk_action_count, 1, 3)),
            "progress": "blocked" if risk_action_count > 0 else "running",
            "delta": "事项跟进",
            "hint": "需要优先处理的关键提醒与异常事项。",
        },
        {
            "key": "biz.project_scope",
            "label": "可用业务场景数",
            "value": str(scene_count),
            "level": _metric_level(scene_count, 3, 12),
            "tone": _tone_from_level(_metric_level(scene_count, 3, 12)),
            "progress": "running",
            "delta": "业务覆盖",
            "hint": "当前账号可直接进入的场景覆盖范围。",
        },
        {
            "key": "biz.execution_pressure",
            "label": "执行压力指数",
            "value": str(min(100, max(0, (today_action_count * 10) + (risk_action_count * 20)))),
            "level": _metric_level((today_action_count * 10) + (risk_action_count * 20), 30, 70),
            "tone": _tone_from_level(_metric_level((today_action_count * 10) + (risk_action_count * 20), 30, 70)),
            "progress": "running",
            "delta": "综合评估",
            "hint": "根据今日行动量与高优先事项计算的运行负载指标。",
        },
    ]
    platform_metrics = [
        {"key": "platform.ready_caps", "label": "可用能力", "value": str(ready_count)},
        {"key": "platform.locked_caps", "label": "受限能力", "value": str(locked_count)},
        {"key": "platform.preview_caps", "label": "预览能力", "value": str(preview_count)},
        {"key": "platform.scene_count", "label": "场景配置数", "value": str(scene_count)},
    ]
    return business_metrics, platform_metrics


def _build_interaction_contract() -> Dict[str, Any]:
    return {
        "scope": "workspace.home",
        "events": [
            {
                "event": "workspace.view",
                "intent": "telemetry.track",
                "stage": "home_enter",
                "blocking": False,
            },
            {
                "event": "workspace.enter_click",
                "intent": "telemetry.track",
                "stage": "scene_enter_click",
                "blocking": False,
            },
            {
                "event": "workspace.enter_result",
                "intent": "telemetry.track",
                "stage": "scene_enter_result",
                "blocking": False,
            },
            {
                "event": "workspace.risk_action_click",
                "intent": "telemetry.track",
                "stage": "risk_action",
                "blocking": False,
            },
        ],
        "core_intents": [
            "system.init",
            "ui.contract",
            "load_view",
            "api.data",
            "telemetry.track",
            "usage.track",
        ],
    }


def _tone_from_level(level: str) -> str:
    normalized = _to_text(level).lower()
    if normalized in {"red", "danger"}:
        return "danger"
    if normalized in {"amber", "warning"}:
        return "warning"
    if normalized in {"green", "success"}:
        return "success"
    return "neutral"


def _resolve_role_source_code(data: Dict[str, Any]) -> str:
    role_surface = data.get("role_surface") if isinstance(data.get("role_surface"), dict) else {}
    role_code = _to_text(role_surface.get("role_code")).lower()
    if role_code:
        return role_code
    return "owner"


def _normalize_role_code(data: Dict[str, Any]) -> str:
    role_code = _resolve_role_source_code(data)
    if role_code in {"pm", "finance", "owner"}:
        return role_code
    return "owner"


def _role_focus_config(role_code: str) -> Dict[str, Any]:
    provider = _load_data_provider()
    if provider is not None:
        fn = getattr(provider, "build_role_focus_config", None)
        if callable(fn):
            value = fn(role_code)
            if isinstance(value, dict) and value:
                return value
    if role_code == "pm":
        return {
            "zone_order": ["primary", "analysis", "support"],
            "focus_blocks": ["todo_core", "risk_core", "ops_progress", "record_overview"],
        }
    if role_code == "finance":
        return {
            "zone_order": ["analysis", "primary", "support"],
            "focus_blocks": ["ops_progress", "risk_core", "metrics_kpi", "record_overview"],
        }
    return {
        "zone_order": ["primary", "support", "analysis"],
        "focus_blocks": ["record_overview", "risk_core", "todo_core", "entry_grid"],
    }


def _v1_page_profile(role_code: str) -> Dict[str, Any]:
    provider = _load_data_provider()
    if provider is not None:
        fn = getattr(provider, "build_v1_page_profile", None)
        if callable(fn):
            value = fn(role_code)
            if isinstance(value, dict) and value:
                return value
    audience_map = {
        "pm": ["internal_user", "reviewer"],
        "finance": ["internal_user", "reviewer"],
        "owner": ["owner", "executive"],
    }
    audience = audience_map.get(role_code, ["owner"])
    priority_model = "task_first" if role_code == "pm" else "metric_first" if role_code == "finance" else "role_first"
    return {"audience": audience, "priority_model": priority_model, "mobile_priority": ["hero", "today_focus", "analysis"]}


def _v1_data_sources() -> Dict[str, Dict[str, Any]]:
    provider = _load_data_provider()
    if provider is not None:
        fn = getattr(provider, "build_v1_data_sources", None)
        if callable(fn):
            value = fn()
            if isinstance(value, dict) and value:
                return value
    return {
        "ds_hero": {"source_type": "computed", "provider": "workspace.hero", "section_keys": ["hero"]},
        "ds_metrics": {"source_type": "computed", "provider": "workspace.metrics.summary", "section_keys": ["metrics"]},
        "ds_today_todos": {"source_type": "computed", "provider": "workspace.todo.today", "section_keys": ["today_actions"]},
        "ds_risk_alerts": {"source_type": "computed", "provider": "workspace.risk.alerts", "section_keys": ["risk"]},
        "ds_ops_progress": {"source_type": "computed", "provider": "workspace.progress.summary", "section_keys": ["ops"]},
        "ds_scene_groups": {"source_type": "scene_context", "provider": "workspace.scene.groups", "section_keys": ["scene_groups"]},
        "ds_capability_groups": {
            "source_type": "capability_registry",
            "provider": "workspace.capability.groups",
            "section_keys": ["group_overview"],
        },
        "ds_advice": {"source_type": "computed", "provider": "workspace.advice", "section_keys": ["advice"]},
        "ds_filters": {"source_type": "static", "provider": "workspace.filters", "section_keys": ["filters"]},
    }


def _v1_state_schema() -> Dict[str, Any]:
    provider = _load_data_provider()
    if provider is not None:
        fn = getattr(provider, "build_v1_state_schema", None)
        if callable(fn):
            value = fn()
            if isinstance(value, dict) and value:
                return value
    return {
        "tones": {
            "success": {"icon": "check-circle"},
            "warning": {"icon": "alert-triangle"},
            "danger": {"icon": "x-circle"},
            "info": {"icon": "info"},
            "neutral": {"icon": "dot"},
        },
        "business_states": {
            "pending": {"tone": "warning", "label": "待处理"},
            "running": {"tone": "info", "label": "进行中"},
            "blocked": {"tone": "danger", "label": "已阻塞"},
            "completed": {"tone": "success", "label": "已完成"},
            "overdue": {"tone": "danger", "label": "已逾期"},
        },
    }


def _v1_action_schema(role_code: str) -> Dict[str, Any]:
    specs: Dict[str, Dict[str, str]] = {
        "open_landing": {"label": "打开默认入口", "intent": "ui.contract"},
        "open_my_work": {"label": "查看全部", "intent": "ui.contract"},
        "open_risk_dashboard": {"label": "进入重点事项", "intent": "ui.contract"},
        "open_scene": {"label": "进入场景", "intent": "ui.contract"},
        "refresh": {"label": "刷新", "intent": "api.data"},
    }
    provider = _load_data_provider()
    if provider is not None:
        fn = getattr(provider, "build_v1_action_specs", None)
        if callable(fn):
            value = fn()
            if isinstance(value, dict) and value:
                specs = value

    actions: Dict[str, Any] = {}
    for key, spec in specs.items():
        if not isinstance(spec, dict):
            continue
        action_key = _to_text(key)
        if not action_key:
            continue
        label = _to_text(spec.get("label")) or action_key
        intent = _to_text(spec.get("intent")) or "ui.contract"
        actions[action_key] = {
            "label": label,
            "intent": intent,
            "target": _shared_action_target(action_key, "workspace.home"),
            "visibility": {"roles": [role_code], "capabilities": [], "expr": None},
        }
    return {"actions": actions}


def _build_page_orchestration(role_code: str, role_source_code: str | None = None) -> Dict[str, Any]:
    source_role_code = _to_text(role_source_code).lower() or role_code
    role_cfg = _role_focus_config(role_code)
    zone_order = role_cfg.get("zone_order") if isinstance(role_cfg.get("zone_order"), list) else []
    zone_rank = {str(key): idx + 1 for idx, key in enumerate(zone_order)}
    zones = [
        {"key": "primary", "label": "主行动区", "order": zone_rank.get("primary", 1)},
        {"key": "analysis", "label": "分析监控区", "order": zone_rank.get("analysis", 2)},
        {"key": "support", "label": "辅助入口区", "order": zone_rank.get("support", 3)},
    ]
    blocks = []
    provider = _load_data_provider()
    if provider is not None:
        zones_fn = getattr(provider, "build_legacy_zones", None)
        if callable(zones_fn):
            payload = zones_fn(role_code, zone_rank)
            if isinstance(payload, list) and payload:
                zones = payload
        blocks_fn = getattr(provider, "build_legacy_blocks", None)
        if callable(blocks_fn):
            payload = blocks_fn(role_code)
            if isinstance(payload, list) and payload:
                blocks = payload
    if not blocks:
        blocks = [
            {
                "key": "record_overview",
                "type": "record_summary",
                "zone": "primary",
                "order": 1,
                "source_path": "hero",
                "visible": True,
                "tone": "info",
                "progress": "running",
            },
            {
                "key": "metrics_hero",
                "type": "hero_metric",
                "zone": "analysis",
                "order": 2,
                "source_path": "metrics",
                "visible": True,
                "tone": "neutral",
                "progress": "running",
            },
            {
                "key": "metrics_kpi",
                "type": "metric_row",
                "zone": "analysis",
                "order": 3,
                "source_path": "metrics",
                "visible": True,
                "tone": "info",
                "progress": "running",
            },
            {
                "key": "todo_core",
                "type": "todo_list",
                "zone": "primary",
                "order": 4,
                "source_path": "today_actions",
                "visible": True,
                "tone": "warning",
                "progress": "pending",
            },
            {
                "key": "risk_core",
                "type": "alert_panel",
                "zone": "primary",
                "order": 5,
                "source_path": "risk",
                "visible": True,
                "tone": "danger",
                "progress": "blocked",
            },
            {
                "key": "ops_progress",
                "type": "progress_summary",
                "zone": "analysis",
                "order": 6,
                "source_path": "ops",
                "visible": True,
                "tone": "info",
                "progress": "running",
            },
            {
                "key": "entry_grid",
                "type": "entry_grid",
                "zone": "support",
                "order": 7,
                "source_path": "scene_groups",
                "visible": True,
                "tone": "neutral",
                "progress": "completed",
            },
            {
                "key": "group_grid",
                "type": "entry_grid",
                "zone": "support",
                "order": 8,
                "source_path": "group_overview",
                "visible": True,
                "tone": "neutral",
                "progress": "completed",
            },
            {
                "key": "advice_fold",
                "type": "accordion_group",
                "zone": "support",
                "order": 9,
                "source_path": "advice",
                "visible": True,
                "tone": "warning",
                "progress": "pending",
            },
            {
                "key": "filters_fold",
                "type": "accordion_group",
                "zone": "support",
                "order": 10,
                "source_path": "filters",
                "visible": role_code != "owner",
                "tone": "neutral",
                "progress": "completed",
            },
            {
                "key": "activity_stream",
                "type": "activity_feed",
                "zone": "analysis",
                "order": 11,
                "source_path": "risk.actions",
                "visible": True,
                "tone": "info",
                "progress": "running",
            },
        ]
    focus_blocks = [str(key) for key in role_cfg.get("focus_blocks", []) if _to_text(key)]
    focus_rank = {key: idx + 1 for idx, key in enumerate(focus_blocks)}

    for block in blocks:
        key = _to_text(block.get("key"))
        if key in focus_rank:
            block["order"] = focus_rank[key]
            block["focus"] = True
        else:
            block["order"] = int(block.get("order", 100)) + 20
            block["focus"] = False

    blocks = sorted(blocks, key=lambda item: (int(item.get("order", 999)), _to_text(item.get("key"))))
    return {
        "schema_version": "v1",
        "page": {
            "key": "workspace.home",
            "intent": "owner.dashboard.open",
            "role_code": source_role_code,
            "render_mode": "governed",
        },
        "zones": zones,
        "blocks": blocks,
        "role_layout": {
            "mode": "heterogeneous_same_page",
            "variant": role_code,
            "focus_blocks": focus_blocks,
        },
    }


def _build_page_orchestration_v1(role_code: str, role_source_code: str | None = None) -> Dict[str, Any]:
    source_role_code = _to_text(role_source_code).lower() or role_code
    role_cfg = _role_focus_config(role_code)
    zone_order = role_cfg.get("zone_order") if isinstance(role_cfg.get("zone_order"), list) else []
    zone_rank = {str(key): idx + 1 for idx, key in enumerate(zone_order)}
    profile = _v1_page_profile(role_code)
    audience = profile.get("audience") if isinstance(profile.get("audience"), list) and profile.get("audience") else ["owner"]
    priority_model = _to_text(profile.get("priority_model")) or (
        "task_first" if role_code == "pm" else "metric_first" if role_code == "finance" else "role_first"
    )
    v1_copy = _workspace_v1_copy(
        {
            "zone.hero.title": "核心关注",
            "zone.hero.description": "角色上下文与默认入口。",
            "zone.today_focus.title": "今日优先事项",
            "zone.today_focus.description": "先处理行动项，再快速处置风险提醒。",
            "zone.analysis.title": "项目总体状态",
            "zone.analysis.description": "关键指标、执行进展与风险动态。",
            "zone.quick_entries.title": "常用功能",
            "zone.quick_entries.description": "按业务场景快速进入处理。",
            "block.hero_record_summary.title": "角色与入口摘要",
            "block.todo_list_today.title": "今日行动",
            "block.risk_alert_panel.title": "系统提醒（高优先）",
            "block.advice_fold.title": "系统建议（补充）",
            "block.metric_row_core.title": "关键指标",
            "block.progress_summary_ops.title": "综合进展",
            "block.activity_feed_risk.title": "风险动态",
            "block.entry_grid_scene.title": "常用功能",
            "action.open_landing.label": "打开默认入口",
            "action.open_my_work.label": "查看全部",
            "action.open_risk_dashboard.label": "进入风险驾驶舱",
            "action.open_scene.label": "进入场景",
            "page.title": "工作台",
            "page.subtitle": "先处理行动项，再关注风险与总体状态",
            "page.badge.runtime_ok": "运行正常",
            "page.action.refresh": "刷新",
        }
    )
    mobile_priority = profile.get("mobile_priority") if isinstance(profile.get("mobile_priority"), list) and profile.get("mobile_priority") else ["hero", "today_focus", "analysis"]

    zones: List[Dict[str, Any]] = []
    provider = _load_data_provider()
    if provider is not None:
        fn = getattr(provider, "build_v1_zones", None)
        if callable(fn):
            payload = fn(role_code, audience, zone_rank)
            if isinstance(payload, list) and payload:
                zones = payload

    if not zones:
        zones = [
        {
            "key": "hero",
            "title": v1_copy.get("zone.hero.title") or "核心关注",
            "description": v1_copy.get("zone.hero.description") or "角色上下文与默认入口。",
            "zone_type": "hero",
            "display_mode": "stack",
            "priority": 40,
            "visibility": {"roles": audience, "capabilities": [], "expr": None},
            "blocks": [
                {
                    "key": "hero_record_summary",
                    "block_type": "record_summary",
                    "title": v1_copy.get("block.hero_record_summary.title") or "角色与入口摘要",
                    "priority": 100,
                    "importance": "critical",
                    "tone": "info",
                    "progress": "running",
                    "section_key": "hero",
                    "data_source": "ds_hero",
                    "loading_strategy": "eager",
                    "refreshable": True,
                    "collapsible": False,
                    "visibility": {"roles": audience, "capabilities": [], "expr": None},
                    "actions": [{"key": "open_landing", "label": v1_copy.get("action.open_landing.label") or "打开默认入口", "intent": "ui.contract"}],
                    "payload": {"style_variant": "default"},
                }
            ],
        },
        {
            "key": "today_focus",
            "title": v1_copy.get("zone.today_focus.title") or "今日优先事项",
            "description": v1_copy.get("zone.today_focus.description") or "先处理行动项，再快速处置风险提醒。",
            "zone_type": "primary",
            "display_mode": "grid",
            "priority": 100,
            "visibility": {"roles": audience, "capabilities": [], "expr": None},
            "blocks": [
                {
                    "key": "todo_list_today",
                    "block_type": "todo_list",
                    "title": v1_copy.get("block.todo_list_today.title") or "今日行动",
                    "priority": 98,
                    "importance": "critical",
                    "tone": "warning",
                    "progress": "pending",
                    "section_key": "today_actions",
                    "data_source": "ds_today_todos",
                    "loading_strategy": "eager",
                    "refreshable": True,
                    "collapsible": False,
                    "visibility": {"roles": audience, "capabilities": [], "expr": None},
                    "actions": [{"key": "open_my_work", "label": v1_copy.get("action.open_my_work.label") or "查看全部", "intent": "ui.contract"}],
                    "payload": {"item_layout": "card", "max_items": 4},
                },
                {
                    "key": "risk_alert_panel",
                    "block_type": "alert_panel",
                    "title": v1_copy.get("block.risk_alert_panel.title") or "系统提醒（高优先）",
                    "priority": 97,
                    "importance": "critical",
                    "tone": "danger",
                    "progress": "blocked",
                    "section_key": "risk",
                    "data_source": "ds_risk_alerts",
                    "loading_strategy": "eager",
                    "refreshable": True,
                    "collapsible": False,
                    "visibility": {"roles": audience, "capabilities": [], "expr": None},
                    "actions": [{"key": "open_risk_dashboard", "label": v1_copy.get("action.open_risk_dashboard.label") or "进入风险驾驶舱", "intent": "ui.contract"}],
                    "payload": {"group_by": "alert_level", "show_counts": True, "max_items": 3},
                },
                {
                    "key": "advice_fold",
                    "block_type": "accordion_group",
                    "title": v1_copy.get("block.advice_fold.title") or "系统建议（补充）",
                    "priority": 40,
                    "importance": "low",
                    "tone": "warning",
                    "progress": "pending",
                    "section_key": "advice",
                    "data_source": "ds_advice",
                    "loading_strategy": "lazy",
                    "refreshable": True,
                    "collapsible": True,
                    "visibility": {"roles": audience, "capabilities": [], "expr": None},
                    "actions": [],
                    "payload": {"mode": "accordion"},
                },
            ],
        },
        {
            "key": "analysis",
            "title": v1_copy.get("zone.analysis.title") or "项目总体状态",
            "description": v1_copy.get("zone.analysis.description") or "关键指标、执行进展与风险动态。",
            "zone_type": "secondary",
            "display_mode": "grid",
            "priority": 80,
            "visibility": {"roles": audience, "capabilities": [], "expr": None},
            "blocks": [
                {
                    "key": "metric_row_core",
                    "block_type": "metric_row",
                    "title": v1_copy.get("block.metric_row_core.title") or "关键指标",
                    "priority": 80,
                    "importance": "medium",
                    "tone": "neutral",
                    "progress": "running",
                    "section_key": "metrics",
                    "data_source": "ds_metrics",
                    "loading_strategy": "eager",
                    "refreshable": True,
                    "collapsible": False,
                    "visibility": {"roles": audience, "capabilities": [], "expr": None},
                    "actions": [],
                    "payload": {"show_trend": True},
                },
                {
                    "key": "progress_summary_ops",
                    "block_type": "progress_summary",
                    "title": v1_copy.get("block.progress_summary_ops.title") or "综合进展",
                    "priority": 70,
                    "importance": "medium",
                    "tone": "info",
                    "progress": "running",
                    "section_key": "ops",
                    "data_source": "ds_ops_progress",
                    "loading_strategy": "lazy",
                    "refreshable": True,
                    "collapsible": True,
                    "visibility": {"roles": audience, "capabilities": [], "expr": None},
                    "actions": [],
                    "payload": {"show_percentage": True},
                },
                {
                    "key": "activity_feed_risk",
                    "block_type": "activity_feed",
                    "title": v1_copy.get("block.activity_feed_risk.title") or "风险动态",
                    "priority": 60,
                    "importance": "medium",
                    "tone": "info",
                    "progress": "running",
                    "section_key": "risk",
                    "data_source": "ds_risk_alerts",
                    "loading_strategy": "lazy",
                    "refreshable": True,
                    "collapsible": False,
                    "visibility": {"roles": audience, "capabilities": [], "expr": None},
                    "actions": [],
                    "payload": {"stream": "risk.actions"},
                },
            ],
        },
        {
            "key": "quick_entries",
            "title": v1_copy.get("zone.quick_entries.title") or "常用功能",
            "description": v1_copy.get("zone.quick_entries.description") or "按业务场景快速进入处理。",
            "zone_type": "supporting",
            "display_mode": "grid",
            "priority": 60,
            "visibility": {"roles": audience, "capabilities": [], "expr": None},
            "blocks": [
                {
                    "key": "entry_grid_scene",
                    "block_type": "entry_grid",
                    "title": v1_copy.get("block.entry_grid_scene.title") or "常用功能",
                    "priority": 65,
                    "importance": "medium",
                    "tone": "neutral",
                    "progress": "completed",
                    "section_key": "scene_groups",
                    "data_source": "ds_scene_groups",
                    "loading_strategy": "lazy",
                    "refreshable": True,
                    "collapsible": False,
                    "visibility": {"roles": audience, "capabilities": [], "expr": None},
                    "actions": [{"key": "open_scene", "label": v1_copy.get("action.open_scene.label") or "进入场景", "intent": "ui.contract"}],
                    "payload": {"layout": "2x4", "show_icon": True, "show_hint": True},
                },
            ],
        },
        ]

        for zone in zones:
            if _to_text(zone.get("key")) != "today_focus":
                continue
            blocks = zone.get("blocks") if isinstance(zone.get("blocks"), list) else []
            zone["blocks"] = [
                block for block in blocks
                if _to_text((block or {}).get("key")) != "advice_fold"
            ]
            break
    preferred_order = _workspace_v1_zone_order(role_code)
    effective_order = preferred_order
    priority_map = {key: 100 - (idx * 10) for idx, key in enumerate(effective_order)}
    for zone in zones:
        zone_key = _to_text(zone.get("key"))
        if zone_key in priority_map:
            zone["priority"] = priority_map[zone_key]

    focus_blocks = {str(key): idx + 1 for idx, key in enumerate(_workspace_v1_focus_map(role_code))}
    for zone in zones:
        blocks = zone.get("blocks") if isinstance(zone.get("blocks"), list) else []
        for block in blocks:
            key = _to_text(block.get("key"))
            if key in focus_blocks:
                block["priority"] = 100 + (len(focus_blocks) - focus_blocks[key])
                block["focus"] = True
            else:
                block["focus"] = False

    return {
        "contract_version": "page_orchestration_v1",
        "scene_key": _workspace_scene("dashboard"),
        "page": {
            "key": "workspace.home",
            "title": v1_copy.get("page.title") or "工作台",
            "subtitle": v1_copy.get("page.subtitle") or "先处理行动项，再关注风险与总体状态",
            "page_type": "workspace",
            "intent": "ui.contract",
            "scene_key": _workspace_scene("dashboard"),
            "layout_mode": "dashboard",
            "audience": audience,
            "priority_model": priority_model,
            "status": "ready",
            "breadcrumbs": [],
            "header": {"badges": [{"label": v1_copy.get("page.badge.runtime_ok") or "运行正常", "tone": "success"}]},
            "global_actions": [{"key": "refresh", "label": v1_copy.get("page.action.refresh") or "刷新", "intent": "api.data"}],
            "filters": [],
            "context": {"role_code": source_role_code},
        },
        "zones": zones,
        "data_sources": _v1_data_sources(),
        "state_schema": _v1_state_schema(),
        "action_schema": _v1_action_schema(role_code),
        "render_hints": {
            "dense_mode": False,
            "preferred_columns": 4,
            "mobile_priority": mobile_priority,
            "sticky_header": True,
        },
        "meta": {
            "generated_by": "smart_core.workspace_home_contract_builder",
            "schema_version": "1.0.0",
            "role_variant": role_code,
            "role_source_code": source_role_code,
        },
    }


def _build_advice_items(locked_caps: Iterable[Dict[str, Any]]) -> List[Dict[str, Any]]:
    provider = _load_data_provider()
    if provider is not None:
        fn = getattr(provider, "build_advice_items", None)
        if callable(fn):
            return fn(locked_caps)
    result: List[Dict[str, Any]] = []
    for cap in list(locked_caps)[:3]:
        reason = _to_text(cap.get("reason")) or "当前账号尚未开通该能力。"
        result.append(
            {
                "id": _to_text(cap.get("key")),
                "level": "amber",
                "tone": "warning",
                "progress": "blocked",
                "title": _to_text(cap.get("ui_label") or cap.get("name") or cap.get("key")) or "能力待开通",
                "description": reason,
                "action_label": "联系管理员开通",
            }
        )
    if result:
        return result
    return [
        {
            "id": "stable",
            "level": "green",
            "tone": "success",
            "progress": "completed",
            "title": "当前整体运行稳定",
            "description": "能力面运行正常，建议优先处理今日关键动作。",
            "action_label": "",
        }
    ]


def build_workspace_home_contract(data: Dict[str, Any]) -> Dict[str, Any]:
    capabilities = data.get("capabilities") if isinstance(data.get("capabilities"), list) else []
    scenes = data.get("scenes") if isinstance(data.get("scenes"), list) else []

    normalized_caps = [cap for cap in capabilities if isinstance(cap, dict)]
    total_caps = len(normalized_caps)
    ready_caps = [cap for cap in normalized_caps if _capability_state(cap) == "READY"]
    locked_caps = [cap for cap in normalized_caps if _capability_state(cap) == "LOCKED"]
    preview_caps = [cap for cap in normalized_caps if _capability_state(cap) == "PREVIEW"]
    reason_counter = Counter(_to_text(cap.get("reason_code")).upper() or "UNKNOWN" for cap in locked_caps)

    locked_count = len(locked_caps)
    preview_count = len(preview_caps)
    ready_count = len(ready_caps)
    scene_count = len([scene for scene in scenes if isinstance(scene, dict)])
    risk_red = min(locked_count, max(0, round(locked_count * 0.5)))
    risk_amber = max(0, locked_count - risk_red + min(preview_count, 2))
    risk_green = max(0, ready_count - risk_red - risk_amber)
    risk_now = locked_count + preview_count
    risk_d7 = max(0, round(risk_now * 0.85))
    risk_d30 = max(0, round(risk_now * 0.7))
    risk_max = max(risk_now, risk_d7, risk_d30, 1)

    permission_denied = reason_counter.get("PERMISSION_DENIED", 0)
    missing_scope = reason_counter.get("CAPABILITY_SCOPE_MISSING", 0)
    feature_disabled = reason_counter.get("FEATURE_DISABLED", 0)

    now = fields.Datetime.now()
    updated_at = now.strftime("%H:%M") if now else "--:--"

    if permission_denied > 0:
        partial_notice = "部分能力因权限受限未开放"
    elif locked_count > 0:
        partial_notice = "部分能力暂不可用"
    else:
        partial_notice = ""
    role_source_code = _resolve_role_source_code(data)
    role_code = _normalize_role_code(data)
    keyword_overrides = _resolve_workspace_keyword_overrides(data)
    today_actions = _build_today_actions(
        data,
        ready_caps,
        role_code=role_code,
        keyword_overrides=keyword_overrides,
    )
    risk_actions = _build_risk_actions(
        data,
        locked_caps,
        role_code=role_code,
        keyword_overrides=keyword_overrides,
    )
    today_business_count = len([row for row in today_actions if _to_text(row.get("source")) == "business"])
    risk_business_count = len([row for row in risk_actions if _to_text(row.get("source")) == "business"])
    urgent_risk_count = len([row for row in risk_actions if _to_text(row.get("status")) == "urgent"])
    risk_red = max(risk_red, urgent_risk_count)
    risk_now = max(risk_now, len(risk_actions))
    risk_max = max(risk_now, risk_d7, risk_d30, 1)
    business_metrics, platform_metrics = _build_metric_sets(
        ready_count=ready_count,
        locked_count=locked_count,
        preview_count=preview_count,
        scene_count=scene_count,
        today_action_count=today_business_count,
        risk_action_count=risk_business_count,
    )
    extraction_stats = _build_extraction_stats(data=data, today_actions=today_actions, risk_actions=risk_actions)
    visibility_diagnosis = _build_business_visibility_diagnosis(data, role_code)
    has_business_signal = bool(
        _to_int(extraction_stats.get("business_rows_total")) > 0
        or _to_int(extraction_stats.get("today_actions_business")) > 0
        or _to_int(extraction_stats.get("risk_actions_business")) > 0
    )
    scene_contract_core: Dict[str, Any] = {
        "scene": {"key": "workspace.home", "page": "workspace.home"},
        "page": {"key": "workspace.home", "title": "工作台", "route": "/"},
        "nav_ref": {
            "active_scene_key": _workspace_scene("dashboard"),
            "active_menu_key": f"scene:{_workspace_scene('dashboard')}",
            "active_menu_id": None,
        },
        "zones": {},
        "record": {"hero": {"title": "工作台", "role_code": role_source_code}},
        "permissions": {},
        "actions": {},
        "extensions": {},
        "diagnostics": {},
    }
    scene_engine_meta: Dict[str, Any] = {}
    scene_engine = _load_scene_engine_module()
    engine_fn = getattr(scene_engine, "build_scene_contract_from_specs", None) if scene_engine else None
    if callable(engine_fn):
        try:
            orchestration_v1 = _build_page_orchestration_v1(role_code, role_source_code=role_source_code)
            zones_payload = orchestration_v1.get("zones") if isinstance(orchestration_v1, dict) else []
            zone_specs = []
            built_zones = {}
            for row in zones_payload if isinstance(zones_payload, list) else []:
                if not isinstance(row, dict):
                    continue
                zone_key = _to_text(row.get("key"))
                if not zone_key:
                    continue
                block_keys = []
                for block in row.get("blocks") if isinstance(row.get("blocks"), list) else []:
                    if not isinstance(block, dict):
                        continue
                    block_key = _to_text(block.get("key"))
                    if block_key:
                        block_keys.append(block_key)
                zone_specs.append(
                    {
                        "key": zone_key,
                        "title": _to_text(row.get("title")),
                        "zone_type": _to_text(row.get("zone_type")),
                        "display_mode": _to_text(row.get("display_mode")),
                        "block_key": block_keys[0] if block_keys else "",
                    }
                )
                built_zones[zone_key] = {
                    "zone_key": zone_key,
                    "title": _to_text(row.get("title")),
                    "zone_type": _to_text(row.get("zone_type")),
                    "display_mode": _to_text(row.get("display_mode")),
                    "blocks": list(row.get("blocks") or []),
                }
            contract = engine_fn(
                scene_hint={"key": "workspace.home", "page": "workspace.home"},
                page_hint={"key": "workspace.home", "title": "工作台", "route": "/"},
                zone_specs=zone_specs,
                built_zones=built_zones,
                record={"hero": {"title": "工作台"}},
                diagnostics={"source": "workspace_home_contract_builder"},
            )
            if isinstance(contract, dict) and contract:
                scene_contract_core = {
                    "scene": dict(contract.get("scene") or scene_contract_core.get("scene") or {}),
                    "page": dict(contract.get("page") or scene_contract_core.get("page") or {}),
                    "nav_ref": dict(contract.get("nav_ref") or scene_contract_core.get("nav_ref") or {}),
                    "zones": dict(contract.get("zones") or scene_contract_core.get("zones") or {}),
                    "record": dict(contract.get("record") or scene_contract_core.get("record") or {}),
                    "permissions": dict(contract.get("permissions") or {}),
                    "actions": dict(contract.get("actions") or {}),
                    "extensions": dict(contract.get("extensions") or {}),
                    "diagnostics": dict(contract.get("diagnostics") or {}),
                }
            scene_engine_meta = {
                "enabled": True,
                "mode": "primary_scene_contract",
                "shape_ok": bool(((contract.get("diagnostics") or {}).get("scene_contract_shape") or {}).get("ok")),
            }
        except Exception as exc:
            scene_engine_meta = {"enabled": False, "error": _to_text(exc)}
    hero_payload = _workspace_hero_payload(
        has_business_signal=has_business_signal,
        gap_level=_to_text(visibility_diagnosis.get("gap_level")),
        updated_at=updated_at,
        partial_notice=partial_notice,
    )
    risk_summary_text = _workspace_risk_summary_text(risk_red)
    risk_payload = _workspace_risk_payload(
        summary=risk_summary_text,
        risk_red=risk_red,
        risk_amber=risk_amber,
        risk_green=risk_green,
        risk_d30=risk_d30,
        risk_d7=risk_d7,
        risk_now=risk_now,
        risk_max=risk_max,
        risk_actions=risk_actions,
        permission_denied=permission_denied,
    )
    ops_payload = _workspace_ops_payload(
        has_business_signal=has_business_signal,
        risk_business_count=risk_business_count,
        today_business_count=today_business_count,
    )
    ops_meta = _workspace_ops_meta(has_business_signal=has_business_signal)
    return {
        "scene": scene_contract_core.get("scene") or {},
        "page": scene_contract_core.get("page") or {},
        "nav_ref": scene_contract_core.get("nav_ref") or {},
        "zones": scene_contract_core.get("zones") or {},
        "record": scene_contract_core.get("record") or {},
        "permissions": scene_contract_core.get("permissions") or {},
        "actions": scene_contract_core.get("actions") or {},
        "extensions": scene_contract_core.get("extensions") or {},
        "schema_version": "v1",
        "semantic_protocol": {
            "block_types": list(BLOCK_TYPES),
            "state_tones": list(STATE_TONES),
            "progress_states": list(PROGRESS_STATES),
        },
        "layout": {
            "sections": [
                {"key": "hero", "enabled": True, "tag": "header"},
                {"key": "today_actions", "enabled": True, "tag": "section"},
                {"key": "risk", "enabled": True, "tag": "section"},
                {"key": "metrics", "enabled": True, "tag": "section"},
                {"key": "ops", "enabled": True, "tag": "details", "open": False},
                {"key": "group_overview", "enabled": True, "tag": "section"},
                {"key": "advice", "enabled": True, "tag": "details", "open": False},
                {"key": "filters", "enabled": False, "tag": "section"},
                {"key": "scene_groups", "enabled": False, "tag": "div"},
            ],
            "texts": _workspace_layout_texts({
                "hero.role_label": "当前角色",
                "hero.landing_label": "默认入口",
                "hero.open_landing_action": "打开默认入口",
                "hero.open_my_work_action": "我的工作",
                "hero.open_usage_action": "使用分析",
                "hero.view_mode_card": "卡片",
                "hero.view_mode_list": "列表",
                "hero.updated_at_label": "数据更新时间",
                "hero.runtime_ok": "状态正常",
                "hero.steady_notice": "当前运行平稳",
                "metrics.aria_label": "核心价值区",
                "today_actions.aria_label": "今日行动",
                "today_actions.title": "今日行动",
                "today_actions.subtitle": "先处理高优先事项，再进入对应场景。",
                "today_actions.count_prefix": "待处理",
                "today_actions.coming_soon_action": "即将开放",
                "risk.aria_label": "关键事项区",
                "risk.title": "关键事项",
                "risk.subtitle": "快速识别当前重点事项。",
                "risk.bucket.red": "高优先 ⚠",
                "risk.bucket.amber": "处理中 ⏳",
                "risk.bucket.green": "正常 ✓",
                "risk.trend_title": "事项趋势（7/30 天）",
                "risk.sources_title": "事项来源分布",
                "risk.actions_title": "事项待处理清单",
                "risk.actions.detail": "看详情",
                "risk.actions.assign": "分派",
                "risk.actions.close": "关闭",
                "risk.actions.approve": "提交处理",
                "ops.title": "运行总体状态",
                "ops.aria_label": "运行总体状态区",
                "ops.compare.title": "关键指标对比",
                "ops.compare.contract": "指标 A",
                "ops.compare.output": "指标 B",
                "ops.kpi.cost_rate": "效率指标",
                "ops.kpi.payment_rate": "完成指标",
                "ops.kpi.output_trend": "趋势指标",
                "ops.kpi.output_note": "基于当前可见运行数据",
                "advice.title": "系统提醒",
                "advice.aria_label": "系统提醒",
                "group_overview.title": "常用功能",
                "group_overview.subtitle": "按分组快速进入核心功能。",
                "group_overview.capability_count_prefix": "功能数",
                "group_overview.allow_prefix": "可用",
                "group_overview.readonly_prefix": "只读",
                "group_overview.deny_prefix": "禁用",
            }),
            "actions": _workspace_layout_actions({
                "todo_default": "查看详情",
                "todo_approval": "处理待办事项",
                "todo_contract": "查看异常事项",
                "todo_risk": "处理关键事项",
                "todo_change": "确认变更事项",
                "todo_overdue": "处理逾期任务",
            }),
        },
        "hero": hero_payload,
        "metrics": business_metrics,
        "platform_metrics": platform_metrics,
        "today_actions": today_actions,
        "risk": {
            "summary": _to_text(risk_payload.get("summary")),
            "buckets": dict(risk_payload.get("buckets") or {}),
            "tone": _to_text(risk_payload.get("tone")) or "info",
            "progress": _to_text(risk_payload.get("progress")) or "running",
            "trend": list(risk_payload.get("trend") or []),
            "sources": list(risk_payload.get("sources") or []),
            "actions": list(risk_payload.get("actions") or []),
        },
        "ops": {
            "bars": ops_payload.get("bars") or {},
            "kpi": ops_payload.get("kpi") or {},
            "tone": _to_text(ops_meta.get("tone")) or "info",
            "progress": _to_text(ops_meta.get("progress")) or "running",
            "data_state": _to_text(ops_meta.get("data_state")) or "fallback",
        },
        "blocks": [
            {
                "type": "hero",
                "key": "workspace.hero",
                "data": {
                    "hero": {
                        "title": hero_payload.get("title") or "工作台",
                        "updated_at": hero_payload.get("updated_at") or updated_at,
                        "status_notice": hero_payload.get("status_notice") or partial_notice,
                    },
                },
                "actions": [
                    {"intent": "ui.contract", "payload": {"scene_key": _workspace_scene("dashboard")}},
                ],
            },
            {
                "type": "metric",
                "key": "workspace.metrics",
                "data": {
                    "metrics": business_metrics,
                    "platform_metrics": platform_metrics,
                },
                "actions": [
                    {"intent": "ui.contract", "payload": {"scene_key": _workspace_scene("operation_overview")}},
                ],
            },
            {
                "type": "risk",
                "key": "workspace.risk",
                "data": {
                    "summary": _to_text(risk_payload.get("summary")),
                    "buckets": dict(risk_payload.get("buckets") or {}),
                    "actions": list(risk_payload.get("actions") or []),
                },
                "actions": [
                    {"intent": "ui.contract", "payload": {"scene_key": _workspace_scene("risk_center")}},
                ],
            },
            {
                "type": "ops",
                "key": "workspace.ops",
                "data": {
                    "bars": ops_payload.get("bars") or {},
                    "kpi": {
                        "cost_rate": _to_int((ops_payload.get("kpi") or {}).get("cost_rate")),
                        "payment_rate": _to_int((ops_payload.get("kpi") or {}).get("payment_rate")),
                    },
                },
                "actions": [
                    {"intent": "ui.contract", "payload": {"scene_key": _workspace_scene("execution")}},
                ],
            },
        ],
        "advice": _build_advice_items(locked_caps),
        "contract_protocol": {
            "primary": "page_orchestration_v1",
            "legacy": {"key": "page_orchestration", "status": "compatibility"},
        },
        "interaction_contract": _build_interaction_contract(),
        "page_orchestration_v1": _build_page_orchestration_v1(role_code, role_source_code=role_source_code),
        "page_orchestration": _build_page_orchestration(role_code, role_source_code=role_source_code),
        "role_variant": {
            "role_code": role_source_code,
            "role_layout_variant": role_code,
            "mode": "heterogeneous_same_page",
            "focus": _role_focus_config(role_code).get("focus_blocks", []),
        },
        "diagnostics": {
            "scene_contract_core": scene_contract_core.get("diagnostics") or {},
            "scene_engine": scene_engine_meta,
            "platform": {
                "ready_caps": ready_count,
                "locked_caps": locked_count,
                "preview_caps": preview_count,
                "permission_denied": permission_denied,
                "missing_scope": missing_scope,
                "feature_disabled": feature_disabled,
            },
            "data_origin": {
                "today_actions": "business_first_with_capability_fallback",
                "risk_actions": "business_first_with_capability_fallback",
                "metrics": "business_metrics",
            },
            "action_ranking_policy": {
                "version": "action_ranking_policy_v1",
                "factors": ["risk_severity", "due_urgency", "pending_count", "business_source_priority"],
                "business_priority": True,
            },
            "extraction_stats": extraction_stats,
            "business_visibility": visibility_diagnosis,
        },
    }
