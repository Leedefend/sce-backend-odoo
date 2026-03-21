# -*- coding: utf-8 -*-
from __future__ import annotations

from typing import Any, Dict, Iterable, List


def build_scene_aliases() -> Dict[str, str]:
    return {
        "default": "workspace.home",
        "dashboard": "portal.dashboard",
        "project_list": "projects.list",
        "project_management": "project.management",
        "execution": "projects.execution",
        "operation_overview": "operation.overview",
        "risk_center": "risk.center",
        "task_center": "task.center",
        "cost_center": "cost.project_boq",
        "finance_center": "finance.center",
    }


def build_layout_texts_overrides() -> Dict[str, str]:
    return {
        "hero.role_label": "当前岗位",
        "hero.landing_label": "默认入口",
        "entry.navigate": "进入场景",
        "entry.navigate_short": "进入",
        "entry.meta.menu": "菜单",
        "entry.meta.action": "动作",
        "todo.empty": "当前暂无待办事项",
        "risk.summary": "风险概览",
        "ops.title": "经营态势",
    }


def build_layout_actions_overrides() -> Dict[str, str]:
    return {
        "todo_default": "查看详情",
        "todo_approval": "处理审批",
        "todo_contract": "查看合同",
        "todo_risk": "处理风险",
        "todo_change": "确认变更",
        "todo_overdue": "处理逾期",
    }


def build_workspace_hero_payload(
    *,
    has_business_signal: bool,
    gap_level: str,
    updated_at: str,
    partial_notice: str,
) -> Dict[str, Any]:
    status_detail = ""
    if not has_business_signal:
        status_detail = "当前业务明细不足，已回退到系统就绪入口。"
    elif _to_text(gap_level).lower() == "limited":
        status_detail = "当前可见业务数据偏少，建议核对岗位授权与数据分配。"
    return {
        "title": "工程协作工作台",
        "lead": "围绕项目执行、经营态势与风险事项，快速完成今日关键动作。",
        "product_tags": ["项目执行", "经营态势", "风险预警"],
        "updated_at": _to_text(updated_at),
        "status_notice": _to_text(partial_notice),
        "status_detail": status_detail,
    }


def build_risk_summary_text(*, risk_red: int) -> str:
    red = _to_int(risk_red)
    if red >= 3:
        return "存在高优先风险，请优先完成处置并跟进闭环。"
    if red >= 1:
        return "存在待跟进风险，建议在今日完成核查与责任落实。"
    return "当前未发现高优先风险，建议保持日常巡检节奏。"


def build_ops_payload(
    *,
    has_business_signal: bool,
    risk_business_count: int,
    today_business_count: int,
) -> Dict[str, Any]:
    if not has_business_signal:
        return {
            "bars": {"contract": 0, "output": 0},
            "kpi": {
                "cost_rate": 0,
                "payment_rate": 0,
                "cost_rate_delta": 0,
                "payment_rate_delta": 0,
                "output_trend_delta": 0,
            },
        }

    risk_count = _to_int(risk_business_count)
    today_count = _to_int(today_business_count)
    contract_score = max(0, min(100, 100 - (risk_count * 10)))
    output_score = max(0, min(100, 100 - (today_count * 8)))
    cost_score = max(0, min(100, 100 - (risk_count * 12)))
    payment_score = max(0, min(100, 100 - (today_count * 6)))

    return {
        "bars": {
            "contract": contract_score,
            "output": output_score,
        },
        "kpi": {
            "cost_rate": cost_score,
            "payment_rate": payment_score,
            "cost_rate_delta": 0,
            "payment_rate_delta": 0,
            "output_trend_delta": 0,
        },
    }


