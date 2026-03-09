# -*- coding: utf-8 -*-
from __future__ import annotations

from collections import Counter
from typing import Any, Dict, Iterable, List
from urllib.parse import parse_qs, urlparse

from odoo import fields


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

    return {
        "schema_version": "v1",
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
                "delta": "能力可用面",
                "hint": "可直接进入并处理业务的能力数量。",
            },
            {
                "key": "capability.locked",
                "label": "受限能力",
                "value": str(locked_count),
                "level": _metric_level(locked_count, 1, 4),
                "delta": "待开通项",
                "hint": "受权限或策略影响暂不可用的能力数量。",
            },
            {
                "key": "capability.preview",
                "label": "预览能力",
                "value": str(preview_count),
                "level": _metric_level(preview_count, 1, 4),
                "delta": "待建设项",
                "hint": "已在契约注册但尚未正式开放的能力数量。",
            },
            {
                "key": "scene.count",
                "label": "可见场景数",
                "value": str(scene_count),
                "level": _metric_level(scene_count, 3, 20),
                "delta": "场景覆盖",
                "hint": "当前角色可访问的场景数量。",
            },
            {
                "key": "nav.count",
                "label": "可见导航节点",
                "value": str(nav_count),
                "level": _metric_level(nav_count, 3, 20),
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
        },
        "advice": _build_advice_items(locked_caps),
    }
