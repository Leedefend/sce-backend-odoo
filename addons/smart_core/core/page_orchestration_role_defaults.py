# -*- coding: utf-8 -*-
from __future__ import annotations

from typing import Any, Dict, List


def to_text(value: Any) -> str:
    return str(value or "").strip()


def build_default_role_section_policy(role_code: str) -> Dict[str, Dict[str, list[str]]]:
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
    return policies.get(to_text(role_code).lower(), {})


def build_default_role_zone_order(role_code: str, page_type: str, page_key: str = "") -> List[str]:
    role = to_text(role_code).lower()
    ptype = to_text(page_type).lower()
    page = to_text(page_key).lower()
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


def build_default_role_focus_sections(role_code: str, page_key: str) -> List[str]:
    role = to_text(role_code).lower()
    page = to_text(page_key).lower()
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
