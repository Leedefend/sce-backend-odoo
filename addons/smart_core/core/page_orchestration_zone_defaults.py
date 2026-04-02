# -*- coding: utf-8 -*-
from __future__ import annotations

from typing import Any, Dict


def to_text(value: Any) -> str:
    return str(value or "").strip()


def build_default_zone_from_tag(tag: str) -> Dict[str, str]:
    normalized = to_text(tag).lower()
    if normalized == "header":
        return {"key": "hero", "title": "页面概览", "zone_type": "hero", "display_mode": "stack"}
    if normalized == "details":
        return {"key": "supporting", "title": "重点信息", "zone_type": "supporting", "display_mode": "accordion"}
    if normalized == "div":
        return {"key": "secondary", "title": "补充信息", "zone_type": "secondary", "display_mode": "flow"}
    return {"key": "primary", "title": "主要内容", "zone_type": "primary", "display_mode": "stack"}


def build_default_zone_for_section(page_key: str, section_key: str, tag: str) -> Dict[str, str]:
    page = to_text(page_key).lower()
    section = to_text(section_key).lower()
    if page == "my_work":
        if section == "hero":
            return {"key": "hero", "title": "", "description": "", "zone_type": "hero", "display_mode": "stack"}
        if section == "todo_focus":
            return {
                "key": "primary",
                "title": "待处理事项",
                "description": "优先处理需要你推进的任务和执行事项。",
                "zone_type": "primary",
                "display_mode": "stack",
            }
        if section == "retry_panel":
            return {
                "key": "supporting",
                "title": "失败处理",
                "description": "仅在批量处理失败时显示，便于重试和定位问题。",
                "zone_type": "supporting",
                "display_mode": "accordion",
            }
        if section == "list_main":
            return {
                "key": "secondary",
                "title": "事项清单",
                "description": "按筛选条件查看全部待处理任务和执行事项。",
                "zone_type": "secondary",
                "display_mode": "stack",
            }
    payload = build_default_zone_from_tag(tag)
    payload["description"] = ""
    return payload


def build_default_block_title(page_key: str, section_key: str) -> str:
    page = to_text(page_key).lower()
    section = to_text(section_key).lower()
    if page == "my_work":
        mapping = {
            "hero": "",
            "todo_focus": "待处理事项",
            "retry_panel": "失败处理",
            "list_main": "事项清单",
        }
        if section in mapping:
            return mapping[section]
    generic_mapping = {
        "hero": "页面概览",
        "todo_focus": "待处理事项",
        "retry_panel": "失败处理",
        "list_main": "事项清单",
    }
    if section in generic_mapping:
        return generic_mapping[section]
    return to_text(section_key)