def build_risk_payload(
    *,
    defaults: Dict[str, Any],
    summary: str,
    risk_red: int,
    risk_amber: int,
    risk_green: int,
    risk_actions: List[Dict[str, Any]],
    permission_denied: int,
) -> Dict[str, Any]:
    payload = dict(defaults or {})
    payload["summary"] = _to_text(summary) or payload.get("summary") or ""
    payload["buckets"] = {
        "red": _to_int(risk_red),
        "amber": _to_int(risk_amber),
        "green": _to_int(risk_green),
    }
    payload["tone"] = "danger" if _to_int(risk_red) > 0 else "warning" if _to_int(risk_amber) > 0 else "success"
    payload["progress"] = "blocked" if _to_int(risk_red) > 0 else "running"

    trend = payload.get("trend") if isinstance(payload.get("trend"), list) else []
    normalized_trend: List[Dict[str, Any]] = []
    default_labels = ["30天前", "7天前", "当前"]
    for index, row in enumerate(trend[:3]):
        if not isinstance(row, dict):
            continue
        normalized_trend.append(
            {
                "label": default_labels[index],
                "value": _to_int(row.get("value")),
                "percent": _to_int(row.get("percent")),
            }
        )
    if normalized_trend:
        payload["trend"] = normalized_trend

    payload["sources"] = [
        {"label": "业务告警动作", "count": len([row for row in list(risk_actions or []) if _to_text((row or {}).get("source")) == "business"])},
        {"label": "能力兜底动作", "count": len([row for row in list(risk_actions or []) if _to_text((row or {}).get("source")) != "business"])},
        {"label": "权限限制", "count": _to_int(permission_denied)},
    ]
    payload["actions"] = list(risk_actions or [])
    return payload


def build_ops_meta(*, defaults: Dict[str, str], has_business_signal: bool) -> Dict[str, str]:
    payload = dict(defaults or {})
    payload["tone"] = "info"
    payload["progress"] = "running"
    payload["data_state"] = "business" if has_business_signal else "fallback"
    return payload


