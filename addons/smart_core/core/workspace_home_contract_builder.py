# -*- coding: utf-8 -*-
from __future__ import annotations

from collections import Counter
from datetime import datetime
from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path
from typing import Any, Dict, Iterable, List, Tuple
from urllib.parse import parse_qs, urlparse

from odoo import fields

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


def _shared_action_target(action_key: str, page_key: str) -> Dict[str, Any]:
    global _ACTION_TARGET_RESOLVER
    if callable(_ACTION_TARGET_RESOLVER):
        return _ACTION_TARGET_RESOLVER(action_key, page_key)
    helper_path = Path(__file__).with_name("action_target_schema.py")
    try:
        spec = spec_from_file_location("smart_core_action_target_schema_workspace_home", helper_path)
        if spec is None or spec.loader is None:
            raise RuntimeError("spec unavailable")
        module = module_from_spec(spec)
        spec.loader.exec_module(module)
        resolver = getattr(module, "resolve_action_target", None)
        if callable(resolver):
            _ACTION_TARGET_RESOLVER = resolver
            return resolver(action_key, page_key)
    except Exception:
        pass
    fallback_scene = str(page_key or "").strip().lower() or "portal.dashboard"
    return {"kind": "scene.key", "scene_key": fallback_scene}


def _load_data_provider():
    global _DATA_PROVIDER_MODULE
    if _DATA_PROVIDER_MODULE is not None:
        return _DATA_PROVIDER_MODULE

    provider_path = None
    try:
        registry_path = Path(__file__).resolve().parents[2] / "smart_scene" / "core" / "scene_provider_registry.py"
        spec = spec_from_file_location("smart_scene_provider_registry_workspace_home", registry_path)
        if spec is not None and spec.loader is not None:
            module = module_from_spec(spec)
            spec.loader.exec_module(module)
            resolver = getattr(module, "resolve_scene_provider_path", None)
            if callable(resolver):
                provider_path = resolver("workspace.home", Path(__file__))
    except Exception:
        provider_path = None

    if provider_path is None:
        provider_path = Path(__file__).with_name("workspace_home_data_provider.py")

    try:
        spec = spec_from_file_location("smart_core_workspace_home_data_provider", provider_path)
        if spec is None or spec.loader is None:
            raise RuntimeError("spec unavailable")
        module = module_from_spec(spec)
        spec.loader.exec_module(module)
        _DATA_PROVIDER_MODULE = module
        return module
    except Exception:
        _DATA_PROVIDER_MODULE = False
        return None


def _load_scene_engine_module():
    global _SCENE_ENGINE_MODULE
    if _SCENE_ENGINE_MODULE is not None:
        return _SCENE_ENGINE_MODULE
    engine_path = Path(__file__).resolve().parents[2] / "smart_scene" / "core" / "scene_engine.py"
    try:
        spec = spec_from_file_location("smart_scene_core_scene_engine_workspace_home", engine_path)
        if spec is None or spec.loader is None:
            raise RuntimeError("spec unavailable")
        module = module_from_spec(spec)
        spec.loader.exec_module(module)
        _SCENE_ENGINE_MODULE = module
        return module
    except Exception:
        _SCENE_ENGINE_MODULE = False
        return None


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
    state = _to_text(cap.get("state")).upper()
    if state in {"READY", "LOCKED", "PREVIEW"}:
        return state
    capability_state = _to_text(cap.get("capability_state")).lower()
    if capability_state in {"allow", "readonly"}:
        return "READY"
    if capability_state in {"deny"}:
        return "LOCKED"
    if capability_state in {"pending", "coming_soon"}:
        return "PREVIEW"
    return "READY"


def _scene_from_route(route: str) -> str:
    route = _to_text(route)
    if not route:
        return ""
    parsed = urlparse(route)
    if parsed.path == "/s" and parsed.query:
        return _to_text(parsed.query)
    if parsed.path.startswith("/s/"):
        return _to_text(parsed.path.split("/s/", 1)[1])
    query = parse_qs(parsed.query or "")
    value = query.get("scene")
    if value and value[0]:
        return _to_text(value[0])
    return ""


def _metric_level(value: int, amber: int, red: int) -> str:
    if value >= red:
        return "red"
    if value >= amber:
        return "amber"
    return "green"


def _is_urgent_capability(title: str, key: str) -> bool:
    merged = f"{_to_text(title)} {_to_text(key)}".lower()
    keywords = ("risk", "approval", "payment", "settlement", "风险", "审批", "付款", "结算")
    return any(keyword in merged for keyword in keywords)


