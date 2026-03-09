# -*- coding: utf-8 -*-
from __future__ import annotations

from typing import Any, Dict, Iterable, List


def _to_text(value: Any) -> str:
    text = str(value or "").strip()
    return text


def _to_int(value: Any) -> int:
    try:
        number = int(value)
        return number if number >= 0 else 0
    except Exception:
        return 0


def _scene_from_route(route: str) -> str:
    from urllib.parse import parse_qs, urlparse

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


def _is_urgent_capability(title: str, key: str) -> bool:
    merged = f"{_to_text(title)} {_to_text(key)}".lower()
    keywords = ("risk", "approval", "payment", "settlement", "风险", "审批", "付款", "结算")
    return any(keyword in merged for keyword in keywords)


def build_today_actions(ready_caps: Iterable[Dict[str, Any]]) -> List[Dict[str, Any]]:
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


def build_advice_items(locked_caps: Iterable[Dict[str, Any]]) -> List[Dict[str, Any]]:
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


def build_role_focus_config(role_code: str) -> Dict[str, Any]:
    role = _to_text(role_code).lower()
    if role == "pm":
        return {
            "zone_order": ["primary", "analysis", "support"],
            "focus_blocks": ["todo_core", "risk_core", "ops_progress", "record_overview"],
        }
    if role == "finance":
        return {
            "zone_order": ["analysis", "primary", "support"],
            "focus_blocks": ["ops_progress", "risk_core", "metrics_kpi", "record_overview"],
        }
    return {
        "zone_order": ["primary", "support", "analysis"],
        "focus_blocks": ["record_overview", "risk_core", "todo_core", "entry_grid"],
    }


def build_v1_focus_map() -> Dict[str, List[str]]:
    return {
        "pm": ["todo_list_today", "risk_alert_panel", "progress_summary_ops", "hero_record_summary"],
        "finance": ["progress_summary_ops", "risk_alert_panel", "metric_row_core", "hero_record_summary"],
        "owner": ["hero_record_summary", "risk_alert_panel", "todo_list_today", "entry_grid_scene"],
    }


def build_v1_page_profile(role_code: str) -> Dict[str, Any]:
    role = _to_text(role_code).lower()
    audience_map = {
        "pm": ["project_manager", "construction_manager"],
        "finance": ["finance_manager", "construction_manager"],
        "owner": ["owner", "executive"],
    }
    audience = audience_map.get(role, ["owner"])
    priority_model = "task_first" if role == "pm" else "metric_first" if role == "finance" else "role_first"
    mobile_priority_map = {
        "pm": ["hero", "today_focus", "analysis"],
        "finance": ["analysis", "hero", "today_focus"],
        "owner": ["hero", "today_focus", "analysis"],
    }
    return {
        "audience": audience,
        "priority_model": priority_model,
        "mobile_priority": mobile_priority_map.get(role, ["hero", "today_focus", "analysis"]),
    }


def build_v1_data_sources() -> Dict[str, Dict[str, Any]]:
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


def build_v1_state_schema() -> Dict[str, Any]:
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


def build_v1_action_specs() -> Dict[str, Dict[str, str]]:
    return {
        "open_landing": {"label": "打开默认入口", "intent": "ui.contract"},
        "open_my_work": {"label": "查看全部", "intent": "ui.contract"},
        "open_risk_dashboard": {"label": "进入风险驾驶舱", "intent": "ui.contract"},
        "open_scene": {"label": "进入场景", "intent": "ui.contract"},
        "refresh": {"label": "刷新", "intent": "api.data"},
    }


def build_legacy_zones(role_code: str, zone_rank: Dict[str, int]) -> List[Dict[str, Any]]:
    return [
        {"key": "primary", "label": "主行动区", "order": int(zone_rank.get("primary", 1))},
        {"key": "analysis", "label": "分析监控区", "order": int(zone_rank.get("analysis", 2))},
        {"key": "support", "label": "辅助入口区", "order": int(zone_rank.get("support", 3))},
    ]


def build_legacy_blocks(role_code: str) -> List[Dict[str, Any]]:
    return [
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
            "visible": _to_text(role_code).lower() != "owner",
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


def build_v1_zones(role_code: str, audience: List[str], zone_rank: Dict[str, int]) -> List[Dict[str, Any]]:
    return [
        {
            "key": "hero",
            "title": "核心关注",
            "description": "页面主关注区，先看角色和当前态势。",
            "zone_type": "hero",
            "display_mode": "grid",
            "priority": int(zone_rank.get("primary", 1)) * 100,
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
            "priority": int(zone_rank.get("primary", 1)) * 90,
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
            "priority": int(zone_rank.get("analysis", 2)) * 80,
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
            "title": "能力入口",
            "description": "按能力分组快速进入业务场景。",
            "zone_type": "supporting",
            "display_mode": "grid",
            "priority": int(zone_rank.get("support", 3)) * 70,
            "visibility": {"roles": audience, "capabilities": [], "expr": None},
            "blocks": [
                {
                    "key": "entry_grid_scene",
                    "block_type": "entry_grid",
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
                    "block_type": "entry_grid",
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
                    "block_type": "accordion_group",
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
                    "block_type": "accordion_group",
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
