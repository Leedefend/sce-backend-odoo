# -*- coding: utf-8 -*-
from __future__ import annotations

from typing import Any, Dict


def _to_text(value: Any) -> str:
    return str(value or "").strip()


def _data_source_key(section_key: str) -> str:
    import re

    token = re.sub(r"[^a-z0-9_]+", "_", _to_text(section_key).lower())
    token = re.sub(r"_+", "_", token).strip("_")
    if not token:
        token = "section"
    return f"ds_section_{token}"


def build_base_data_sources() -> Dict[str, Dict[str, Any]]:
    return {
        "ds_sections": {"source_type": "static", "provider": "page_contract.sections", "section_keys": ["_all"]},
    }


def build_section_data_source(page_key: str, section_key: str, section_tag: str) -> Dict[str, Any]:
    return {
        "source_type": "scene_context",
        "provider": "page_contract.section",
        "page_key": _to_text(page_key),
        "section_key": _to_text(section_key),
        "section_tag": _to_text(section_tag).lower() or "section",
        "section_keys": [_to_text(section_key)],
    }


def build_section_data_source_key(section_key: str) -> str:
    return _data_source_key(section_key)


def build_zone_from_tag(tag: str) -> Dict[str, str]:
    normalized = _to_text(tag).lower()
    if normalized == "header":
        return {"key": "hero", "title": "页面头部", "zone_type": "hero", "display_mode": "stack"}
    if normalized == "details":
        return {"key": "supporting", "title": "辅助信息", "zone_type": "supporting", "display_mode": "accordion"}
    if normalized == "div":
        return {"key": "secondary", "title": "扩展信息", "zone_type": "secondary", "display_mode": "flow"}
    return {"key": "primary", "title": "主体内容", "zone_type": "primary", "display_mode": "stack"}


def build_semantic_from_section(page_key: str, section_key: str, tag: str) -> Dict[str, Any]:
    key = _to_text(section_key).lower()
    page = _to_text(page_key).lower()
    normalized_tag = _to_text(tag).lower()

    if normalized_tag == "header":
        return {"block_type": "record_summary", "tone": "info", "progress": "running", "importance": "high"}
    if normalized_tag == "details":
        return {"block_type": "accordion_group", "tone": "neutral", "progress": "completed", "importance": "medium"}
    if normalized_tag == "div":
        return {"block_type": "activity_feed", "tone": "neutral", "progress": "running", "importance": "medium"}

    if any(token in key for token in ("error", "forbidden", "risk", "warning", "blocked")):
        return {"block_type": "alert_panel", "tone": "danger", "progress": "blocked", "importance": "high"}
    if any(token in key for token in ("loading", "pending", "status_loading")):
        return {"block_type": "progress_summary", "tone": "info", "progress": "running", "importance": "medium"}
    if any(token in key for token in ("summary", "kpi", "metric", "cards", "hero", "project_summary")):
        return {"block_type": "metric_row", "tone": "info", "progress": "running", "importance": "high"}
    if any(token in key for token in ("todo", "approval", "quick_actions", "next_actions")):
        return {"block_type": "todo_list", "tone": "warning", "progress": "pending", "importance": "high"}
    if any(token in key for token in ("filter", "group", "slice", "preset", "tiles")):
        return {"block_type": "entry_grid", "tone": "neutral", "progress": "completed", "importance": "medium"}
    if any(token in key for token in ("table", "list", "daily", "top", "visibility")):
        return {"block_type": "activity_feed", "tone": "neutral", "progress": "running", "importance": "medium"}
    if page in {"login", "menu", "placeholder"}:
        return {"block_type": "record_summary", "tone": "neutral", "progress": "running", "importance": "medium"}
    return {"block_type": "record_summary", "tone": "neutral", "progress": "running", "importance": "medium"}


def build_action_templates(section_key: str) -> list[Dict[str, Any]]:
    key = _to_text(section_key).lower()
    if "risk" in key:
        return [{"key": "open_workspace_overview", "label": "查看重点事项", "intent": "ui.contract"}]
    if any(token in key for token in ("approval", "todo", "next_actions")):
        return [{"key": "open_my_work", "label": "进入工作区", "intent": "ui.contract"}]
    if any(token in key for token in ("filter", "group", "slice")):
        return [{"key": "apply_filters", "label": "应用筛选", "intent": "ui.contract"}]
    if any(token in key for token in ("table", "list", "records")):
        return [{"key": "open_list", "label": "查看明细", "intent": "ui.contract"}]
    return []


def build_page_type(page_key: str) -> str:
    key = _to_text(page_key).lower()
    if key in {"home", "workbench"}:
        return "workspace"
    if key in {"login", "menu", "placeholder"}:
        return "entry_hub"
    if key in {"my_work"}:
        return "approval"
    if key in {"scene_health", "usage_analytics"}:
        return "monitor"
    if key in {"action", "record", "scene"}:
        return "detail"
    return "list"


