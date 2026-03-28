# -*- coding: utf-8 -*-
from __future__ import annotations

from typing import Any, Dict, List


def to_text(value: Any) -> str:
    return str(value or "").strip()


def build_default_action_templates(section_key: str) -> List[Dict[str, Any]]:
    key = to_text(section_key).lower()
    if "risk" in key:
        return [{"key": "open_workspace_overview", "label": "查看重点事项", "intent": "ui.contract"}]
    if any(token in key for token in ("approval", "todo", "next_actions")):
        return [{"key": "open_my_work", "label": "进入工作区", "intent": "ui.contract"}]
    if any(token in key for token in ("filter", "group", "slice")):
        return [{"key": "apply_filters", "label": "应用筛选", "intent": "ui.contract"}]
    if any(token in key for token in ("table", "list", "records")):
        return [{"key": "open_list", "label": "查看明细", "intent": "ui.contract"}]
    return []


def build_default_action_templates_for_page(page_key: str, section_key: str) -> List[Dict[str, Any]]:
    page = to_text(page_key).lower()
    section = to_text(section_key).lower()
    if page == "my_work":
        if section == "todo_focus":
            return [{"key": "open_list", "label": "查看全部事项", "intent": "ui.contract"}]
        if section in {"hero", "retry_panel", "list_main"}:
            return []
    return build_default_action_templates(section_key)
