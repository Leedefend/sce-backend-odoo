# -*- coding: utf-8 -*-
from __future__ import annotations

from typing import Any

from odoo.addons.smart_core.core.page_contracts_builder import build_page_contracts
from odoo.addons.smart_core.core.runtime_page_parser_semantic_bridge import (
    apply_runtime_page_parser_semantic_bridge,
)
from odoo.addons.smart_core.core.runtime_page_semantic_orchestration_bridge import (
    apply_runtime_page_semantic_orchestration_bridge,
)
from odoo.addons.smart_core.core.scene_contract_builder import (
    build_release_surface_scene_contract_from_page_contract,
)

_LEAKED_TECHNICAL_TITLES = {
    "页面头部",
    "主体内容",
    "辅助信息",
    "扩展信息",
    "hero",
    "todo_focus",
    "list_main",
    "my_work-primary",
}

_SEMANTIC_TITLE_BY_KEY = {
    "hero": "页面概览",
    "primary": "待处理事项",
    "supporting": "重点信息",
    "secondary": "事项清单",
    "todo_focus": "待处理事项",
    "retry_panel": "失败处理",
    "list_main": "事项清单",
}


def _resolve_role_source_code(data: dict[str, Any]) -> str:
    role_surface = data.get("role_surface") if isinstance(data.get("role_surface"), dict) else {}
    role_code = str(role_surface.get("role_code") or "").strip().lower()
    return role_code or "owner"


def mirror_workspace_home_role_context(data: dict[str, Any]) -> None:
    if not isinstance(data, dict):
        return
    role_code = _resolve_role_source_code(data)
    workspace_home = data.get("workspace_home") if isinstance(data.get("workspace_home"), dict) else None
    if not isinstance(workspace_home, dict):
        return
    record = workspace_home.get("record") if isinstance(workspace_home.get("record"), dict) else {}
    hero = record.get("hero") if isinstance(record.get("hero"), dict) else {}
    hero["role_code"] = role_code
    record["hero"] = hero
    workspace_home["record"] = record

    page_orchestration_v1 = (
        workspace_home.get("page_orchestration_v1")
        if isinstance(workspace_home.get("page_orchestration_v1"), dict)
        else {}
    )
    page = page_orchestration_v1.get("page") if isinstance(page_orchestration_v1.get("page"), dict) else {}
    context = page.get("context") if isinstance(page.get("context"), dict) else {}
    context["role_code"] = role_code
    page["context"] = context
    page_orchestration_v1["page"] = page
    workspace_home["page_orchestration_v1"] = page_orchestration_v1


def _to_text(value: Any) -> str:
    return str(value or "").strip()


def _semantic_title_for(raw_title: str, key: str, fallback: str) -> str:
    if raw_title and raw_title not in _LEAKED_TECHNICAL_TITLES:
        return raw_title
    if key in _SEMANTIC_TITLE_BY_KEY:
        return _SEMANTIC_TITLE_BY_KEY[key]
    return fallback


def _sanitize_page_orchestration_titles(page: dict[str, Any]) -> dict[str, Any]:
    orchestration = page.get("page_orchestration_v1") if isinstance(page.get("page_orchestration_v1"), dict) else {}
    zones = orchestration.get("zones") if isinstance(orchestration.get("zones"), list) else []
    sanitized_zones: list[dict[str, Any]] = []
    for zone in zones:
        if not isinstance(zone, dict):
            continue
        next_zone = dict(zone)
        zone_key = _to_text(next_zone.get("key")).lower()
        zone_title = _to_text(next_zone.get("title"))
        next_zone["title"] = _semantic_title_for(zone_title, zone_key, "信息区")
        zone_desc = _to_text(next_zone.get("description"))
        if zone_desc in _LEAKED_TECHNICAL_TITLES:
            next_zone["description"] = ""
        blocks = next_zone.get("blocks") if isinstance(next_zone.get("blocks"), list) else []
        sanitized_blocks: list[dict[str, Any]] = []
        for block in blocks:
            if not isinstance(block, dict):
                continue
            next_block = dict(block)
            block_key = _to_text(next_block.get("key")).lower() or _to_text(next_block.get("section_key")).lower()
            block_title = _to_text(next_block.get("title"))
            next_block["title"] = _semantic_title_for(block_title, block_key, "信息项")
            sanitized_blocks.append(next_block)
        next_zone["blocks"] = sanitized_blocks
        sanitized_zones.append(next_zone)
    orchestration["zones"] = sanitized_zones
    page["page_orchestration_v1"] = orchestration
    return page


def build_runtime_page_contracts(data: dict[str, Any]) -> dict[str, Any]:
    payload = build_page_contracts(data)
    role_code = _resolve_role_source_code(data)
    pages = payload.get("pages") if isinstance(payload.get("pages"), dict) else {}
    for page_key, page in list(pages.items()):
        if not isinstance(page, dict):
            continue
        orchestration = page.get("page_orchestration_v1") if isinstance(page.get("page_orchestration_v1"), dict) else {}
        meta = orchestration.get("meta") if isinstance(orchestration.get("meta"), dict) else {}
        page_payload = orchestration.get("page") if isinstance(orchestration.get("page"), dict) else {}
        context = page_payload.get("context") if isinstance(page_payload.get("context"), dict) else {}
        context["role_code"] = role_code
        page_payload["context"] = context
        orchestration["page"] = page_payload
        meta["role_source_code"] = role_code
        orchestration["meta"] = meta
        page["page_orchestration_v1"] = orchestration
        page = apply_runtime_page_parser_semantic_bridge(page, page_key=page_key)
        page = apply_runtime_page_semantic_orchestration_bridge(page)
        page = _sanitize_page_orchestration_titles(page)
        if page_key == "my_work":
            page["scene_contract_standard_v1"] = build_release_surface_scene_contract_from_page_contract(
                page,
                scene_key="my_work.workspace",
                title="我的工作",
                product_key="my_work",
                capability="delivery.my_work.workspace",
                route="/my-work",
                diagnostics_ref="page.contract:my_work",
            )
        pages[page_key] = page
    payload["pages"] = pages
    return payload


def build_runtime_page_contract(page_key: str, data: dict[str, Any]) -> dict[str, Any]:
    pages = build_runtime_page_contracts(data).get("pages")
    if not isinstance(pages, dict):
        return {}
    page = pages.get(page_key)
    return page if isinstance(page, dict) else {}