def build_page_audience(page_key: str) -> list[str]:
    key = _to_text(page_key).lower()
    if key in {"usage_analytics", "scene_health"}:
        return ["executive", "owner", "internal_user"]
    if key in {"my_work", "action", "record"}:
        return ["internal_user", "owner", "reviewer"]
    if key in {"home", "workbench"}:
        return ["internal_user", "owner", "executive"]
    return ["generic_user"]


def build_default_page_actions(page_key: str) -> list[Dict[str, Any]]:
    key = _to_text(page_key).lower()
    if key == "home":
        return [
            {"key": "open_my_work", "label": "我的工作", "intent": "ui.contract"},
            {"key": "open_usage_analytics", "label": "使用分析", "intent": "ui.contract"},
        ]
    if key == "my_work":
        return [
            {"key": "open_workbench", "label": "返回工作台", "intent": "ui.contract"},
            {"key": "open_workspace_overview", "label": "查看工作概览", "intent": "ui.contract"},
            {"key": "refresh_page", "label": "刷新", "intent": "api.data"},
        ]
    if key == "workbench":
        return [
            {"key": "open_workbench", "label": "返回工作台", "intent": "ui.contract"},
            {"key": "open_menu", "label": "打开菜单", "intent": "ui.contract"},
            {"key": "refresh_page", "label": "刷新", "intent": "api.data"},
        ]
    if key in {"scene_health", "usage_analytics", "scene_packages"}:
        return [
            {"key": "open_workbench", "label": "返回工作台", "intent": "ui.contract"},
            {"key": "refresh_page", "label": "刷新", "intent": "api.data"},
        ]
    if key in {"action", "record", "scene"}:
        return [
            {"key": "open_my_work", "label": "进入工作区", "intent": "ui.contract"},
            {"key": "open_workspace_overview", "label": "查看工作概览", "intent": "ui.contract"},
            {"key": "refresh_page", "label": "刷新", "intent": "api.data"},
        ]
    return [{"key": "refresh_page", "label": "刷新", "intent": "api.data"}]


def build_role_section_policy(role_code: str) -> Dict[str, Dict[str, list[str]]]:
    policies: Dict[str, Dict[str, Dict[str, list[str]]]] = {
        "pm": {
            "usage_analytics": {"disable": ["tables_role_user"]},
            "scene_health": {"disable": ["details_debt"]},
        },
        "finance": {
            "action": {"disable": ["group_view"]},
            "record": {"disable": ["dev_context"]},
        },
        "owner": {
            "workbench": {"disable": ["hud_details"]},
            "action": {"disable": ["advanced_view", "dev_context"]},
            "record": {"disable": ["dev_context"]},
            "scene_health": {"disable": ["details_drift", "details_debt"]},
        },
    }
    return policies.get(_to_text(role_code).lower(), {})


def build_role_zone_order(role_code: str, page_type: str, page_key: str = "") -> list[str]:
    role = _to_text(role_code).lower()
    ptype = _to_text(page_type).lower()
    page = _to_text(page_key).lower()
    if page == "action":
        if role == "finance":
            return ["secondary", "primary", "hero", "supporting"]
        if role == "owner":
            return ["primary", "secondary", "hero", "supporting"]
        return ["primary", "secondary", "hero", "supporting"]
    if ptype == "monitor":
        return ["hero", "secondary", "primary", "supporting"] if role == "finance" else ["hero", "primary", "secondary", "supporting"]
    if ptype == "approval":
        return ["hero", "primary", "supporting", "secondary"] if role == "pm" else ["hero", "secondary", "primary", "supporting"]
    if ptype == "detail":
        return ["hero", "primary", "secondary", "supporting"] if role != "owner" else ["hero", "supporting", "primary", "secondary"]
    return ["hero", "primary", "secondary", "supporting"]


def build_role_focus_sections(role_code: str, page_key: str) -> list[str]:
    role = _to_text(role_code).lower()
    page = _to_text(page_key).lower()
    mapping: Dict[str, Dict[str, list[str]]] = {
        "pm": {
            "workbench": ["status_panel", "tiles"],
            "action": ["quick_actions", "quick_filters"],
            "record": ["project_summary", "next_actions"],
            "my_work": ["todo_focus", "list_main"],
        },
        "finance": {
            "workbench": ["status_panel"],
            "action": ["quick_filters", "group_summary"],
            "record": ["project_summary"],
            "usage_analytics": ["summary_usage", "tables_daily"],
        },
        "owner": {
            "workbench": ["header", "status_panel"],
            "scene_health": ["cards", "governance"],
            "usage_analytics": ["summary_visibility", "tables_top"],
            "action": ["focus_strip"],
        },
    }
    return mapping.get(role, {}).get(page, [])
