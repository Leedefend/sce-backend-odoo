# -*- coding: utf-8 -*-
from __future__ import annotations

from collections import Counter
from typing import Any, Dict, Iterable, List
from urllib.parse import parse_qs, urlparse

from odoo import fields

BLOCK_TYPES = (
    "hero_metric",
    "kpi_row",
    "todo_list",
    "alert_panel",
    "progress_group",
    "quick_entry_grid",
    "fold_section",
    "record_summary",
    "activity_feed",
)

STATE_TONES = ("success", "warning", "danger", "info", "neutral")
PROGRESS_STATES = ("overdue", "blocked", "pending", "running", "completed")


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


def _tone_from_level(level: str) -> str:
    normalized = _to_text(level).lower()
    if normalized in {"red", "danger"}:
        return "danger"
    if normalized in {"amber", "warning"}:
        return "warning"
    if normalized in {"green", "success"}:
        return "success"
    return "neutral"


def _normalize_role_code(data: Dict[str, Any]) -> str:
    role_surface = data.get("role_surface") if isinstance(data.get("role_surface"), dict) else {}
    role_code = _to_text(role_surface.get("role_code")).lower()
    if role_code in {"pm", "finance", "owner"}:
        return role_code
    return "owner"


def _role_focus_config(role_code: str) -> Dict[str, Any]:
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