def _as_record_list(payload: Any) -> List[Dict[str, Any]]:
    if isinstance(payload, list):
        return [row for row in payload if isinstance(row, dict)]
    if isinstance(payload, dict):
        for key in ("items", "records", "rows", "data", "actions", "tasks"):
            value = payload.get(key)
            if isinstance(value, list):
                return [row for row in value if isinstance(row, dict)]
    return []


def _extract_business_collections(data: Dict[str, Any]) -> Dict[str, List[Dict[str, Any]]]:
    ignored_top_keys = {
        "capabilities",
        "scenes",
        "nav",
        "nav_legacy",
        "nav_meta",
        "nav_contract",
        "default_route",
        "intents",
        "intents_meta",
        "feature_flags",
        "capability_groups",
        "capability_surface_summary",
        "preload",
        "page_contracts",
        "workspace_home",
        "role_surface",
        "role_surface_map",
        "surface_mapping",
        "surface_policies",
        "ext_facts",
        "user",
    }
    collections: Dict[str, List[Dict[str, Any]]] = {}
    for key, value in data.items():
        if key in ignored_top_keys:
            continue
        rows = _as_record_list(value)
        if rows:
            collections[str(key)] = rows
    return collections


def _is_risk_semantic_action(source_key: str, row: Dict[str, Any], action: Dict[str, Any]) -> bool:
    source_text = _to_text(source_key).lower()
    status_text = _to_text(action.get("status") or row.get("status") or row.get("state") or row.get("severity") or row.get("level")).lower()
    title_text = _to_text(action.get("title") or row.get("title") or row.get("name") or row.get("label")).lower()
    desc_text = _to_text(action.get("description") or row.get("description") or row.get("summary")).lower()
    scene_text = _to_text(action.get("scene_key") or row.get("scene_key") or row.get("scene")).lower()
    route_text = _to_text(action.get("route") or row.get("route")).lower()
    merged = " ".join([source_text, status_text, title_text, desc_text, scene_text, route_text])

    risk_tokens = (
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
    )
    return any(token in merged for token in risk_tokens)


def _route_scene_by_source(source_key: str) -> str:
    text = _to_text(source_key).lower()
    if "risk" in text or "风险" in text:
        return "risk.center"
    if "task" in text or "任务" in text:
        return "task.center"
    if "cost" in text or "boq" in text or "成本" in text:
        return "cost.project_boq"
    if "payment" in text or "finance" in text or "付款" in text or "财务" in text:
        return "finance.center"
    if "project" in text or "项目" in text:
        return "projects.list"
    return "project.management"


def _parse_deadline(value: Any) -> datetime | None:
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


def _role_ranking_profile(role_code: str) -> Dict[str, int]:
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


def _impact_score(row: Dict[str, Any]) -> int:
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