def resolve_scene_by_source(source_key: str) -> str:
    aliases = build_scene_aliases()
    text = _to_text(source_key).lower()
    if "risk" in text or "风险" in text:
        return aliases["risk_center"]
    if "task" in text or "任务" in text:
        return aliases["task_center"]
    if "cost" in text or "boq" in text or "成本" in text:
        return aliases["cost_center"]
    if "payment" in text or "finance" in text or "付款" in text or "财务" in text:
        return aliases["finance_center"]
    if "project" in text or "项目" in text:
        return aliases["project_list"]
    return aliases["project_management"]


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
    entries: List[Dict[str, Any]] = []
    for cap in list(ready_caps):
        payload = cap.get("default_payload") if isinstance(cap.get("default_payload"), dict) else {}
        route = _to_text(payload.get("route"))
        scene_key = _scene_from_route(route)
        title = _to_text(cap.get("ui_label") or cap.get("name") or cap.get("key"))
        entries.append(
            {
                "entry_key": _to_text(cap.get("key")),
                "title": title,
                "hint": _to_text(cap.get("ui_hint")) or "进入能力继续处理业务",
                "scene_key": scene_key,
                "route": route,
                "menu_id": _to_int(payload.get("menu_id")),
                "action_id": _to_int(payload.get("action_id")),
            }
        )

    templates = [
        {
            "id": "action-risk",
            "title": "待处理风险事项",
            "description": "优先处理高风险项目，避免延误与损失扩大。",
            "status": "urgent",
            "tone": "danger",
            "keywords": ("risk.center", "risk", "风险"),
        },
        {
            "id": "action-payment",
            "title": "待审批付款申请",
            "description": "处理付款审批与节点确认，保障资金协同。",
            "status": "urgent",
            "tone": "warning",
            "keywords": ("payment", "finance", "付款", "资金", "财务"),
        },
        {
            "id": "action-task",
            "title": "待跟进项目任务",
            "description": "跟进关键任务进度，避免节点延期。",
            "status": "normal",
            "tone": "info",
            "keywords": ("task.center", "task", "任务", "项目"),
        },
        {
            "id": "action-cost",
            "title": "待确认成本清单",
            "description": "核对工程量与成本偏差，保持成本可控。",
            "status": "normal",
            "tone": "info",
            "keywords": ("cost.project_boq", "cost", "boq", "成本", "清单"),
        },
    ]

    used_keys = set()
    actions: List[Dict[str, Any]] = []
    for template in templates:
        matched = None
        for entry in entries:
            entry_key = _to_text(entry.get("entry_key"))
            if entry_key in used_keys:
                continue
            scope = " ".join(
                [
                    _to_text(entry.get("entry_key")),
                    _to_text(entry.get("title")),
                    _to_text(entry.get("scene_key")),
                    _to_text(entry.get("route")),
                ]
            ).lower()
            if any(keyword in scope for keyword in template["keywords"]):
                matched = entry
                used_keys.add(entry_key)
                break
        if not matched:
            continue
        actions.append(
            {
                "id": template["id"],
                "title": template["title"],
                "description": template["description"],
                "status": template["status"],
                "tone": template["tone"],
                "progress": "pending",
                "ready": True,
                "entry_key": _to_text(matched.get("entry_key")),
                "scene_key": _to_text(matched.get("scene_key")),
                "route": _to_text(matched.get("route")),
                "menu_id": _to_int(matched.get("menu_id")),
                "action_id": _to_int(matched.get("action_id")),
                "source": "business",
                "source_detail": "semantic_template",
            }
        )

    if len(actions) < 3:
        for entry in entries:
            entry_key = _to_text(entry.get("entry_key"))
            if entry_key in used_keys:
                continue
            actions.append(
                {
                    "id": entry_key or _to_text(entry.get("title")) or "action-extra",
                    "title": _to_text(entry.get("title")) or "待处理事项",
                    "description": _to_text(entry.get("hint")) or "进入场景继续处理业务",
                    "status": "urgent" if _is_urgent_capability(_to_text(entry.get("title")), entry_key) else "normal",
                    "tone": "danger" if _is_urgent_capability(_to_text(entry.get("title")), entry_key) else "info",
                    "progress": "pending",
                    "ready": True,
                    "entry_key": entry_key,
                    "scene_key": _to_text(entry.get("scene_key")),
                    "route": _to_text(entry.get("route")),
                    "menu_id": _to_int(entry.get("menu_id")),
                    "action_id": _to_int(entry.get("action_id")),
                    "source": "capability_fallback",
                    "source_detail": "capability_template",
                }
            )
            if len(actions) >= 4:
                break

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
        "pm": ["todo_list_today", "risk_alert_panel", "metric_row_core", "progress_summary_ops"],
        "finance": ["todo_list_today", "risk_alert_panel", "progress_summary_ops", "metric_row_core"],
        "owner": ["todo_list_today", "risk_alert_panel", "metric_row_core", "progress_summary_ops"],
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
        "pm": ["today_focus", "analysis", "quick_entries", "hero"],
        "finance": ["today_focus", "analysis", "quick_entries", "hero"],
        "owner": ["today_focus", "analysis", "quick_entries", "hero"],
    }
    return {
        "audience": audience,
        "priority_model": priority_model,
        "mobile_priority": mobile_priority_map.get(role, ["today_focus", "analysis", "quick_entries", "hero"]),
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
    zones: List[Dict[str, Any]] = [
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

    role_zone_order: Dict[str, List[str]] = {
        "pm": ["today_focus", "analysis", "quick_entries", "hero"],
        "finance": ["analysis", "today_focus", "quick_entries", "hero"],
        "owner": ["analysis", "today_focus", "hero", "quick_entries"],
    }
    preferred_order = role_zone_order.get(_to_text(role_code), role_zone_order["owner"])
    max_priority = 100
    priority_step = 10
    priority_map = {key: max_priority - (idx * priority_step) for idx, key in enumerate(preferred_order)}

    for zone in zones:
        zone_key = _to_text(zone.get("key"))
        if zone_key in priority_map:
            zone["priority"] = priority_map[zone_key]

    return zones