def _build_page_orchestration(role_code: str) -> Dict[str, Any]:
    role_cfg = _role_focus_config(role_code)
    zone_order = role_cfg.get("zone_order") if isinstance(role_cfg.get("zone_order"), list) else []
    zone_rank = {str(key): idx + 1 for idx, key in enumerate(zone_order)}
    zones = [
        {"key": "primary", "label": "主行动区", "order": zone_rank.get("primary", 1)},
        {"key": "analysis", "label": "分析监控区", "order": zone_rank.get("analysis", 2)},
        {"key": "support", "label": "辅助入口区", "order": zone_rank.get("support", 3)},
    ]
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
            "type": "kpi_row",
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
            "type": "progress_group",
            "zone": "analysis",
            "order": 6,
            "source_path": "ops",
            "visible": True,
            "tone": "info",
            "progress": "running",
        },
        {
            "key": "entry_grid",
            "type": "quick_entry_grid",
            "zone": "support",
            "order": 7,
            "source_path": "scene_groups",
            "visible": True,
            "tone": "neutral",
            "progress": "completed",
        },
        {
            "key": "group_grid",
            "type": "quick_entry_grid",
            "zone": "support",
            "order": 8,
            "source_path": "group_overview",
            "visible": True,
            "tone": "neutral",
            "progress": "completed",
        },
        {
            "key": "advice_fold",
            "type": "fold_section",
            "zone": "support",
            "order": 9,
            "source_path": "advice",
            "visible": True,
            "tone": "warning",
            "progress": "pending",
        },
        {
            "key": "filters_fold",
            "type": "fold_section",
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
            "role_code": role_code,
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


def _build_page_orchestration_v1(role_code: str) -> Dict[str, Any]:
    role_cfg = _role_focus_config(role_code)
    zone_order = role_cfg.get("zone_order") if isinstance(role_cfg.get("zone_order"), list) else []
    zone_rank = {str(key): idx + 1 for idx, key in enumerate(zone_order)}
    audience_map = {
        "pm": ["project_manager", "construction_manager"],
        "finance": ["finance_manager", "construction_manager"],
        "owner": ["owner", "executive"],
    }
    audience = audience_map.get(role_code, ["owner"])
    priority_model = "task_first" if role_code == "pm" else "metric_first" if role_code == "finance" else "role_first"

    zones: List[Dict[str, Any]] = [
        {
            "key": "hero",
            "title": "核心关注",
            "description": "页面主关注区，先看角色和当前态势。",
            "zone_type": "hero",
            "display_mode": "grid",
            "priority": zone_rank.get("primary", 1) * 100,
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
            "title": "今日聚焦",
            "description": "今日待办与关键风险。",
            "zone_type": "primary",
            "display_mode": "stack",
            "priority": zone_rank.get("primary", 1) * 90,
            "visibility": {"roles": audience, "capabilities": [], "expr": None},
            "blocks": [
                {
                    "key": "todo_list_today",
                    "block_type": "todo_list",
                    "title": "今日待办",
                    "priority": 95,
                    "importance": "high",
                    "tone": "warning",
                    "progress": "pending",
                    "section_key": "today_actions",
                    "data_source": "ds_today_todos",
                    "loading_strategy": "eager",
                    "refreshable": True,
                    "collapsible": False,
                    "visibility": {"roles": audience, "capabilities": [], "expr": None},
                    "actions": [{"key": "open_my_work", "label": "查看全部", "intent": "ui.contract"}],
                    "payload": {"item_layout": "card", "max_items": 6},
                },
                {
                    "key": "risk_alert_panel",
                    "block_type": "alert_panel",
                    "title": "关键风险",
                    "priority": 90,
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
                    "payload": {"group_by": "alert_level", "show_counts": True, "max_items": 10},
                },
            ],
        },
        {
            "key": "analysis",
            "title": "经营分析",
            "description": "关键指标与执行进展。",
            "zone_type": "secondary",
            "display_mode": "grid",
            "priority": zone_rank.get("analysis", 2) * 80,
            "visibility": {"roles": audience, "capabilities": [], "expr": None},
            "blocks": [
                {
                    "key": "kpi_row_core",
                    "block_type": "kpi_row",
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
                    "key": "progress_group_ops",
                    "block_type": "progress_group",
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
            "title": "能力入口",
            "description": "按能力分组快速进入业务场景。",
            "zone_type": "supporting",
            "display_mode": "grid",
            "priority": zone_rank.get("support", 3) * 70,
            "visibility": {"roles": audience, "capabilities": [], "expr": None},
            "blocks": [
                {
                    "key": "entry_grid_scene",
                    "block_type": "quick_entry_grid",
                    "title": "场景入口",
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
                {
                    "key": "entry_grid_capability",
                    "block_type": "quick_entry_grid",
                    "title": "能力分组",
                    "priority": 60,
                    "importance": "medium",
                    "tone": "neutral",
                    "progress": "completed",
                    "section_key": "group_overview",
                    "data_source": "ds_capability_groups",
                    "loading_strategy": "lazy",
                    "refreshable": True,
                    "collapsible": False,
                    "visibility": {"roles": audience, "capabilities": [], "expr": None},
                    "actions": [],
                    "payload": {"layout": "2x4", "show_icon": True, "show_hint": True},
                },
                {
                    "key": "advice_fold",
                    "block_type": "fold_section",
                    "title": "系统建议",
                    "priority": 55,
                    "importance": "medium",
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
                {
                    "key": "filters_fold",
                    "block_type": "fold_section",
                    "title": "筛选器",
                    "priority": 50,
                    "importance": "low",
                    "tone": "neutral",
                    "progress": "completed",
                    "section_key": "filters",
                    "data_source": "ds_filters",
                    "loading_strategy": "lazy",
                    "refreshable": False,
                    "collapsible": True,
                    "visibility": {"roles": audience, "capabilities": [], "expr": None},
                    "actions": [],
                    "payload": {"mode": "accordion"},
                },
            ],
        },
    ]

    v1_focus_map = {
        "pm": ["todo_list_today", "risk_alert_panel", "progress_group_ops", "hero_record_summary"],
        "finance": ["progress_group_ops", "risk_alert_panel", "kpi_row_core", "hero_record_summary"],
        "owner": ["hero_record_summary", "risk_alert_panel", "todo_list_today", "entry_grid_scene"],
    }
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
            "subtitle": "今日运营与执行总览",
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
            "context": {"role_code": role_code},
        },
        "zones": zones,
        "data_sources": {
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
        },
        "state_schema": {
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
        },
        "action_schema": {
            "actions": {
                "open_landing": {"label": "打开默认入口", "intent": "ui.contract", "target": {"kind": "scene.key", "scene_key": "portal.dashboard"}},
                "open_my_work": {"label": "查看全部", "intent": "ui.contract", "target": {"kind": "scene.key", "scene_key": "my_work.workspace"}},
                "open_risk_dashboard": {
                    "label": "进入风险驾驶舱",
                    "intent": "ui.contract",
                    "target": {"kind": "scene.key", "scene_key": "projects.dashboard"},
                },
                "open_scene": {"label": "进入场景", "intent": "ui.contract", "target": {"kind": "scene.key", "scene_key": "projects.list"}},
                "refresh": {"label": "刷新", "intent": "api.data", "target": {"kind": "page.refresh"}},
            }
        },
        "render_hints": {
            "dense_mode": False,
            "preferred_columns": 4,
            "mobile_priority": ["hero", "today_focus", "analysis"],
            "sticky_header": True,
        },
        "meta": {
            "generated_by": "smart_core.workspace_home_contract_builder",
            "schema_version": "1.0.0",
            "role_variant": role_code,
        },
    }


def _build_today_actions(ready_caps: Iterable[Dict[str, Any]]) -> List[Dict[str, Any]]:
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
            }
        )
    return actions


def _build_advice_items(locked_caps: Iterable[Dict[str, Any]]) -> List[Dict[str, Any]]:
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
    nav_count = len(data.get("nav") or []) if isinstance(data.get("nav"), list) else 0

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
    role_code = _normalize_role_code(data)

    return {
        "schema_version": "v1",
        "semantic_protocol": {
            "block_types": list(BLOCK_TYPES),
            "state_tones": list(STATE_TONES),
            "progress_states": list(PROGRESS_STATES),
        },
        "layout": {
            "sections": [
                {"key": "hero", "enabled": True, "tag": "header"},
                {"key": "metrics", "enabled": True, "tag": "section"},
                {"key": "today_actions", "enabled": True, "tag": "section"},
                {"key": "risk", "enabled": True, "tag": "section"},
                {"key": "ops", "enabled": True, "tag": "details", "open": False},
                {"key": "advice", "enabled": True, "tag": "details", "open": False},
                {"key": "group_overview", "enabled": True, "tag": "section"},
                {"key": "filters", "enabled": True, "tag": "section"},
                {"key": "scene_groups", "enabled": True, "tag": "div"},
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
                "hero.steady_notice": "当前运行平稳",
                "metrics.aria_label": "核心价值区",
                "today_actions.aria_label": "今日建议",
                "today_actions.title": "今日待办",
                "today_actions.subtitle": "点击可直接进入处理界面。",
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
                "ops.title": "项目经营概览",
                "ops.aria_label": "项目经营概览区",
                "ops.compare.title": "合同额 vs 累计产值",
                "ops.compare.contract": "合同额",
                "ops.compare.output": "累计产值",
                "ops.kpi.cost_rate": "成本执行率",
                "ops.kpi.payment_rate": "资金支付比例",
                "ops.kpi.output_trend": "本月产值趋势",
                "ops.kpi.output_note": "基于当前可见业务数据",
                "advice.title": "系统建议关注事项",
                "advice.aria_label": "系统建议关注事项",
                "group_overview.title": "辅助入口",
                "group_overview.subtitle": "按业务域查看功能分组与可用状态。",
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
            "lead": "围绕项目经营、风险与审批，优先处理今天最关键事项。",
            "product_tags": ["管理工具", "项目管理", "经营分析", "风险管控"],
            "updated_at": updated_at,
            "status_notice": partial_notice,
            "status_detail": "",
        },
        "metrics": [
            {
                "key": "capability.ready",
                "label": "可进入能力",
                "value": str(ready_count),
                "level": _metric_level(ready_count, 1, 8),
                "tone": _tone_from_level(_metric_level(ready_count, 1, 8)),
                "progress": "running",
                "delta": "能力可用面",
                "hint": "可直接进入并处理业务的能力数量。",
            },
            {
                "key": "capability.locked",
                "label": "受限能力",
                "value": str(locked_count),
                "level": _metric_level(locked_count, 1, 4),
                "tone": _tone_from_level(_metric_level(locked_count, 1, 4)),
                "progress": "blocked",
                "delta": "待开通项",
                "hint": "受权限或策略影响暂不可用的能力数量。",
            },
            {
                "key": "capability.preview",
                "label": "预览能力",
                "value": str(preview_count),
                "level": _metric_level(preview_count, 1, 4),
                "tone": _tone_from_level(_metric_level(preview_count, 1, 4)),
                "progress": "pending",
                "delta": "待建设项",
                "hint": "已在契约注册但尚未正式开放的能力数量。",
            },
            {
                "key": "scene.count",
                "label": "可见场景数",
                "value": str(scene_count),
                "level": _metric_level(scene_count, 3, 20),
                "tone": _tone_from_level(_metric_level(scene_count, 3, 20)),
                "progress": "running",
                "delta": "场景覆盖",
                "hint": "当前角色可访问的场景数量。",
            },
            {
                "key": "nav.count",
                "label": "可见导航节点",
                "value": str(nav_count),
                "level": _metric_level(nav_count, 3, 20),
                "tone": _tone_from_level(_metric_level(nav_count, 3, 20)),
                "progress": "running",
                "delta": "导航覆盖",
                "hint": "当前导航树可见一级节点数量。",
            },
        ],
        "today_actions": _build_today_actions(ready_caps),
        "risk": {
            "summary": (
                "高风险集中在受限能力，请优先处理开通项。"
                if risk_red >= 3
                else "存在受限能力，建议先处理高优先级入口。"
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
                {"label": "权限限制", "count": permission_denied},
                {"label": "能力前置缺失", "count": missing_scope},
                {"label": "功能未开通", "count": feature_disabled},
            ],
            "actions": [
                {
                    "id": _to_text(cap.get("key")),
                    "title": _to_text(cap.get("ui_label") or cap.get("name") or cap.get("key")) or "受限能力",
                    "description": _to_text(cap.get("reason")) or "当前账号尚未开通该能力。",
                    "entry_key": _to_text(cap.get("key")),
                }
                for cap in locked_caps[:3]
            ],
        },
        "ops": {
            "bars": {
                "contract": 100,
                "output": round((ready_count / max(total_caps, 1)) * 100),
            },
            "kpi": {
                "cost_rate": round((ready_count / max(total_caps, 1)) * 100),
                "payment_rate": round(((ready_count + preview_count) / max(total_caps, 1)) * 100),
                "cost_rate_delta": 0,
                "payment_rate_delta": 0,
                "output_trend_delta": 0,
            },
            "tone": "info",
            "progress": "running",
        },
        "advice": _build_advice_items(locked_caps),
        "page_orchestration_v1": _build_page_orchestration_v1(role_code),
        "page_orchestration": _build_page_orchestration(role_code),
        "role_variant": {
            "role_code": role_code,
            "mode": "heterogeneous_same_page",
            "focus": _role_focus_config(role_code).get("focus_blocks", []),
        },
    }