def _urgency_score(row: Dict[str, Any], title: str, source_key: str, status_text: str, role_code: str = "", source_kind: str = "business") -> int:
    profile = _role_ranking_profile(role_code)
    severity_weight = _to_int(profile.get("severity_weight") or 0)
    deadline_weight = _to_int(profile.get("deadline_weight") or 0)
    pending_weight = _to_int(profile.get("pending_weight") or 0)
    source_weight = _to_int(profile.get("source_weight") or 0)
    impact_weight = _to_int(profile.get("impact_weight") or 0)

    score = 0
    merged = f"{status_text} {title} {_to_text(source_key)}".lower()
    if any(token in merged for token in ("critical", "urgent", "overdue", "严重", "紧急", "逾期", "高")):
        score += severity_weight
    elif any(token in merged for token in ("warning", "high", "关注", "预警", "待处理")):
        score += max(20, int(severity_weight * 0.58))
    if _is_urgent_capability(title, source_key):
        score += max(8, int(severity_weight * 0.33))

    deadline = (
        _parse_deadline(row.get("due_date"))
        or _parse_deadline(row.get("deadline"))
        or _parse_deadline(row.get("planned_date"))
        or _parse_deadline(row.get("date_deadline"))
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
    score += min(impact_weight, _impact_score(row))
    if _to_text(source_kind) == "business":
        score += source_weight
    return score


def _to_business_action(source_key: str, row: Dict[str, Any], index: int, role_code: str = "", source_kind: str = "business") -> Dict[str, Any]:
    title = _to_text(row.get("title") or row.get("name") or row.get("label") or row.get("display_name"))
    if not title:
        title = f"待处理事项 {index + 1}"
    description = _to_text(row.get("description") or row.get("summary") or row.get("hint") or "进入场景继续处理业务")
    scene_key = _to_text(row.get("scene_key") or row.get("scene") or _route_scene_by_source(source_key))
    route = _to_text(row.get("route")) or f"/s/{scene_key}"
    status_text = _to_text(row.get("status") or row.get("state") or row.get("level") or row.get("severity")).lower()
    urgent_keywords = ("urgent", "high", "critical", "overdue", "严重", "紧急", "逾期", "高")
    is_urgent = any(word in status_text for word in urgent_keywords) or _is_urgent_capability(title, source_key)
    urgency_score = _urgency_score(
        row=row,
        title=title,
        source_key=source_key,
        status_text=status_text,
        role_code=role_code,
        source_kind=source_kind,
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


def _build_business_today_actions(data: Dict[str, Any], role_code: str = "") -> List[Dict[str, Any]]:
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
            candidates.append(_to_business_action(source_key, row, idx, role_code=role_code, source_kind="business"))
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


def _build_today_actions(data: Dict[str, Any], ready_caps: Iterable[Dict[str, Any]], role_code: str = "") -> List[Dict[str, Any]]:
    business_actions = _build_business_today_actions(data, role_code=role_code)
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
    expected_by_role = {
        "pm": ["project_actions", "risk_actions", "tasks", "project_tasks"],
        "finance": ["payment_requests", "risk_actions", "project_actions"],
        "owner": ["project_actions", "risk_actions", "payment_requests"],
    }
    expected = expected_by_role.get(role_code, ["project_actions", "risk_actions"])
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


def _build_risk_actions(data: Dict[str, Any], locked_caps: Iterable[Dict[str, Any]], role_code: str = "") -> List[Dict[str, Any]]:
    collections = _extract_business_collections(data)
    preferred = ["risk_actions", "risk", "risk_events", "alerts", "today_actions"]
    actions: List[Dict[str, Any]] = []
    for source_key in preferred:
        rows = collections.get(source_key, [])
        for idx, row in enumerate(rows[:6]):
            action = _to_business_action(source_key, row, idx, role_code=role_code, source_kind="business")
            if not _is_risk_semantic_action(source_key, row, action):
                continue
            action["scene_key"] = "risk.center"
            action["route"] = "/s/risk.center"
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
                action = _to_business_action("today_actions", row, idx, role_code=role_code, source_kind="business")
                if not _is_risk_semantic_action("today_actions", row, action):
                    continue
                action["scene_key"] = "risk.center"
                action["route"] = "/s/risk.center"
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
                "scene_key": "risk.center",
                "route": "/s/risk.center",
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
            "hint": "基于任务、审批、风险等业务动作聚合。",
        },
        {
            "key": "biz.risk_actions",
            "label": "高优先风险事项",
            "value": str(risk_action_count),
            "level": _metric_level(risk_action_count, 1, 3),
            "tone": _tone_from_level(_metric_level(risk_action_count, 1, 3)),
            "progress": "blocked" if risk_action_count > 0 else "running",
            "delta": "风险跟进",
            "hint": "需要优先处理的风险提醒与异常事项。",
        },
        {
            "key": "biz.project_scope",
            "label": "在管业务场景数",
            "value": str(scene_count),
            "level": _metric_level(scene_count, 3, 12),
            "tone": _tone_from_level(_metric_level(scene_count, 3, 12)),
            "progress": "running",
            "delta": "业务覆盖",
            "hint": "当前账号可直接进入的业务场景覆盖范围。",
        },
        {
            "key": "biz.execution_pressure",
            "label": "执行压力指数",
            "value": str(min(100, max(0, (today_action_count * 10) + (risk_action_count * 20)))),
            "level": _metric_level((today_action_count * 10) + (risk_action_count * 20), 30, 70),
            "tone": _tone_from_level(_metric_level((today_action_count * 10) + (risk_action_count * 20), 30, 70)),
            "progress": "running",
            "delta": "综合评估",
            "hint": "根据今日行动量与高优先风险计算的运行负载指标。",
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
        "pm": ["project_manager", "construction_manager"],
        "finance": ["finance_manager", "construction_manager"],
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
        "open_risk_dashboard": {"label": "进入风险驾驶舱", "intent": "ui.contract"},
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
            "target": _shared_action_target(action_key, "portal.dashboard"),
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
            "title": "核心关注",
            "description": "角色上下文与默认入口。",
            "zone_type": "hero",
            "display_mode": "stack",
            "priority": 40,
            "visibility": {"roles": audience, "capabilities": [], "expr": None},
            "blocks": [
                {
                    "key": "hero_record_summary",
                    "block_type": "record_summary",
                    "title": "角色与入口摘要",
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
                    "actions": [{"key": "open_landing", "label": "打开默认入口", "intent": "ui.contract"}],
                    "payload": {"style_variant": "default"},
                }
            ],
        },
        {
            "key": "today_focus",
            "title": "今日优先事项",
            "description": "先处理行动项，再快速处置风险提醒。",
            "zone_type": "primary",
            "display_mode": "grid",
            "priority": 100,
            "visibility": {"roles": audience, "capabilities": [], "expr": None},
            "blocks": [
                {
                    "key": "todo_list_today",
                    "block_type": "todo_list",
                    "title": "今日行动",
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
                    "actions": [{"key": "open_my_work", "label": "查看全部", "intent": "ui.contract"}],
                    "payload": {"item_layout": "card", "max_items": 4},
                },
                {
                    "key": "risk_alert_panel",
                    "block_type": "alert_panel",
                    "title": "系统提醒（高优先）",
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
                    "actions": [{"key": "open_risk_dashboard", "label": "进入风险驾驶舱", "intent": "ui.contract"}],
                    "payload": {"group_by": "alert_level", "show_counts": True, "max_items": 3},
                },
                {
                    "key": "advice_fold",
                    "block_type": "accordion_group",
                    "title": "系统建议（补充）",
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
            "title": "项目总体状态",
            "description": "关键指标、执行进展与风险动态。",
            "zone_type": "secondary",
            "display_mode": "grid",
            "priority": 80,
            "visibility": {"roles": audience, "capabilities": [], "expr": None},
            "blocks": [
                {
                    "key": "metric_row_core",
                    "block_type": "metric_row",
                    "title": "关键指标",
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
                    "title": "综合进展",
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
                    "title": "风险动态",
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
            "title": "常用功能",
            "description": "按业务场景快速进入处理。",
            "zone_type": "supporting",
            "display_mode": "grid",
            "priority": 60,
            "visibility": {"roles": audience, "capabilities": [], "expr": None},
            "blocks": [
                {
                    "key": "entry_grid_scene",
                    "block_type": "entry_grid",
                    "title": "常用功能",
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
                    "actions": [{"key": "open_scene", "label": "进入场景", "intent": "ui.contract"}],
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
    role_zone_order = {
        "pm": ["today_focus", "analysis", "quick_entries", "hero"],
        "finance": ["analysis", "today_focus", "quick_entries", "hero"],
        "owner": ["analysis", "today_focus", "hero", "quick_entries"],
    }
    preferred_order = role_zone_order.get(role_code, role_zone_order["owner"])
    effective_order = preferred_order
    priority_map = {key: 100 - (idx * 10) for idx, key in enumerate(effective_order)}
    for zone in zones:
        zone_key = _to_text(zone.get("key"))
        if zone_key in priority_map:
            zone["priority"] = priority_map[zone_key]

    v1_focus_map = {
        "pm": ["todo_list_today", "risk_alert_panel", "metric_row_core", "progress_summary_ops"],
        "finance": ["todo_list_today", "risk_alert_panel", "progress_summary_ops", "metric_row_core"],
        "owner": ["todo_list_today", "risk_alert_panel", "metric_row_core", "progress_summary_ops"],
    }
    provider = _load_data_provider()
    if provider is not None:
        fn = getattr(provider, "build_v1_focus_map", None)
        if callable(fn):
            payload = fn()
            if isinstance(payload, dict) and payload:
                v1_focus_map = payload
    focus_blocks = {str(key): idx + 1 for idx, key in enumerate(v1_focus_map.get(role_code, []))}
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
        "scene_key": "portal.dashboard",
        "page": {
            "key": "portal.dashboard",
            "title": "工作台",
            "subtitle": "先处理行动项，再关注风险与总体状态",
            "page_type": "workspace",
            "intent": "ui.contract",
            "scene_key": "portal.dashboard",
            "layout_mode": "dashboard",
            "audience": audience,
            "priority_model": priority_model,
            "status": "ready",
            "breadcrumbs": [],
            "header": {"badges": [{"label": "运行正常", "tone": "success"}]},
            "global_actions": [{"key": "refresh", "label": "刷新", "intent": "api.data"}],
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
    today_actions = _build_today_actions(data, ready_caps, role_code=role_code)
    risk_actions = _build_risk_actions(data, locked_caps, role_code=role_code)
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
        "scene": {"key": "portal.dashboard", "page": "portal.dashboard"},
        "page": {"key": "portal.dashboard", "title": "工作台", "route": "/"},
        "nav_ref": {"active_scene_key": "portal.dashboard", "active_menu_key": "scene:portal.dashboard", "active_menu_id": None},
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
                scene_hint={"key": "portal.dashboard", "page": "portal.dashboard"},
                page_hint={"key": "portal.dashboard", "title": "工作台", "route": "/"},
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
            "texts": {
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
                "today_actions.subtitle": "先处理高优先事项，再进入对应业务场景。",
                "today_actions.count_prefix": "待处理",
                "today_actions.coming_soon_action": "即将开放",
                "risk.aria_label": "关键风险区",
                "risk.title": "关键风险",
                "risk.subtitle": "10 秒识别整体风险态势。",
                "risk.bucket.red": "严重 ⚠",
                "risk.bucket.amber": "关注 ⏳",
                "risk.bucket.green": "正常 ✓",
                "risk.trend_title": "风险趋势（7/30 天）",
                "risk.sources_title": "风险来源分布",
                "risk.actions_title": "风险待处理清单",
                "risk.actions.detail": "看详情",
                "risk.actions.assign": "分派",
                "risk.actions.close": "关闭",
                "risk.actions.approve": "发起审批",
                "ops.title": "项目总体状态",
                "ops.aria_label": "项目总体状态区",
                "ops.compare.title": "合同履约与产值完成",
                "ops.compare.contract": "合同额",
                "ops.compare.output": "累计产值",
                "ops.kpi.cost_rate": "成本控制率",
                "ops.kpi.payment_rate": "资金支付率",
                "ops.kpi.output_trend": "本月产值趋势",
                "ops.kpi.output_note": "基于当前可见业务数据",
                "advice.title": "系统提醒",
                "advice.aria_label": "系统提醒",
                "group_overview.title": "常用功能",
                "group_overview.subtitle": "按业务域快速进入核心功能。",
                "group_overview.capability_count_prefix": "功能数",
                "group_overview.allow_prefix": "可用",
                "group_overview.readonly_prefix": "只读",
                "group_overview.deny_prefix": "禁用",
            },
            "actions": {
                "todo_default": "查看详情",
                "todo_approval": "审核付款申请",
                "todo_contract": "查看合同异常",
                "todo_risk": "处理风险事项",
                "todo_change": "确认变更事项",
                "todo_overdue": "处理逾期任务",
            },
        },
        "hero": {
            "title": "工作台",
            "lead": "先做什么、风险在哪、状态如何：围绕今日行动推进业务闭环。",
            "product_tags": ["项目管理", "经营状态", "风险预警"],
            "updated_at": updated_at,
            "status_notice": partial_notice,
            "status_detail": (
                "当前业务明细不足，主区已回退到系统就绪入口。"
                if not has_business_signal
                else "当前角色可见业务数据偏少，建议核对项目归属与示例数据分配。"
                if _to_text(visibility_diagnosis.get("gap_level")) == "limited"
                else ""
            ),
        },
        "metrics": business_metrics,
        "platform_metrics": platform_metrics,
        "today_actions": today_actions,
        "risk": {
            "summary": (
                "存在高优先风险，请先处理系统提醒事项。"
                if risk_red >= 3
                else "存在需要跟进的风险，建议今日内完成处理。"
                if risk_red >= 1
                else "当前未出现严重风险，建议保持日常巡检节奏。"
            ),
            "buckets": {"red": risk_red, "amber": risk_amber, "green": risk_green},
            "tone": "danger" if risk_red > 0 else "warning" if risk_amber > 0 else "success",
            "progress": "blocked" if risk_red > 0 else "running",
            "trend": [
                {"label": "30天前", "value": risk_d30, "percent": round((risk_d30 / risk_max) * 100)},
                {"label": "7天前", "value": risk_d7, "percent": round((risk_d7 / risk_max) * 100)},
                {"label": "当前", "value": risk_now, "percent": round((risk_now / risk_max) * 100)},
            ],
            "sources": [
                {"label": "业务风险动作", "count": len([row for row in risk_actions if _to_text(row.get("source")) == "business"])},
                {"label": "能力兜底动作", "count": len([row for row in risk_actions if _to_text(row.get("source")) != "business"])},
                {"label": "权限限制", "count": permission_denied},
            ],
            "actions": risk_actions,
        },
        "ops": {
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
            "tone": "info",
            "progress": "running",
            "data_state": "business" if has_business_signal else "fallback",
        },
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
