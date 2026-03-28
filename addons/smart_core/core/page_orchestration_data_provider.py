# -*- coding: utf-8 -*-
from __future__ import annotations

from typing import Any, Dict

from .page_orchestration_defaults import (
    build_default_page_actions as resolve_default_page_actions,
    build_default_page_audience,
    build_default_page_type,
    to_text,
)
from .page_orchestration_action_defaults import (
    build_default_action_templates,
    build_default_action_templates_for_page,
)
from .page_orchestration_role_defaults import (
    build_default_role_focus_sections,
    build_default_role_section_policy,
    build_default_role_zone_order,
)
from .page_orchestration_zone_defaults import (
    build_default_block_title,
    build_default_zone_for_section,
    build_default_zone_from_tag,
)


def _to_text(value: Any) -> str:
    return to_text(value)


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
    return build_default_zone_from_tag(tag)


def build_zone_for_section(page_key: str, section_key: str, tag: str) -> Dict[str, str]:
    return build_default_zone_for_section(page_key, section_key, tag)


def build_block_title(page_key: str, section_key: str) -> str:
    return build_default_block_title(page_key, section_key)


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
    return build_default_action_templates(section_key)


def build_action_templates_for_page(page_key: str, section_key: str) -> list[Dict[str, Any]]:
    return build_default_action_templates_for_page(page_key, section_key)


def build_page_type(page_key: str) -> str:
    return build_default_page_type(page_key)


def build_page_audience(page_key: str) -> list[str]:
    return build_default_page_audience(page_key)


def build_default_page_actions(page_key: str) -> list[Dict[str, Any]]:
    return resolve_default_page_actions(page_key)


def build_role_section_policy(role_code: str) -> Dict[str, Dict[str, list[str]]]:
    return build_default_role_section_policy(role_code)


def build_role_zone_order(role_code: str, page_type: str, page_key: str = "") -> list[str]:
    return build_default_role_zone_order(role_code, page_type, page_key)


def build_role_focus_sections(role_code: str, page_key: str) -> list[str]:
    return build_default_role_focus_sections(role_code, page_key)
