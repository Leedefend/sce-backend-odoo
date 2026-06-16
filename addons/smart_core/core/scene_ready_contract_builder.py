# -*- coding: utf-8 -*-
from __future__ import annotations

from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path
from typing import Any, Dict, List
from odoo.addons.smart_core.core.source_authority import build_source_authority_contract
from odoo.addons.smart_core.core.scene_dsl_compiler import scene_compile
from odoo.addons.smart_core.core.scene_ready_entry_semantic_bridge import apply_scene_ready_entry_semantic_bridge
from odoo.addons.smart_core.core.scene_ready_parser_semantic_bridge import apply_scene_ready_parser_semantic_bridge
from odoo.addons.smart_core.core.scene_ready_semantic_orchestration_bridge import (
    apply_scene_ready_semantic_orchestration_bridge,
)
from odoo.addons.smart_core.core.ui_base_contract_adapter import adapt_ui_base_contract

SOURCE_KIND = "scene_ready_contract_projection"
SOURCE_AUTHORITIES = (
    "scene_registry",
    "scene_dsl_contract_compiler",
    "ui_base_contract",
    "scene_provider_registry",
    "scene_ready_semantic_bridges",
)
NO_BUSINESS_FACT_AUTHORITY = True


def source_authority_contract() -> Dict[str, Any]:
    return build_source_authority_contract(
        kind=SOURCE_KIND,
        authorities=SOURCE_AUTHORITIES,
        no_business_fact_authority=NO_BUSINESS_FACT_AUTHORITY,
        scene_runtime_contract_only=True,
    )


def _text(value: Any) -> str:
    return str(value or "").strip()


def _to_int(value: Any) -> int:
    try:
        return int(value or 0)
    except Exception:
        return 0


def _as_dict(value: Any) -> Dict[str, Any]:
    return dict(value) if isinstance(value, dict) else {}


def _as_list(value: Any) -> List[Any]:
    return list(value) if isinstance(value, list) else []


def _scene_key_matches(scene_key: str, *candidates: str) -> bool:
    normalized = _text(scene_key).lower()
    if not normalized:
        return False
    pool = set()
    for candidate in candidates:
        value = _text(candidate).lower()
        if not value:
            continue
        pool.add(value)
        pool.add(value.replace(".", "_"))
        pool.add(value.replace("_", "."))
    return normalized in pool


def _resolve_scene_provider_payload(scene_key: str, runtime_context: Dict[str, Any] | None = None) -> Dict[str, Any]:
    runtime_payload = runtime_context if isinstance(runtime_context, dict) else {}
    try:
        from odoo.addons.smart_scene.core.scene_provider_registry import resolve_scene_provider_path
    except Exception:
        return {}

    provider_path = resolve_scene_provider_path(scene_key, Path(__file__).resolve())
    if not provider_path or not provider_path.exists() or not provider_path.is_file():
        return {}

    spec = spec_from_file_location(
        f"scene_ready_provider_{scene_key.replace('.', '_')}",
        provider_path,
    )
    if spec is None or spec.loader is None:
        return {}
    module = module_from_spec(spec)
    try:
        spec.loader.exec_module(module)
    except Exception:
        return {}

    builder = getattr(module, "build", None)
    if not callable(builder):
        builder = getattr(module, "get_scene_content", None)
    if not callable(builder):
        return {}
    try:
        payload = builder(scene_key=scene_key, runtime=runtime_payload, context={})
    except Exception:
        return {}
    return payload if isinstance(payload, dict) else {}


def _normalize_scene(item: Dict[str, Any]) -> Dict[str, Any]:
    scene_key = _text(item.get("code") or item.get("key"))
    scene_title = _text(item.get("name") or scene_key)
    layout = item.get("layout") if isinstance(item.get("layout"), dict) else {}
    return {
        "key": scene_key,
        "title": scene_title,
        "layout": dict(layout),
    }


