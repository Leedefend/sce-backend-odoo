# -*- coding: utf-8 -*-
from __future__ import annotations

from typing import Any

from odoo.addons.smart_core.core.page_contracts_builder import build_page_contracts


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
        pages[page_key] = page
    payload["pages"] = pages
    return payload


def build_runtime_page_contract(page_key: str, data: dict[str, Any]) -> dict[str, Any]:
    pages = build_runtime_page_contracts(data).get("pages")
    if not isinstance(pages, dict):
        return {}
    page = pages.get(page_key)
    return page if isinstance(page, dict) else {}
