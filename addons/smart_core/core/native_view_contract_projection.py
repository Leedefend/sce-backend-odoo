# -*- coding: utf-8 -*-
"""Shared helpers for projecting primary native-view semantics into canonical contract fields."""

from __future__ import annotations

from typing import Any, Dict


PREFERRED_VIEW_ORDER = (
    "form",
    "tree",
    "kanban",
    "search",
    "pivot",
    "graph",
    "calendar",
    "gantt",
    "activity",
    "dashboard",
)


def resolve_primary_view_type(
    requested_view_type: Any,
    head: Dict[str, Any] | None,
    views: Dict[str, Any] | None,
) -> str:
    if isinstance(requested_view_type, str) and requested_view_type.strip():
        return requested_view_type.split(",")[0].strip()
    if isinstance(requested_view_type, (list, tuple)):
        for item in requested_view_type:
            key = str(item or "").strip()
            if key:
                return key
    head_view_type = str((head or {}).get("view_type") or "").strip()
    if head_view_type:
        return head_view_type
    for candidate in PREFERRED_VIEW_ORDER:
        if candidate in (views or {}):
            return candidate
    return "form"


def inject_primary_view_projection(data: Dict[str, Any] | None, requested_view_type: Any = None) -> Dict[str, Any]:
    if not isinstance(data, dict):
        return {}

    views = data.get("views") if isinstance(data.get("views"), dict) else {}
    head = data.get("head") if isinstance(data.get("head"), dict) else {}
    primary_view_type = resolve_primary_view_type(requested_view_type, head, views)
    primary_view = views.get(primary_view_type) if isinstance(views.get(primary_view_type), dict) else {}

    if "layout" not in data and primary_view.get("layout") is not None:
        data["layout"] = primary_view.get("layout")
    parser_contract = primary_view.get("parser_contract") if isinstance(primary_view.get("parser_contract"), dict) else None
    if "parser_contract" not in data:
        if parser_contract:
            data["parser_contract"] = parser_contract
        elif primary_view.get("layout") is not None:
            data["parser_contract"] = {
                "contract_version": str(data.get("contract_version") or "native_view.v1"),
                "view_type": primary_view_type,
                "layout": {"kind": primary_view_type},
                "projection_source": "legacy_primary_view_fallback",
            }

    view_semantics = primary_view.get("view_semantics") if isinstance(primary_view.get("view_semantics"), dict) else None
    if "view_semantics" not in data:
        if view_semantics:
            data["view_semantics"] = view_semantics
        elif primary_view.get("layout") is not None:
            data["view_semantics"] = {
                "kind": "view_semantics",
                "source_view": primary_view_type,
                "capability_flags": {"has_layout": True},
                "semantic_meta": {"projection_source": "legacy_primary_view_fallback"},
            }
    if "model" not in data and head.get("model"):
        data["model"] = head.get("model")
    if "view_type" not in data and primary_view_type:
        data["view_type"] = primary_view_type
    if "permissions" not in data and isinstance(data.get("permissions"), dict):
        data["permissions"] = data.get("permissions")
    if "fields" not in data and isinstance(data.get("fields"), dict):
        data["fields"] = data.get("fields")
    if "native_view" not in data and isinstance(data.get("native_view"), dict):
        data["native_view"] = data.get("native_view")
    return data
