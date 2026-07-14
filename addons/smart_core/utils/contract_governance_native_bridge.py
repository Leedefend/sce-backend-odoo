# -*- coding: utf-8 -*-
from __future__ import annotations

import importlib.util
from pathlib import Path
from typing import Any

try:
    from .contract_governance_registry import _USER_SURFACE_ACTION_MAX
except ImportError:
    spec = importlib.util.spec_from_file_location(
        "contract_governance_registry",
        Path(__file__).with_name("contract_governance_registry.py"),
    )
    if spec is None or spec.loader is None:
        raise
    registry = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(registry)
    _USER_SURFACE_ACTION_MAX = registry._USER_SURFACE_ACTION_MAX


def _safe_text(value: Any, fallback: str = "") -> str:
    text = str(value or "").strip()
    if text.lower() in {"undefined", "null"}:
        text = ""
    return text or fallback


def _safe_lower(value: Any) -> str:
    return _safe_text(value).lower()


def _as_dict(value: Any) -> dict:
    return dict(value) if isinstance(value, dict) else {}


def _deep_clone_json_like(obj: Any) -> Any:
    if isinstance(obj, dict):
        return {k: _deep_clone_json_like(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_deep_clone_json_like(v) for v in obj]
    return obj


def normalize_native_view_contract_surface(data: dict) -> None:
    parser_contract = _as_dict(data.get("parser_contract"))
    if parser_contract:
        parser_contract.setdefault("layout", _as_dict(parser_contract.get("layout")))
        contract_version = _safe_text(data.get("contract_version")) or "native_view.v1"
        parser_contract.setdefault("contract_version", contract_version)
        data["parser_contract"] = parser_contract

    view_semantics = _as_dict(data.get("view_semantics"))
    if view_semantics:
        view_semantics.setdefault("kind", "view_semantics")
        view_semantics["capability_flags"] = _as_dict(view_semantics.get("capability_flags"))
        view_semantics["semantic_meta"] = _as_dict(view_semantics.get("semantic_meta"))
        data["view_semantics"] = view_semantics

    native_view = _as_dict(data.get("native_view"))
    if native_view:
        native_view["views"] = _as_dict(native_view.get("views"))
        native_view["search"] = _as_dict(native_view.get("search"))
        native_view["toolbar"] = _as_dict(native_view.get("toolbar"))
        data["native_view"] = native_view


def normalize_scene_semantic_surface(data: dict) -> None:
    def _normalize_page_surface(page_payload: dict) -> dict:
        page = _as_dict(page_payload)
        surface = _as_dict(page.get("surface"))
        if surface:
            surface["semantic_view"] = _as_dict(surface.get("semantic_view"))
            surface["semantic_page"] = _as_dict(surface.get("semantic_page"))
            page["surface"] = surface
        return page

    def _normalize_parser_semantic_surface(surface_payload: dict) -> dict:
        surface = _as_dict(surface_payload)
        if not surface:
            return {}
        parser_contract = _as_dict(surface.get("parser_contract"))
        if parser_contract:
            parser_contract.setdefault("layout", _as_dict(parser_contract.get("layout")))
            parser_contract.setdefault(
                "contract_version",
                _safe_text(data.get("contract_version")) or "native_view.v1",
            )
            surface["parser_contract"] = parser_contract
        view_semantics = _as_dict(surface.get("view_semantics"))
        if view_semantics:
            view_semantics.setdefault("kind", "view_semantics")
            view_semantics["capability_flags"] = _as_dict(view_semantics.get("capability_flags"))
            view_semantics["semantic_meta"] = _as_dict(view_semantics.get("semantic_meta"))
            surface["view_semantics"] = view_semantics
        native_view = _as_dict(surface.get("native_view"))
        if native_view:
            native_view["views"] = _as_dict(native_view.get("views"))
            native_view["search"] = _as_dict(native_view.get("search"))
            native_view["toolbar"] = _as_dict(native_view.get("toolbar"))
            surface["native_view"] = native_view
        semantic_page = _as_dict(surface.get("semantic_page"))
        if semantic_page:
            surface["semantic_page"] = semantic_page
        return surface

    scene_contract_standard = _as_dict(data.get("scene_contract_standard_v1"))
    if scene_contract_standard:
        scene_contract_standard["page"] = _normalize_page_surface(scene_contract_standard.get("page"))
        governance = _as_dict(scene_contract_standard.get("governance"))
        parser_surface = _normalize_parser_semantic_surface(governance.get("parser_semantic_surface"))
        if parser_surface:
            governance["parser_semantic_surface"] = parser_surface
        scene_contract_standard["governance"] = governance
        data["scene_contract_standard_v1"] = scene_contract_standard

    scene_contract_v1 = _as_dict(data.get("scene_contract_v1"))
    if scene_contract_v1:
        scene_contract_v1["page"] = _normalize_page_surface(scene_contract_v1.get("page"))
        diagnostics = _as_dict(scene_contract_v1.get("diagnostics"))
        parser_surface = _normalize_parser_semantic_surface(diagnostics.get("parser_semantic_surface"))
        if parser_surface:
            diagnostics["parser_semantic_surface"] = parser_surface
        scene_contract_v1["diagnostics"] = diagnostics
        data["scene_contract_v1"] = scene_contract_v1

    semantic_runtime = _as_dict(data.get("semantic_runtime"))
    if semantic_runtime:
        semantic_runtime["semantic_view"] = _as_dict(semantic_runtime.get("semantic_view"))
        semantic_runtime["semantic_page"] = _as_dict(semantic_runtime.get("semantic_page"))
        parser_surface = _normalize_parser_semantic_surface(semantic_runtime.get("parser_semantic_surface"))
        if parser_surface:
            semantic_runtime["parser_semantic_surface"] = parser_surface
        data["semantic_runtime"] = semantic_runtime

    released_scene_surface = _as_dict(data.get("released_scene_semantic_surface"))
    if released_scene_surface:
        released_scene_surface["page_surface"] = _normalize_page_surface({"surface": released_scene_surface.get("page_surface")}).get("surface") or {}
        parser_surface = _normalize_parser_semantic_surface(released_scene_surface.get("parser_semantic_surface"))
        if parser_surface:
            released_scene_surface["parser_semantic_surface"] = parser_surface
        data["released_scene_semantic_surface"] = released_scene_surface


def search_surface_from_contract(data: dict) -> dict:
    search = _as_dict(data.get("search"))
    if not search:
        return {}
    surface: dict[str, Any] = {
        "owner_layer": "scene_orchestration",
        "source": "contract_governance.search_surface",
    }
    for source_key, target_key in (
        ("filters", "filters"),
        ("fields", "fields"),
        ("group_by", "group_by"),
        ("groupBy", "group_by"),
        ("searchpanel", "searchpanel"),
        ("search_panel", "searchpanel"),
        ("searchPanel", "searchpanel"),
        ("native_search_menu", "native_search_menu"),
        ("nativeSearchMenu", "native_search_menu"),
        ("default_state", "default_state"),
    ):
        value = search.get(source_key)
        if isinstance(value, (list, dict)) and value:
            surface[target_key] = _deep_clone_json_like(value)
    interaction_model = _safe_text(search.get("interaction_model") or search.get("interactionModel"))
    if interaction_model:
        surface["interaction_model"] = interaction_model
    default_sort = _safe_text(search.get("default_sort") or search.get("defaultSort") or data.get("default_sort"))
    if default_sort:
        surface["default_sort"] = default_sort
    mode = _safe_text(search.get("mode"))
    if mode:
        surface["mode"] = mode
    elif any(surface.get(key) for key in ("filters", "group_by", "searchpanel")):
        surface["mode"] = "faceted"
    return surface if len(surface) > 2 else {}


def scene_actions_from_contract(data: dict) -> dict:
    semantic_page = _as_dict(data.get("semantic_page"))
    semantic_actions = _as_dict(semantic_page.get("actions"))
    out: dict[str, Any] = {}

    header_actions = semantic_actions.get("header_actions")
    record_actions = semantic_actions.get("record_actions")
    toolbar_actions = semantic_actions.get("toolbar_actions")
    if isinstance(header_actions, list) and header_actions:
        out["primary_actions"] = _deep_clone_json_like(header_actions)
    if isinstance(record_actions, list) and record_actions:
        out["contextual_actions"] = _deep_clone_json_like(record_actions)
    if isinstance(toolbar_actions, list) and toolbar_actions:
        out["secondary_actions"] = _deep_clone_json_like(toolbar_actions)

    if not out:
        grouped_rows = data.get("action_groups")
        if isinstance(grouped_rows, list):
            for group in grouped_rows:
                if not isinstance(group, dict):
                    continue
                key = _safe_lower(group.get("key"))
                rows = group.get("actions")
                if not isinstance(rows, list) or not rows:
                    continue
                if key in {"basic", "primary", "workflow"} and "primary_actions" not in out:
                    out["primary_actions"] = _deep_clone_json_like(rows)
                elif key in {"drilldown", "record", "contextual"} and "contextual_actions" not in out:
                    out["contextual_actions"] = _deep_clone_json_like(rows)
                elif "secondary_actions" not in out:
                    out["secondary_actions"] = _deep_clone_json_like(rows)

    if not out:
        rows = data.get("buttons")
        if isinstance(rows, list) and rows:
            out["primary_actions"] = _deep_clone_json_like(rows[:_USER_SURFACE_ACTION_MAX])

    if out:
        out["owner_layer"] = "scene_orchestration"
        out["source"] = "contract_governance.action_surface"
    return out


def ensure_scene_contract_v1_envelope(data: dict) -> None:
    semantic_page = _as_dict(data.get("semantic_page"))
    list_profile = _as_dict(data.get("list_profile"))
    if list_profile and not _as_dict(semantic_page.get("list_semantics")):
        list_semantics = {
            "owner_layer": "scene_orchestration",
            "source": "contract_governance.list_profile_bridge",
            "columns": [
                {"name": _safe_text(name), "label": _safe_text((_as_dict(list_profile.get("column_labels"))).get(_safe_text(name)), _safe_text(name))}
                for name in (list_profile.get("columns") if isinstance(list_profile.get("columns"), list) else [])
                if _safe_text(name)
            ],
            "hidden_columns": [
                _safe_text(name)
                for name in (list_profile.get("hidden_columns") if isinstance(list_profile.get("hidden_columns"), list) else [])
                if _safe_text(name)
            ],
            "row_primary": _safe_text(list_profile.get("row_primary")),
            "row_secondary": _safe_text(list_profile.get("row_secondary")),
            "status_field": _safe_text(list_profile.get("status_field")),
        }
        semantic_page["list_semantics"] = list_semantics

    search_surface = search_surface_from_contract(data)
    actions = scene_actions_from_contract(data)
    if not semantic_page and not search_surface and not actions:
        return

    scene_contract = _as_dict(data.get("scene_contract_v1"))
    scene_contract["contract_version"] = "v1"
    scene_contract.setdefault("owner_layer", "scene_orchestration")
    scene_contract.setdefault("source", "ui.contract.delivery_surface")
    if semantic_page:
        current_semantic_page = _as_dict(scene_contract.get("semantic_page"))
        current_semantic_page.update(_deep_clone_json_like(semantic_page))
        scene_contract["semantic_page"] = current_semantic_page
    if search_surface and not _as_dict(scene_contract.get("search_surface")):
        scene_contract["search_surface"] = search_surface
    if actions:
        current_actions = _as_dict(scene_contract.get("actions"))
        for key, value in actions.items():
            current_actions.setdefault(key, value)
        scene_contract["actions"] = current_actions
    diagnostics = _as_dict(scene_contract.get("diagnostics"))
    diagnostics.setdefault("scene_contract_supply", "ui_contract_governance_bridge")
    diagnostics.setdefault("scene_contract_supply_owner_layer", "scene_orchestration")
    scene_contract["diagnostics"] = diagnostics
    data["scene_contract_v1"] = scene_contract