def _scene_switch_catalog(rows: List[Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
    catalog: Dict[str, Dict[str, Any]] = {}
    for row in rows or []:
        payload = _as_dict(row)
        scene_key = _text(payload.get("code") or payload.get("key"))
        if not scene_key:
            continue
        target = _as_dict(payload.get("target"))
        catalog[scene_key] = {
            "label": _text(payload.get("name") or payload.get("title") or scene_key),
            "route": _text(target.get("route")) or f"/s/{scene_key}",
        }
    return catalog


def _normalize_actions(item: Dict[str, Any]) -> List[Dict[str, Any]]:
    target = item.get("target") if isinstance(item.get("target"), dict) else {}
    out: List[Dict[str, Any]] = []
    action_id = int(target.get("action_id") or 0)
    menu_id = int(target.get("menu_id") or 0)
    route = _text(target.get("route"))
    if action_id > 0:
        out.append(
            {
                "key": "open_scene_action",
                "label": "打开场景",
                "intent": "ui.contract",
                "target": {
                    "action_id": action_id,
                    "menu_id": menu_id if menu_id > 0 else None,
                },
            }
        )
    if route:
        out.append(
            {
                "key": "open_scene_route",
                "label": "打开路由",
                "intent": "ui.contract",
                "target": {"route": route},
            }
        )
    return out


def _normalize_search_surface(item: Dict[str, Any]) -> Dict[str, Any]:
    list_profile = item.get("list_profile") if isinstance(item.get("list_profile"), dict) else {}
    return {
        "default_sort": _text(item.get("default_sort")),
        "filters": list(item.get("filters") or []),
        "columns": list(list_profile.get("columns") or []),
        "hidden_columns": list(list_profile.get("hidden_columns") or []),
    }


def _normalize_permission_surface(item: Dict[str, Any]) -> Dict[str, Any]:
    access = item.get("access") if isinstance(item.get("access"), dict) else {}
    required = access.get("required_capabilities")
    return {
        "visible": bool(access.get("visible", True)),
        "allowed": bool(access.get("allowed", True)),
        "reason_code": _text(access.get("reason_code")),
        "required_capabilities": list(required) if isinstance(required, list) else [],
    }


def _search_surface_nonempty(payload: Dict[str, Any]) -> bool:
    data = _as_dict(payload)
    return bool(
        _text(data.get("default_sort"))
        or _as_list(data.get("filters"))
        or _as_list(data.get("columns"))
        or _as_list(data.get("hidden_columns"))
        or _as_list(data.get("fields"))
        or _as_list(data.get("group_by"))
    )


def _permission_surface_nonempty(payload: Dict[str, Any]) -> bool:
    data = _as_dict(payload)
    required_capabilities = _as_list(data.get("required_capabilities"))
    return bool(required_capabilities or _text(data.get("reason_code")))


def _workflow_surface_nonempty(payload: Dict[str, Any]) -> bool:
    data = _as_dict(payload)
    return bool(
        _text(data.get("state_field"))
        or _as_list(data.get("states"))
        or _as_list(data.get("transitions"))
    )


def _validation_surface_nonempty(payload: Dict[str, Any]) -> bool:
    data = _as_dict(payload)
    return bool(_as_list(data.get("required_fields")) or _as_dict(data.get("field_rules")))


def _normalize_list_surface(payload: Dict[str, Any]) -> Dict[str, Any]:
    list_surface = payload.get("list_surface") if isinstance(payload.get("list_surface"), dict) else {}
    return dict(list_surface)


def _list_surface_nonempty(payload: Dict[str, Any]) -> bool:
    data = _as_dict(payload)
    return bool(data)


def _normalize_form_surface(payload: Dict[str, Any]) -> Dict[str, Any]:
    form_surface = payload.get("form_surface") if isinstance(payload.get("form_surface"), dict) else {}
    return dict(form_surface)


def _merge_form_surface(compiled_form_surface: Dict[str, Any], seeded_form_surface: Dict[str, Any]) -> Dict[str, Any]:
    merged = dict(_as_dict(seeded_form_surface))
    merged.update(_as_dict(compiled_form_surface))
    return merged


def _form_surface_nonempty(payload: Dict[str, Any]) -> bool:
    data = _as_dict(payload)
    return bool(data)


def _normalize_optimization_composition(payload: Dict[str, Any]) -> Dict[str, Any]:
    composition = payload.get("optimization_composition") if isinstance(payload.get("optimization_composition"), dict) else {}
    return dict(composition)


def _optimization_composition_nonempty(payload: Dict[str, Any]) -> bool:
    return bool(_as_dict(payload))


def _derive_form_surface_from_base_contract(ui_base_contract: Dict[str, Any]) -> Dict[str, Any]:
    contract = _as_dict(ui_base_contract)
    views = _as_dict(contract.get("views"))
    form_view = _as_dict(views.get("form"))
    semantic_page = _as_dict(contract.get("semantic_page"))
    form_semantics = _as_dict(semantic_page.get("form_semantics"))
    out: Dict[str, Any] = {}

    layout = _as_list(form_view.get("layout"))
    if layout:
        out["layout"] = layout
    header_actions = _as_list(form_view.get("header_buttons"))
    if header_actions:
        out["header_actions"] = header_actions
    stat_actions = []
    for key in ("button_box", "stat_buttons"):
        stat_actions.extend(_as_list(form_view.get(key)))
    if stat_actions:
        out["stat_actions"] = stat_actions
    relation_fields = _as_list(form_semantics.get("relation_fields"))
    if relation_fields:
        out["relation_fields"] = relation_fields
    field_behavior_map = _as_dict(form_semantics.get("field_behavior_map"))
    if field_behavior_map:
        out["field_behavior_map"] = field_behavior_map

    flags = {}
    for key in (
        "layout_section_count",
        "has_statusbar",
        "has_notebook",
        "has_chatter",
        "has_attachments",
    ):
        if key in form_semantics:
            flags[key] = form_semantics.get(key)
    if flags:
        out["flags"] = flags
    return out


def _derive_optimization_composition(payload: Dict[str, Any]) -> Dict[str, Any]:
    search_surface = _as_dict(payload.get("search_surface"))
    list_surface = _as_dict(payload.get("list_surface"))
    if not (search_surface or list_surface):
        return {}

    toolbar_sections = []
    if search_surface:
        toolbar_sections.append({"key": "search", "kind": "search", "priority": 10, "visible": True})
        toolbar_sections.append(
            {"key": "active_conditions", "kind": "active_conditions", "priority": 20, "visible": True}
        )
    if list_surface.get("available_view_modes"):
        toolbar_sections.append({"key": "view_switch", "kind": "view_switch", "priority": 30, "visible": True})
    if list_surface.get("default_sort"):
        toolbar_sections.append({"key": "sort", "kind": "sort", "priority": 40, "visible": True})

    default_state = _as_dict(search_surface.get("default_state"))
    default_filters = [row for row in _as_list(default_state.get("filters")) if isinstance(row, dict)]
    filters = [row for row in _as_list(search_surface.get("filters")) if isinstance(row, dict)]
    high_frequency_filters = default_filters or filters[:2]

    out: Dict[str, Any] = {}
    if toolbar_sections:
        out["toolbar_sections"] = toolbar_sections
    if search_surface:
        out["active_conditions"] = {
            "visible": True,
            "include": ["route_preset", "search_term", "sort"],
            "merge_rules": {"route_preset_overrides_search_term": True},
        }
    if high_frequency_filters:
        out["high_frequency_filters"] = high_frequency_filters
    if filters or _as_list(search_surface.get("group_by")) or _as_list(search_surface.get("searchpanel")):
        out["advanced_filters"] = {
            "visible": True,
            "collapsible": True,
            "default_open": False,
            "source": {
                "include_remaining_filters": True,
                "include_searchpanel": bool(_as_list(search_surface.get("searchpanel"))),
                "include_saved_filters": False,
            },
        }
    return out


def _normalize_kanban_surface(payload: Dict[str, Any]) -> Dict[str, Any]:
    kanban_surface = payload.get("kanban_surface") if isinstance(payload.get("kanban_surface"), dict) else {}
    return dict(kanban_surface)


def _kanban_surface_nonempty(payload: Dict[str, Any]) -> bool:
    return bool(_as_dict(payload))


def _derive_kanban_surface_from_base_contract(ui_base_contract: Dict[str, Any]) -> Dict[str, Any]:
    contract = _as_dict(ui_base_contract)
    views = _as_dict(contract.get("views"))
    kanban_view = _as_dict(views.get("kanban"))
    profile = _as_dict(kanban_view.get("kanban_profile"))
    out: Dict[str, Any] = {}
    for key in (
        "title_field",
        "subtitle_field",
        "status_field",
        "primary_fields",
        "secondary_fields",
        "status_fields",
        "metric_fields",
        "quick_action_count",
        "max_meta",
    ):
        value = profile.get(key)
        if value not in (None, {}, []):
            out[key] = value
    for key in ("fields", "columns", "default_sort", "order"):
        value = kanban_view.get(key)
        if value not in (None, {}, []):
            out[key] = value
    return out


def _scene_type_from_compiled(compiled: Dict[str, Any]) -> str:
    meta = _as_dict(compiled.get("meta"))
    surface_profile = _as_dict(meta.get("surface_profile"))
    scene_type = _text(surface_profile.get("scene_type"))
    if scene_type:
        return scene_type
    surface = _as_dict(compiled.get("surface"))
    kind = _text(surface.get("kind"))
    if kind in {"workspace", "list", "form", "kanban", "ledger", "record"}:
        return kind
    page = _as_dict(compiled.get("page"))
    mode = _text(page.get("mode"))
    if mode in {"list", "form", "kanban", "ledger", "record"}:
        return mode
    return "list"


def _scene_action_rows(actions: List[Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
    rows: Dict[str, Dict[str, Any]] = {}
    for item in actions or []:
        if not isinstance(item, dict):
            continue
        key = _text(item.get("key") or item.get("intent") or item.get("label"))
        if not key or key in rows:
            continue
        target = _as_dict(item.get("target"))
        rows[key] = {
            "key": key,
            "label": _text(item.get("label") or item.get("title") or key),
            "intent": _text(item.get("intent")),
            "target": {
                "type": _text(target.get("type")),
                "route": _text(target.get("route")),
                "scene_key": _text(target.get("scene_key")),
            },
        }
    return rows


def _scene_action_refs(keys: List[Any], action_rows: Dict[str, Dict[str, Any]]) -> List[Dict[str, Any]]:
    refs: List[Dict[str, Any]] = []
    seen: set[str] = set()
    for raw in keys or []:
        key = _text(raw)
        if not key or key in seen:
            continue
        seen.add(key)
        row = _as_dict(action_rows.get(key))
        refs.append(
            {
                "key": key,
                "label": _text(row.get("label") or key),
                "intent": _text(row.get("intent")),
                "target": _as_dict(row.get("target")),
            }
        )
    return refs


def _scene_block(
    *,
    key: str,
    kind: str,
    title: str,
    order: int,
    visible: bool = True,
    semantic_role: str = "content",
    layout: Dict[str, Any] | None = None,
    data_deps: Dict[str, Any] | None = None,
    actions: List[Dict[str, Any]] | None = None,
    children: List[Dict[str, Any]] | None = None,
    payload: Dict[str, Any] | None = None,
) -> Dict[str, Any]:
    block: Dict[str, Any] = {
        "key": _text(key),
        "kind": _text(kind),
        "title": _text(title),
        "order": int(order) if order > 0 else 0,
        "visible": bool(visible),
        "semantic_role": _text(semantic_role) or "content",
    }
    if layout:
        block["layout"] = dict(layout)
    if data_deps:
        block["data_deps"] = dict(data_deps)
    if actions:
        block["actions"] = list(actions)
    if children:
        block["children"] = list(children)
    if payload:
        block["payload"] = dict(payload)
    return block


def _enforce_native_view_block_structure(
    *,
    scene_key: str,
    scene_type: str,
    blocks: List[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    if scene_type not in {"form", "list", "kanban"}:
        return list(blocks or [])

    blueprint: Dict[str, List[tuple[str, str, str, int]]] = {
        "form": [
            ("page_shell", "page_shell", "页面", 10),
            ("header_bar", "header_bar", "页头", 20),
            ("statusbar", "statusbar", "状态", 30),
            ("primary_actions", "primary_actions", "主要操作", 40),
            ("smart_actions", "smart_actions", "统计操作", 50),
            ("body", "body", "表单主体", 60),
            ("relation_block", "relation_block", "关联内容", 70),
            ("chatter", "chatter", "沟通记录", 80),
            ("footer", "footer", "流程提示", 90),
        ],
        "list": [
            ("page_shell", "page_shell", "页面", 10),
            ("header_bar", "header_bar", "页头", 20),
            ("toolbar", "toolbar", "工具栏", 30),
            ("list_view", "list_view", "列表", 40),
            ("pagination", "pagination", "分页", 50),
            ("footer", "footer", "流程提示", 60),
        ],
        "kanban": [
            ("page_shell", "page_shell", "页面", 10),
            ("header_bar", "header_bar", "页头", 20),
            ("toolbar", "toolbar", "工具栏", 30),
            ("overview_strip", "overview_strip", "概览", 40),
            ("kanban_board", "kanban_board", "看板", 50),
            ("pagination", "pagination", "分页", 60),
            ("footer", "footer", "流程提示", 70),
        ],
    }
    required_kinds = {
        "form": {"page_shell", "header_bar", "statusbar", "body"},
        "list": {"page_shell", "header_bar", "toolbar", "list_view"},
        "kanban": {"page_shell", "header_bar", "toolbar", "kanban_board"},
    }

    rows = [row for row in (blocks or []) if isinstance(row, dict)]
    by_kind: Dict[str, Dict[str, Any]] = {}
    for row in rows:
        kind = _text(row.get("kind")).lower()
        if not kind or kind in by_kind:
            continue
        by_kind[kind] = dict(row)

    out: List[Dict[str, Any]] = []
    for suffix, kind, default_title, order in blueprint.get(scene_type, []):
        current = by_kind.get(kind)
        if current:
            row = dict(current)
            row["order"] = order
            if not _text(row.get("key")):
                row["key"] = f"{scene_key}.{suffix}"
            if not _text(row.get("kind")):
                row["kind"] = kind
            if not _text(row.get("title")):
                row["title"] = default_title
            out.append(row)
            continue
        if kind in required_kinds.get(scene_type, set()):
            out.append(
                _scene_block(
                    key=f"{scene_key}.{suffix}",
                    kind=kind,
                    title=default_title,
                    order=order,
                    semantic_role="content" if kind in {"body", "list_view", "kanban_board"} else "system",
                )
            )
    return out


def _build_scene_blocks(compiled: Dict[str, Any], scene_type_override: str | None = None) -> List[Dict[str, Any]]:
    scene_type = _text(scene_type_override) or _scene_type_from_compiled(compiled)
    scene = _as_dict(compiled.get("scene"))
    page = _as_dict(compiled.get("page"))
    surface = _as_dict(compiled.get("surface"))
    intent = _as_dict(surface.get("intent"))
    search_surface = _as_dict(compiled.get("search_surface"))
    list_surface = _as_dict(compiled.get("list_surface"))
    form_surface = _as_dict(compiled.get("form_surface"))
    kanban_surface = _as_dict(compiled.get("kanban_surface"))
    action_surface = _as_dict(compiled.get("action_surface"))
    optimization = _as_dict(compiled.get("optimization_composition"))
    projection = _as_dict(compiled.get("projection"))
    view_modes = _as_list(compiled.get("view_modes"))
    actions = _as_list(compiled.get("actions"))
    action_rows = _scene_action_rows(actions)

    primary_actions = _scene_action_refs(_as_list(action_surface.get("primary_actions")), action_rows)
    header_actions = _scene_action_refs(_as_list(form_surface.get("header_actions")), action_rows)
    stat_actions = _scene_action_refs(_as_list(form_surface.get("stat_actions")), action_rows)
    toolbar_rows = _as_list(optimization.get("toolbar_sections"))
    quick_filters = _as_list(optimization.get("high_frequency_filters"))
    advanced_filters = _as_dict(optimization.get("advanced_filters"))
    relation_fields = _as_list(form_surface.get("relation_fields"))
    flags = _as_dict(form_surface.get("flags"))
    overview_items = _as_list(_as_dict(projection.get("group_summary")).get("items"))

    title = _text(page.get("title") or scene.get("title") or intent.get("title") or scene.get("key") or "场景")
    summary = _text(intent.get("summary"))
    scene_key = _text(scene.get("key"))
    blocks: List[Dict[str, Any]] = [
        _scene_block(
            key=f"{scene_key}.shell",
            kind="page_shell",
            title=title,
            order=10,
            semantic_role="system",
            layout={"full_width": True},
            payload={
                "scene_key": scene_key,
                "scene_type": scene_type,
                "summary": summary,
                "view_modes": view_modes,
            },
        ),
        _scene_block(
            key=f"{scene_key}.header",
            kind="header_bar",
            title=title,
            order=20,
            semantic_role="system",
            actions=header_actions or primary_actions[:3],
            payload={
                "scene_key": scene_key,
                "title": title,
                "summary": summary,
                "view_modes": view_modes,
            },
        ),
    ]

    if scene_type in {"form", "record"}:
        blocks.extend(
            [
                _scene_block(
                    key=f"{scene_key}.statusbar",
                    kind="statusbar",
                    title="状态",
                    order=30,
                    semantic_role="system",
                    payload={
                        "workflow_surface": _as_dict(compiled.get("workflow_surface")),
                        "validation_surface": _as_dict(compiled.get("validation_surface")),
                    },
                ),
                _scene_block(
                    key=f"{scene_key}.primary_actions",
                    kind="primary_actions",
                    title="主要操作",
                    order=40,
                    semantic_role="primary",
                    actions=primary_actions or header_actions,
                    payload={"selection_mode": _text(action_surface.get("selection_mode")) or "single"},
                ),
                _scene_block(
                    key=f"{scene_key}.smart_actions",
                    kind="smart_actions",
                    title="统计操作",
                    order=50,
                    semantic_role="secondary",
                    actions=stat_actions,
                    payload={
                        "button_box": _as_list(form_surface.get("button_box")),
                        "stat_actions": _as_list(form_surface.get("stat_actions")),
                    },
                ),
                _scene_block(
                    key=f"{scene_key}.body",
                    kind="body",
                    title="表单主体",
                    order=60,
                    semantic_role="content",
                    layout={"kind": "form", "density": "cozy", "full_width": False},
                    data_deps={
                        "layout": _as_list(form_surface.get("layout")),
                        "fields": _as_dict(form_surface.get("field_behavior_map")),
                    },
                    payload={
                        "layout": _as_list(form_surface.get("layout")),
                        "flags": flags,
                    },
                ),
            ]
        )
        if relation_fields:
            blocks.append(
                _scene_block(
                    key=f"{scene_key}.relations",
                    kind="relation_block",
                    title="关联内容",
                    order=70,
                    semantic_role="support",
                    payload={"relation_fields": relation_fields},
                )
            )
        if bool(flags.get("has_chatter")) or bool(flags.get("has_attachments")):
            blocks.append(
                _scene_block(
                    key=f"{scene_key}.chatter",
                    kind="chatter",
                    title="沟通记录",
                    order=80,
                    semantic_role="support",
                    payload={"has_attachments": bool(flags.get("has_attachments"))},
                )
            )
        blocks.append(
            _scene_block(
                key=f"{scene_key}.footer",
                kind="footer",
                title="流程提示",
                order=90,
                semantic_role="system",
                payload={
                    "next_scene_key": _text(compiled.get("next_scene")),
                    "next_scene_route": _text(compiled.get("next_scene_route")),
                },
            )
        )
        return _enforce_native_view_block_structure(scene_key=scene_key, scene_type="form", blocks=blocks)

    if scene_type in {"list", "ledger"}:
        blocks.extend(
            [
                _scene_block(
                    key=f"{scene_key}.toolbar",
                    kind="toolbar",
                    title="工具栏",
                    order=30,
                    semantic_role="system",
                    payload={
                        "search_surface": search_surface,
                        "list_surface": list_surface,
                        "toolbar_sections": toolbar_rows,
                        "quick_filters": quick_filters,
                        "advanced_filters": advanced_filters,
                    },
                ),
                _scene_block(
                    key=f"{scene_key}.list_view",
                    kind="list_view",
                    title="列表",
                    order=40,
                    semantic_role="content",
                    layout={"kind": "list", "density": "compact", "full_width": True},
                    data_deps={
                        "columns": _as_list(list_surface.get("columns")),
                        "search_fields": _as_list(search_surface.get("fields")),
                        "group_by": _as_list(search_surface.get("group_by")),
                    },
                    payload={
                        "default_sort": _text(list_surface.get("default_sort") if isinstance(list_surface.get("default_sort"), str) else _as_dict(list_surface.get("default_sort")).get("raw")),
                        "available_view_modes": view_modes,
                    },
                ),
                _scene_block(
                    key=f"{scene_key}.pagination",
                    kind="pagination",
                    title="分页",
                    order=50,
                    semantic_role="system",
                    payload={"default_limit": _text(list_surface.get("limit")) or _text(list_surface.get("page_size"))},
                ),
                _scene_block(
                    key=f"{scene_key}.footer",
                    kind="footer",
                    title="流程提示",
                    order=60,
                    semantic_role="system",
                    payload={
                        "next_scene_key": _text(compiled.get("next_scene")),
                        "next_scene_route": _text(compiled.get("next_scene_route")),
                    },
                ),
            ]
        )
        return _enforce_native_view_block_structure(scene_key=scene_key, scene_type="list", blocks=blocks)

    if scene_type == "kanban":
        blocks.extend(
            [
                _scene_block(
                    key=f"{scene_key}.toolbar",
                    kind="toolbar",
                    title="工具栏",
                    order=30,
                    semantic_role="system",
                    payload={
                        "search_surface": search_surface,
                        "list_surface": list_surface,
                        "view_modes": view_modes,
                        "toolbar_sections": toolbar_rows,
                    },
                ),
                _scene_block(
                    key=f"{scene_key}.overview",
                    kind="overview_strip",
                    title="概览",
                    order=40,
                    semantic_role="secondary",
                    payload={"overview_items": overview_items},
                ),
                _scene_block(
                    key=f"{scene_key}.board",
                    kind="kanban_board",
                    title="看板",
                    order=50,
                    semantic_role="content",
                    layout={"kind": "kanban", "density": "cozy", "full_width": True},
                    data_deps={
                        "columns": _as_list(kanban_surface.get("columns")) or _as_list(list_surface.get("columns")),
                        "fields": _as_list(kanban_surface.get("fields")),
                        "search_fields": _as_list(search_surface.get("fields")),
                    },
                    payload={
                        "available_view_modes": view_modes,
                        "selection_mode": _text(action_surface.get("selection_mode")) or "multi",
                        "actions": primary_actions,
                        "kanban_surface": kanban_surface,
                    },
                ),
                _scene_block(
                    key=f"{scene_key}.pagination",
                    kind="pagination",
                    title="分页",
                    order=60,
                    semantic_role="system",
                    payload={"default_limit": _text(list_surface.get("limit")) or _text(list_surface.get("page_size"))},
                ),
                _scene_block(
                    key=f"{scene_key}.footer",
                    kind="footer",
                    title="流程提示",
                    order=70,
                    semantic_role="system",
                    payload={
                        "next_scene_key": _text(compiled.get("next_scene")),
                        "next_scene_route": _text(compiled.get("next_scene_route")),
                    },
                ),
            ]
        )
        return _enforce_native_view_block_structure(scene_key=scene_key, scene_type="kanban", blocks=blocks)

    blocks.extend(
        [
            _scene_block(
                key=f"{scene_key}.toolbar",
                kind="toolbar",
                title="工具栏",
                order=30,
                semantic_role="system",
                payload={
                    "search_surface": search_surface,
                    "list_surface": list_surface,
                    "view_modes": view_modes,
                },
            ),
            _scene_block(
                key=f"{scene_key}.content",
                kind="content",
                title="内容",
                order=40,
                semantic_role="content",
                payload={
                    "projection": projection,
                    "action_surface": action_surface,
                },
            ),
            _scene_block(
                key=f"{scene_key}.footer",
                kind="footer",
                title="流程提示",
                order=50,
                semantic_role="system",
                payload={
                    "next_scene_key": _text(compiled.get("next_scene")),
                    "next_scene_route": _text(compiled.get("next_scene_route")),
                },
            ),
        ]
    )
    return blocks


def _build_view_orchestration_contract_v1(
    *,
    scene_key: str,
    scene_blocks_by_view: Dict[str, Any],
) -> Dict[str, Any]:
    def _section_defs(mode: str) -> List[Dict[str, Any]]:
        rows = scene_blocks_by_view.get(mode) if isinstance(scene_blocks_by_view, dict) else []
        blocks = [item for item in rows if isinstance(item, dict)]
        out: List[Dict[str, Any]] = []
        for item in blocks:
            kind = _text(item.get("kind"))
            key = _text(item.get("key")) or f"{scene_key}.{kind}"
            if not kind:
                continue
            out.append(
                {
                    "key": key,
                    "kind": kind,
                    "order": int(item.get("order") or 0),
                    "visible": bool(item.get("visible", True)),
                    "semantic_role": _text(item.get("semantic_role")) or "content",
                    "title": _text(item.get("title") or kind),
                }
            )
        return out

    return {
        "schema_version": "view_orchestration_v1",
        "scene_key": scene_key,
        "views": {
            "form": {"sections": _section_defs("form")},
            "list": {"sections": _section_defs("list")},
            "kanban": {"sections": _section_defs("kanban")},
        },
    }


def apply_scene_ready_search_semantic_bridge(payload: Dict[str, Any] | None) -> Dict[str, Any]:
    """Compatibility bridge: keep payload stable when optional search bridge is absent."""
    return dict(payload or {})


def apply_scene_ready_action_semantic_bridge(payload: Dict[str, Any] | None) -> Dict[str, Any]:
    """Compatibility bridge: keep payload stable when optional action bridge is absent."""
    return dict(payload or {})


def _scene_type_consumption_metrics(entries: List[Dict[str, Any]]) -> Dict[str, Any]:
    buckets: Dict[str, Dict[str, Any]] = {}
    for entry in entries:
        if not isinstance(entry, dict):
            continue
        meta = entry.get("meta") if isinstance(entry.get("meta"), dict) else {}
        base_facts = meta.get("base_facts") if isinstance(meta.get("base_facts"), dict) else {}
        surface_profile = meta.get("surface_profile") if isinstance(meta.get("surface_profile"), dict) else {}
        scene_type = _text(surface_profile.get("scene_type") or "list")
        row = buckets.get(scene_type)
        if not isinstance(row, dict):
            row = {
                "scene_count": 0,
                "base_fact_hits": {
                    "search": 0,
                    "workflow": 0,
                    "validator": 0,
                    "actions": 0,
                },
                "surface_nonempty_hits": {
                    "search": 0,
                    "workflow": 0,
                    "validation": 0,
                    "action_surface": 0,
                },
            }
            buckets[scene_type] = row
        row["scene_count"] = int(row.get("scene_count") or 0) + 1

        fact_hits = row.get("base_fact_hits") if isinstance(row.get("base_fact_hits"), dict) else {}
        for key in ("search", "workflow", "validator", "actions"):
            if bool(base_facts.get(key)):
                fact_hits[key] = int(fact_hits.get(key) or 0) + 1
        row["base_fact_hits"] = fact_hits

        surface_hits = row.get("surface_nonempty_hits") if isinstance(row.get("surface_nonempty_hits"), dict) else {}
        search_surface = entry.get("search_surface") if isinstance(entry.get("search_surface"), dict) else {}
        workflow_surface = entry.get("workflow_surface") if isinstance(entry.get("workflow_surface"), dict) else {}
        validation_surface = entry.get("validation_surface") if isinstance(entry.get("validation_surface"), dict) else {}
        action_surface = entry.get("action_surface") if isinstance(entry.get("action_surface"), dict) else {}

        if bool(search_surface.get("filters") or search_surface.get("fields") or search_surface.get("group_by")):
            surface_hits["search"] = int(surface_hits.get("search") or 0) + 1
        if bool(workflow_surface.get("states") or workflow_surface.get("transitions") or workflow_surface.get("state_field")):
            surface_hits["workflow"] = int(surface_hits.get("workflow") or 0) + 1
        if bool(validation_surface.get("required_fields") or validation_surface.get("field_rules")):
            surface_hits["validation"] = int(surface_hits.get("validation") or 0) + 1
        action_counts = action_surface.get("counts") if isinstance(action_surface.get("counts"), dict) else {}
        if int(action_counts.get("total") or 0) > 0:
            surface_hits["action_surface"] = int(surface_hits.get("action_surface") or 0) + 1
        row["surface_nonempty_hits"] = surface_hits

    metrics: Dict[str, Any] = {}
    for scene_type, row in buckets.items():
        scene_count = int(row.get("scene_count") or 0)
        fact_hits = row.get("base_fact_hits") if isinstance(row.get("base_fact_hits"), dict) else {}
        surface_hits = row.get("surface_nonempty_hits") if isinstance(row.get("surface_nonempty_hits"), dict) else {}

        def _ratio(hit: int) -> float:
            return float(hit) / float(scene_count) if scene_count > 0 else 0.0

        metrics[scene_type] = {
            "scene_count": scene_count,
            "base_fact_hits": fact_hits,
            "base_fact_consumption_rate": {
                "search": _ratio(int(fact_hits.get("search") or 0)),
                "workflow": _ratio(int(fact_hits.get("workflow") or 0)),
                "validator": _ratio(int(fact_hits.get("validator") or 0)),
                "actions": _ratio(int(fact_hits.get("actions") or 0)),
            },
            "surface_nonempty_hits": surface_hits,
            "surface_nonempty_rate": {
                "search": _ratio(int(surface_hits.get("search") or 0)),
                "workflow": _ratio(int(surface_hits.get("workflow") or 0)),
                "validation": _ratio(int(surface_hits.get("validation") or 0)),
                "action_surface": _ratio(int(surface_hits.get("action_surface") or 0)),
            },
        }
    return metrics


def _pilot_scene_surface_spec(scene_key: str) -> Dict[str, Any]:
    if _scene_key_matches(scene_key, "workspace.home"):
        return {
            "kind": "workspace",
            "intent": {
                "title": "角色首页：先处理高优先级行动",
                "summary": "优先处理今日待办，完成后自动刷新当前视图。",
                "empty_title": "当前暂无待处理事项",
                "empty_hint": "建议切换筛选条件或进入场景导航继续巡检。",
                "primary_action": {"label": "查看我的工作", "target": "/my-work"},
                "secondary_action": {"label": "进入场景导航", "target": "/"},
            },
        }
    return {
        "kind": "generic",
        "intent": {
            "title": "场景视图",
            "summary": "当前场景已启用严格契约消费模式。",
            "empty_title": "暂无可展示数据",
            "empty_hint": "请检查场景契约或稍后重试。",
            "primary_action": {"label": "返回角色首页", "target": "/"},
        },
    }


def _default_view_modes(scene_key: str, page: Dict[str, Any], scene: Dict[str, Any]) -> List[Dict[str, Any]]:
    mode_candidates: List[str] = []
    layout_kind = _text((scene.get("layout") if isinstance(scene.get("layout"), dict) else {}).get("kind"))
    page_mode = _text(page.get("mode"))
    if layout_kind in {"list", "table"}:
        mode_candidates = ["tree", "kanban"]
    elif layout_kind in {"workspace", "dashboard"} or _scene_key_matches(scene_key, "workspace.home"):
        mode_candidates = ["kanban", "tree"]
    elif page_mode:
        mode_candidates = [page_mode]
    else:
        mode_candidates = ["tree"]
    out: List[Dict[str, Any]] = []
    for mode in mode_candidates:
        label = {
            "tree": "列表",
            "kanban": "看板",
            "pivot": "透视",
            "graph": "图表",
            "calendar": "日历",
            "gantt": "甘特",
            "activity": "活动",
            "dashboard": "仪表板",
        }.get(mode, mode)
        out.append({"key": mode, "label": label, "enabled": True})
    return out


def _default_projection(scene_key: str) -> Dict[str, Any]:
    kind = "generic"
    if _scene_key_matches(scene_key, "workspace.home"):
        kind = "workspace_home"
    return {
        "kind": kind,
        "summary_items": [],
        "overview_strip": [],
        "group_summary": {"items": []},
    }


def _default_action_surface(scene_key: str, actions: List[Dict[str, Any]]) -> Dict[str, Any]:
    keys = [_text(item.get("key")) for item in actions if isinstance(item, dict) and _text(item.get("key"))]
    unique_keys: List[str] = []
    for key in keys:
        if key not in unique_keys:
            unique_keys.append(key)
    if not unique_keys and _scene_key_matches(scene_key, "workspace.home"):
        unique_keys = ["open_my_work", "open_risk_center"]
    selection_mode = "single"
    return {
        "primary_actions": unique_keys[:3],
        "groups": [{
            "key": "workflow",
            "label": "流程推进",
            "actions": unique_keys,
        }] if unique_keys else [],
        "selection_mode": selection_mode,
    }


def _seed_pilot_scene_contract(scene_key: str, scene_payload: Dict[str, Any]) -> Dict[str, Any]:
    if not _scene_key_matches(scene_key, "workspace.home"):
        return scene_payload
    payload = dict(scene_payload)
    layout = _as_dict(payload.get("layout"))
    pseudo_scene = {"layout": layout}
    if not _as_dict(payload.get("surface")):
        payload["surface"] = _pilot_scene_surface_spec(scene_key)
    if not _as_list(payload.get("view_modes")):
        payload["view_modes"] = _default_view_modes(scene_key, {}, pseudo_scene)
    if not _as_dict(payload.get("sections")):
        payload["sections"] = {
            "quick_actions": {"enabled": True, "tag": "section"},
            "group_summary": {"enabled": True, "tag": "section"},
        }
    if not _as_dict(payload.get("projection")):
        payload["projection"] = _default_projection(scene_key)
    action_surface = _as_dict(payload.get("action_surface"))
    if not _as_list(action_surface.get("groups")):
        seed = _default_action_surface(scene_key, _as_list(payload.get("actions")))
        action_surface.setdefault("primary_actions", seed.get("primary_actions"))
        action_surface.setdefault("selection_mode", seed.get("selection_mode"))
        action_surface["groups"] = seed.get("groups")
    if action_surface:
        payload["action_surface"] = action_surface
    runtime_policy = _as_dict(payload.get("runtime_policy"))
    runtime_policy.setdefault("strict_contract_mode", True)
    runtime_policy.setdefault("scene_tier", "core")
    payload["runtime_policy"] = runtime_policy
    payload.setdefault("scene_tier", "core")
    return payload


def _action_surface_with_counts(action_surface: Dict[str, Any], actions: List[Dict[str, Any]]) -> Dict[str, Any]:
    payload = dict(action_surface or {})
    counts = payload.get("counts") if isinstance(payload.get("counts"), dict) else {}
    total = len([row for row in actions if isinstance(row, dict)])
    payload["counts"] = {
        "total": _to_int(counts.get("total") or total),
        "primary": _to_int(counts.get("primary") or len(_as_list(payload.get("primary_actions")))),
        "groups": _to_int(counts.get("groups") or len(_as_list(payload.get("groups")))),
    }
    return payload


def _declared_runtime_policy(item: Dict[str, Any], compiled: Dict[str, Any]) -> Dict[str, Any]:
    item_runtime = _as_dict(item.get("runtime_policy"))
    item_runtime_alt = _as_dict(_as_dict(item.get("runtime")).get("runtime_policy"))
    compiled_runtime = _as_dict(compiled.get("runtime_policy"))
    scene_runtime = _as_dict(_as_dict(compiled.get("scene")).get("runtime_policy"))
    merged: Dict[str, Any] = {}
    merged.update(item_runtime)
    merged.update(item_runtime_alt)
    merged.update(compiled_runtime)
    merged.update(scene_runtime)
    return merged


def _declared_scene_tier(item: Dict[str, Any], compiled: Dict[str, Any], runtime_policy: Dict[str, Any]) -> str:
    return (
        _text(runtime_policy.get("scene_tier"))
        or _text(item.get("scene_tier") or item.get("tier"))
        or _text(_as_dict(compiled.get("scene")).get("tier"))
        or _text(_as_dict(_as_dict(compiled.get("meta")).get("runtime_policy")).get("scene_tier"))
    )


def _strict_contract_missing_paths(compiled: Dict[str, Any]) -> List[str]:
    missing: List[str] = []
    surface = _as_dict(compiled.get("surface"))
    intent = _as_dict(surface.get("intent"))
    view_modes = _as_list(compiled.get("view_modes"))
    sections = _as_dict(compiled.get("sections"))
    action_surface = _as_dict(compiled.get("action_surface"))
    projection = _as_dict(compiled.get("projection"))
    group_summary = _as_dict(projection.get("group_summary"))

    if not _text(surface.get("kind")):
        missing.append("surface.kind")
    if not _text(intent.get("title")):
        missing.append("surface.intent.title")
    if not _text(intent.get("summary")):
        missing.append("surface.intent.summary")
    if not view_modes:
        missing.append("view_modes")
    if not isinstance(sections.get("quick_actions"), dict):
        missing.append("sections.quick_actions")
    if not isinstance(sections.get("group_summary"), dict):
        missing.append("sections.group_summary")
    if not _as_list(action_surface.get("primary_actions")):
        missing.append("action_surface.primary_actions")
    if not _as_list(action_surface.get("groups")):
        missing.append("action_surface.groups")
    if not _text(action_surface.get("selection_mode")):
        missing.append("action_surface.selection_mode")
    if not isinstance(projection.get("summary_items"), list):
        missing.append("projection.summary_items")
    if not isinstance(projection.get("overview_strip"), list):
        missing.append("projection.overview_strip")
    if not isinstance(group_summary.get("items"), list):
        missing.append("projection.group_summary.items")
    return missing


def _apply_pilot_strict_contract(scene_key: str, item: Dict[str, Any], compiled: Dict[str, Any]) -> Dict[str, Any]:
    is_pilot_scene = _scene_key_matches(
        scene_key,
        "workspace.home",
    )
    scene_payload = _as_dict(compiled.get("scene"))
    page_payload = _as_dict(compiled.get("page"))
    actions_payload = _as_list(compiled.get("actions"))

    runtime_policy = _declared_runtime_policy(item, compiled)
    scene_tier = _declared_scene_tier(item, compiled, runtime_policy)

    if not scene_tier and is_pilot_scene:
        scene_tier = "core"
    if "strict_contract_mode" not in runtime_policy and is_pilot_scene:
        runtime_policy["strict_contract_mode"] = True
    if scene_tier and "scene_tier" not in runtime_policy:
        runtime_policy["scene_tier"] = scene_tier

    if scene_tier:
        compiled["scene_tier"] = scene_tier
        scene_payload["tier"] = scene_tier
    if runtime_policy:
        compiled["runtime_policy"] = runtime_policy
        scene_payload["runtime_policy"] = {
            "strict_contract_mode": bool(runtime_policy.get("strict_contract_mode"))
            if isinstance(runtime_policy.get("strict_contract_mode"), bool)
            else runtime_policy.get("strict_contract_mode"),
            "scene_tier": _text(runtime_policy.get("scene_tier") or scene_tier),
        }
    compiled["scene"] = scene_payload

    strict_mode = bool(runtime_policy.get("strict_contract_mode"))
    should_materialize = True
    source_missing = _strict_contract_missing_paths(compiled) if strict_mode else []
    defaults_applied: List[str] = []

    if should_materialize and (not isinstance(compiled.get("surface"), dict) or not compiled.get("surface")):
        compiled["surface"] = _pilot_scene_surface_spec(scene_key)
        defaults_applied.append("surface")

    if should_materialize and (not isinstance(compiled.get("view_modes"), list) or not compiled.get("view_modes")):
        compiled["view_modes"] = _default_view_modes(scene_key, page_payload, scene_payload)
        defaults_applied.append("view_modes")

    if should_materialize and (not isinstance(compiled.get("sections"), dict) or not compiled.get("sections")):
        compiled["sections"] = {
            "quick_actions": {"enabled": True, "tag": "section"},
            "group_summary": {"enabled": True, "tag": "section"},
        }
        defaults_applied.append("sections")

    if should_materialize and (not isinstance(compiled.get("projection"), dict) or not compiled.get("projection")):
        compiled["projection"] = _default_projection(scene_key)
        defaults_applied.append("projection")

    action_surface = _as_dict(compiled.get("action_surface"))
    if should_materialize and (not isinstance(action_surface.get("groups"), list) or not action_surface.get("groups")):
        seed = _default_action_surface(scene_key, actions_payload)
        action_surface.setdefault("primary_actions", seed.get("primary_actions"))
        action_surface.setdefault("selection_mode", seed.get("selection_mode"))
        action_surface["groups"] = seed.get("groups")
        defaults_applied.append("action_surface.groups")
    compiled["action_surface"] = _action_surface_with_counts(action_surface, [row for row in actions_payload if isinstance(row, dict)])

    meta_payload = _as_dict(compiled.get("meta"))
    meta_runtime_policy = _as_dict(meta_payload.get("runtime_policy"))
    if runtime_policy:
        meta_runtime_policy.update({
            "strict_contract_mode": runtime_policy.get("strict_contract_mode"),
            "scene_tier": _text(runtime_policy.get("scene_tier") or scene_tier),
        })
    if meta_runtime_policy:
        meta_payload["runtime_policy"] = meta_runtime_policy
    if scene_tier:
        meta_payload["scene_tier"] = scene_tier
    if strict_mode:
        missing_after = _strict_contract_missing_paths(compiled)
        contract_guard = {
            "strict_mode": True,
            "source_missing": source_missing,
            "missing": missing_after,
            "defaults_applied": defaults_applied,
            "contract_ready": len(missing_after) == 0,
        }
        compiled["contract_guard"] = contract_guard
        meta_payload["contract_guard"] = contract_guard
    compiled["meta"] = meta_payload

    return compiled


def _scene_ready_entry(
    item: Dict[str, Any],
    *,
    runtime_context: Dict[str, Any] | None = None,
    action_surface_strategy: Dict[str, Any] | None = None,
    scene_catalog: Dict[str, Dict[str, Any]] | None = None,
) -> Dict[str, Any]:
    scene_key = _text(item.get("code") or item.get("key"))
    scene_payload = dict(item)
    runtime_ctx = runtime_context if isinstance(runtime_context, dict) else {}
    scene_provider_payload = _resolve_scene_provider_payload(scene_key, runtime_ctx)

    if scene_provider_payload:
        for field in (
            "guidance",
            "primary_action",
            "next_action",
            "fallback_strategy",
            "delivery_handoff_v1",
            "next_scene",
            "next_scene_key",
            "next_scene_route",
            "handling_entry_catalog",
            "extensions",
        ):
            current = scene_payload.get(field)
            provider_value = scene_provider_payload.get(field)
            if current in (None, {}, [], "") and provider_value not in (None, {}, [], ""):
                scene_payload[field] = provider_value

    if not isinstance(scene_payload.get("actions"), list):
        provider_actions = scene_provider_payload.get("default_actions") if isinstance(scene_provider_payload.get("default_actions"), list) else []
        if provider_actions:
            scene_payload["actions"] = provider_actions

    if not bool(scene_provider_payload.get("skip_pilot_seed")):
        scene_payload = _seed_pilot_scene_contract(scene_key, scene_payload)

    base_contract_raw = item.get("ui_base_contract") if isinstance(item.get("ui_base_contract"), dict) else {}
    base_contract_adapted = adapt_ui_base_contract(base_contract_raw, scene_key=scene_key)
    ui_base_contract = (
        base_contract_adapted.get("normalized_contract")
        if isinstance(base_contract_adapted.get("normalized_contract"), dict)
        else {}
    )
    runtime_payload = scene_payload.get("runtime") if isinstance(scene_payload.get("runtime"), dict) else {}
    runtime_merged = dict(runtime_payload)
    role_code = _text(runtime_ctx.get("role_code"))
    if role_code:
        runtime_merged["role_code"] = role_code
    company_id = int(runtime_ctx.get("company_id") or 0)
    if company_id > 0:
        runtime_merged["company_id"] = company_id
    strategy_payload = action_surface_strategy if isinstance(action_surface_strategy, dict) else {}
    if strategy_payload:
        runtime_merged["action_surface_strategy"] = strategy_payload

    provider_next_scene = _text(scene_provider_payload.get("next_scene") or scene_provider_payload.get("next_scene_key"))
    provider_next_scene_route = _text(scene_provider_payload.get("next_scene_route"))
    if provider_next_scene and not _text(runtime_merged.get("next_scene") or runtime_merged.get("next_scene_key")):
        runtime_merged["next_scene"] = provider_next_scene
    if provider_next_scene_route and not _text(runtime_merged.get("next_scene_route")):
        runtime_merged["next_scene_route"] = provider_next_scene_route

    if runtime_merged:
        scene_payload["runtime"] = runtime_merged

    if scene_provider_payload:
        providers_inline = scene_payload.get("providers") if isinstance(scene_payload.get("providers"), list) else []
        providers_inline.append(
            {
                "key": f"runtime.scene_provider.{scene_key}",
                "payload": scene_provider_payload,
            }
        )
        scene_payload["providers"] = providers_inline

    provider_registry = item.get("provider_registry") if isinstance(item.get("provider_registry"), dict) else {}
    compiled = scene_compile(
        scene_payload,
        scene_key=scene_key,
        ui_base_contract=ui_base_contract,
        provider_registry=provider_registry,
    )
    for field in (
        "surface",
        "view_modes",
        "sections",
        "projection",
        "action_surface",
        "runtime_policy",
        "scene_tier",
        "guidance",
        "primary_action",
        "next_action",
        "fallback_strategy",
        "delivery_handoff_v1",
        "handling_entry_catalog",
        "extensions",
    ):
        if field in compiled and compiled.get(field) not in (None, {}, []):
            continue
        source_value = scene_payload.get(field)
        if source_value in (None, {}, []):
            continue
        compiled[field] = source_value
    compiled_action_surface = _as_dict(compiled.get("action_surface"))
    seeded_action_surface = _as_dict(scene_payload.get("action_surface"))
    if seeded_action_surface:
        if not _as_list(compiled_action_surface.get("primary_actions")) and _as_list(seeded_action_surface.get("primary_actions")):
            compiled_action_surface["primary_actions"] = _as_list(seeded_action_surface.get("primary_actions"))
        if not _as_list(compiled_action_surface.get("groups")) and _as_list(seeded_action_surface.get("groups")):
            compiled_action_surface["groups"] = _as_list(seeded_action_surface.get("groups"))
        if not _text(compiled_action_surface.get("selection_mode")) and _text(seeded_action_surface.get("selection_mode")):
            compiled_action_surface["selection_mode"] = _text(seeded_action_surface.get("selection_mode"))
    if compiled_action_surface:
        compiled["action_surface"] = compiled_action_surface
    related_scenes = _as_list(scene_payload.get("related_scenes"))
    if related_scenes:
        compiled["related_scenes"] = related_scenes
    compiled_search_surface = _normalize_search_surface(_as_dict(compiled.get("search_surface")))
    seeded_search_surface = _normalize_search_surface(_as_dict(scene_payload.get("search_surface")))
    if not _search_surface_nonempty(compiled_search_surface) and _search_surface_nonempty(seeded_search_surface):
        compiled["search_surface"] = seeded_search_surface
    compiled_permission_surface = _normalize_permission_surface(_as_dict(compiled.get("permission_surface")))
    seeded_permission_surface = _normalize_permission_surface(_as_dict(scene_payload.get("permission_surface")))
    if not _permission_surface_nonempty(compiled_permission_surface) and _permission_surface_nonempty(seeded_permission_surface):
        compiled["permission_surface"] = seeded_permission_surface
    compiled_workflow_surface = _as_dict(compiled.get("workflow_surface"))
    seeded_workflow_surface = _as_dict(scene_payload.get("workflow_surface"))
    if not _workflow_surface_nonempty(compiled_workflow_surface) and _workflow_surface_nonempty(seeded_workflow_surface):
        compiled["workflow_surface"] = dict(seeded_workflow_surface)
    compiled_validation_surface = _as_dict(compiled.get("validation_surface"))
    seeded_validation_surface = _as_dict(scene_payload.get("validation_surface"))
    if not _validation_surface_nonempty(compiled_validation_surface) and _validation_surface_nonempty(seeded_validation_surface):
        compiled["validation_surface"] = dict(seeded_validation_surface)
    page = dict(compiled.get("page") or {})
    zones = page.get("zones") if isinstance(page.get("zones"), list) else []
    if not zones:
        page["zones"] = [
            {"name": "header", "blocks": ["scene.header"]},
            {"name": "main", "blocks": ["scene.main"]},
        ]
    if not _text(page.get("route")) and scene_key:
        page["route"] = f"/s/{scene_key}"
    compiled["page"] = page
    compiled.setdefault("workflow_surface", {})
    compiled.setdefault("validation_surface", {})
    meta_payload = compiled.get("meta") if isinstance(compiled.get("meta"), dict) else {}
    target_payload = item.get("target") if isinstance(item.get("target"), dict) else {}
    page_route = _text(page.get("route"))
    target_route = _text(target_payload.get("route"))
    meta_target = {
        "route": target_route or page_route,
        "action_id": _to_int(target_payload.get("action_id")) or None,
        "menu_id": _to_int(target_payload.get("menu_id")) or None,
        "model": _text(target_payload.get("model")) or None,
        "view_mode": _text(target_payload.get("view_mode")) or None,
    }
    meta_payload["target"] = {k: v for k, v in meta_target.items() if v not in (None, "")}
    source_ref_payload = item.get("ui_base_contract_ref") if isinstance(item.get("ui_base_contract_ref"), dict) else {}
    asset_version = _text(source_ref_payload.get("asset_version"))
    source_kind = "none"
    if asset_version.startswith("runtime-minimal"):
        source_kind = "runtime_minimal"
    elif asset_version.startswith("runtime-fallback"):
        source_kind = "runtime_fallback"
    elif source_ref_payload.get("asset_id"):
        source_kind = "asset"
    elif isinstance(item.get("ui_base_contract"), dict) and item.get("ui_base_contract"):
        source_kind = "inline"
    meta_payload["ui_base_contract_source"] = {
        "kind": source_kind,
        "asset_id": source_ref_payload.get("asset_id"),
        "asset_version": asset_version,
        "source_ref": _text(source_ref_payload.get("source_ref")),
    }

    def _resolve_next_scene_from_providers() -> tuple[str, str]:
        providers = item.get("providers") if isinstance(item.get("providers"), list) else []
        for provider in providers:
            payload = provider if isinstance(provider, dict) else {}
            inline = payload.get("payload") if isinstance(payload.get("payload"), dict) else {}
            next_key = _text(inline.get("next_scene") or inline.get("next_scene_key"))
            next_route = _text(inline.get("next_scene_route"))
            if next_key or next_route:
                return next_key, next_route
            provider_key = _text(payload.get("key") or payload.get("provider"))
            if not provider_key:
                continue
            registry_payload = provider_registry.get(provider_key) if isinstance(provider_registry, dict) else {}
            if callable(registry_payload):
                try:
                    registry_payload = registry_payload(scene_key=scene_key, runtime=runtime_merged, context={})
                except Exception:
                    registry_payload = {}
            registry_entry = registry_payload if isinstance(registry_payload, dict) else {}
            next_key = _text(registry_entry.get("next_scene") or registry_entry.get("next_scene_key"))
            next_route = _text(registry_entry.get("next_scene_route"))
            if next_key or next_route:
                return next_key, next_route
        return "", ""

    next_scene_key = _text(scene_payload.get("next_scene") or scene_payload.get("next_scene_key") or item.get("next_scene") or item.get("next_scene_key"))
    next_scene_route = _text(scene_payload.get("next_scene_route") or item.get("next_scene_route"))
    payload_runtime = scene_payload.get("runtime") if isinstance(scene_payload.get("runtime"), dict) else {}
    if not next_scene_key and payload_runtime:
        next_scene_key = _text(payload_runtime.get("next_scene") or payload_runtime.get("next_scene_key"))
    if not next_scene_route and payload_runtime:
        next_scene_route = _text(payload_runtime.get("next_scene_route"))
    policies_payload = scene_payload.get("policies") if isinstance(scene_payload.get("policies"), dict) else item.get("policies") if isinstance(item.get("policies"), dict) else {}
    if not next_scene_key and policies_payload:
        nav_policy = policies_payload.get("navigation_policy") if isinstance(policies_payload.get("navigation_policy"), dict) else {}
        next_scene_key = _text(nav_policy.get("next_scene") or nav_policy.get("next_scene_key"))
        next_scene_route = next_scene_route or _text(nav_policy.get("next_scene_route"))

    if not next_scene_key and not next_scene_route:
        provider_next_key, provider_next_route = _resolve_next_scene_from_providers()
        next_scene_key = next_scene_key or provider_next_key
        next_scene_route = next_scene_route or provider_next_route

    if not next_scene_key and _scene_key_matches(scene_key, "workspace.intake"):
        next_scene_key = "workspace.management"
    if not next_scene_route and next_scene_key:
        next_scene_route = f"/s/{next_scene_key}"

    if next_scene_key:
        compiled["next_scene"] = next_scene_key
    if next_scene_route:
        compiled["next_scene_route"] = next_scene_route
    if next_scene_key or next_scene_route:
        meta_payload["next_scene"] = {
            "key": next_scene_key,
            "route": next_scene_route,
        }

    orchestrator_input = (
        base_contract_adapted.get("orchestrator_input")
        if isinstance(base_contract_adapted.get("orchestrator_input"), dict)
        else {}
    )
    if orchestrator_input:
        meta_payload["ui_base_orchestrator_input"] = orchestrator_input
    compiled["meta"] = meta_payload
    compiled = apply_scene_ready_parser_semantic_bridge(compiled, ui_base_contract)
    compiled = apply_scene_ready_entry_semantic_bridge(compiled)
    compiled = apply_scene_ready_search_semantic_bridge(compiled)
    compiled = apply_scene_ready_semantic_orchestration_bridge(
        compiled,
        scene_key=scene_key,
        scene_catalog=scene_catalog,
    )
    compiled = apply_scene_ready_action_semantic_bridge(compiled)
    compiled_list_surface = _normalize_list_surface(compiled)
    seeded_list_surface = _normalize_list_surface(scene_payload)
    if _list_surface_nonempty(compiled_list_surface):
        compiled["list_surface"] = compiled_list_surface
    elif _list_surface_nonempty(seeded_list_surface):
        compiled["list_surface"] = seeded_list_surface
    compiled_form_surface = _normalize_form_surface(compiled)
    seeded_form_surface = _normalize_form_surface(scene_payload)
    base_form_surface = _derive_form_surface_from_base_contract(ui_base_contract)
    merged_form_surface = _merge_form_surface(compiled_form_surface, seeded_form_surface)
    merged_form_surface = _merge_form_surface(merged_form_surface, base_form_surface)
    if _form_surface_nonempty(merged_form_surface):
        compiled["form_surface"] = merged_form_surface
    elif _form_surface_nonempty(seeded_form_surface):
        compiled["form_surface"] = seeded_form_surface
    compiled_kanban_surface = _normalize_kanban_surface(compiled)
    seeded_kanban_surface = _normalize_kanban_surface(scene_payload)
    base_kanban_surface = _derive_kanban_surface_from_base_contract(ui_base_contract)
    merged_kanban_surface = dict(base_kanban_surface)
    merged_kanban_surface.update(seeded_kanban_surface)
    merged_kanban_surface.update(compiled_kanban_surface)
    if _kanban_surface_nonempty(merged_kanban_surface):
        compiled["kanban_surface"] = merged_kanban_surface
    elif _kanban_surface_nonempty(seeded_kanban_surface):
        compiled["kanban_surface"] = seeded_kanban_surface
    optimization_composition = _normalize_optimization_composition(compiled)
    if not _optimization_composition_nonempty(optimization_composition):
        optimization_composition = _derive_optimization_composition(compiled)
    if _optimization_composition_nonempty(optimization_composition):
        compiled["optimization_composition"] = optimization_composition
    scene_blocks = _build_scene_blocks(compiled)
    if scene_blocks:
        compiled["scene_blocks"] = scene_blocks
    scene_blocks_by_view: Dict[str, Any] = {}
    for mode in ("form", "list", "kanban"):
        blocks = _build_scene_blocks(compiled, scene_type_override=mode)
        if blocks:
            scene_blocks_by_view[mode] = blocks
    if scene_blocks_by_view:
        compiled["scene_blocks_by_view"] = scene_blocks_by_view
        compiled["view_orchestration_contract_v1"] = _build_view_orchestration_contract_v1(
            scene_key=scene_key,
            scene_blocks_by_view=scene_blocks_by_view,
        )
    compiled = _apply_pilot_strict_contract(scene_key, item, compiled)
    return compiled


def build_scene_ready_contract_v1(
    *,
    scenes: List[Dict[str, Any]] | None,
    role_surface: Dict[str, Any] | None = None,
    scene_version: str | None = None,
    schema_version: str | None = None,
    scene_channel: str | None = None,
    action_surface_strategy: Dict[str, Any] | None = None,
    runtime_context: Dict[str, Any] | None = None,
) -> Dict[str, Any]:
    scene_rows = []
    for item in scenes or []:
        if not isinstance(item, dict):
            continue
        scene_key = _text(item.get("code") or item.get("key"))
        if not scene_key:
            continue
        scene_rows.append(item)
    scene_rows.sort(key=lambda row: _text(row.get("code") or row.get("key")))
    scene_catalog = _scene_switch_catalog(scene_rows)

    entries = [
        _scene_ready_entry(
            row,
            runtime_context=runtime_context,
            action_surface_strategy=action_surface_strategy,
            scene_catalog=scene_catalog,
        )
        for row in scene_rows
    ]
    role_payload = role_surface if isinstance(role_surface, dict) else {}
    landing_scene_key = _text(role_payload.get("landing_scene_key"))
    if not landing_scene_key and entries:
        landing_scene_key = _text((entries[0].get("scene") or {}).get("key"))

    base_bound_scene_count = 0
    compile_issue_scene_count = 0
    for entry in entries:
        meta = entry.get("meta") if isinstance(entry.get("meta"), dict) else {}
        verdict = meta.get("compile_verdict") if isinstance(meta.get("compile_verdict"), dict) else {}
        if bool(verdict.get("base_contract_bound")):
            base_bound_scene_count += 1
        if not bool(verdict.get("ok", False)):
            compile_issue_scene_count += 1

    return {
        "contract_version": "v1",
        "schema_version": "scene_ready_contract_v1",
        "scene_version": _text(scene_version),
        "source_schema_version": _text(schema_version),
        "scene_channel": _text(scene_channel),
        "active_scene_key": landing_scene_key,
        "scenes": entries,
        "meta": {
            "generated_by": "smart_core.scene_ready_contract_builder",
            "source_authority": source_authority_contract(),
            "scene_count": len(entries),
            "mode": "dual_track",
            "base_contract_bound_scene_count": base_bound_scene_count,
            "compile_issue_scene_count": compile_issue_scene_count,
            "scene_type_consumption_metrics": _scene_type_consumption_metrics(entries),
        },
    }
