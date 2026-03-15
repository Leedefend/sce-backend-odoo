# -*- coding: utf-8 -*-
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Tuple


ALLOWED_ZONES = {"header", "toolbar", "search", "main", "sidebar", "footer"}


@dataclass
class CompileContext:
    scene_key: str
    ui_base_contract: Dict[str, Any]
    provider_registry: Dict[str, Any]


def _text(value: Any) -> str:
    return str(value or "").strip()


def _as_dict(value: Any) -> Dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _as_list(value: Any) -> List[Any]:
    return list(value) if isinstance(value, list) else []


def _resolve_path(payload: Dict[str, Any], path: str) -> Any:
    node: Any = payload
    for part in [seg for seg in path.split(".") if seg]:
        if not isinstance(node, dict) or part not in node:
            return None
        node = node.get(part)
    return node


def parse_scene_dsl(scene_payload: Dict[str, Any], scene_key: str) -> Dict[str, Any]:
    target = _as_dict(scene_payload.get("target"))
    zones_raw = _as_list(scene_payload.get("zones"))
    blocks_raw = _as_list(scene_payload.get("blocks"))
    actions_raw = _as_list(scene_payload.get("actions"))

    zones: List[Dict[str, Any]] = []
    for row in zones_raw:
        if isinstance(row, str):
            zones.append({"name": _text(row), "blocks": []})
        elif isinstance(row, dict):
            zones.append({
                "name": _text(row.get("name") or row.get("zone") or row.get("key")),
                "blocks": _as_list(row.get("blocks")),
            })

    if not zones:
        zones = [
            {"name": "header", "blocks": []},
            {"name": "main", "blocks": []},
        ]

    blocks: List[Dict[str, Any]] = []
    for row in blocks_raw:
        payload = _as_dict(row)
        if not payload:
            continue
        blocks.append({
            "type": _text(payload.get("type") or payload.get("block_type") or "list_block"),
            "zone": _text(payload.get("zone") or "main") or "main",
            "source": _text(payload.get("source") or "ui_base_contract.views.tree"),
            "provider": _text(payload.get("provider")),
            "model": _text(payload.get("model") or target.get("model")),
            "fields": _as_list(payload.get("fields")),
        })

    if not blocks:
        blocks.append(
            {
                "type": "list_block",
                "zone": "main",
                "source": "ui_base_contract.views.tree",
                "provider": "",
                "model": _text(target.get("model")),
                "fields": [],
            }
        )

    actions: List[Dict[str, Any]] = []
    for row in actions_raw:
        payload = _as_dict(row)
        if not payload:
            continue
        actions.append(
            {
                "key": _text(payload.get("key")),
                "label": _text(payload.get("label")),
                "intent": _text(payload.get("intent")),
                "placement": _text(payload.get("placement") or "toolbar") or "toolbar",
                "target": _as_dict(payload.get("target")),
            }
        )

    if not actions:
        action_id = int(target.get("action_id") or 0)
        route = _text(target.get("route"))
        if action_id > 0 or route:
            actions.append(
                {
                    "key": "open_scene",
                    "label": "打开场景",
                    "intent": "ui.contract",
                    "placement": "toolbar",
                    "target": {
                        "action_id": action_id if action_id > 0 else None,
                        "menu_id": int(target.get("menu_id") or 0) or None,
                        "route": route or None,
                    },
                }
            )

    return {
        "scene": {
            "key": scene_key,
            "title": _text(scene_payload.get("name") or scene_key),
            "layout": _as_dict(scene_payload.get("layout")),
        },
        "page": {
            "scene_key": scene_key,
            "route": _text(target.get("route")) or f"/s/{scene_key}",
            "zones": zones,
        },
        "blocks": blocks,
        "actions": actions,
        "search_surface": {
            "default_sort": _text(scene_payload.get("default_sort")),
            "filters": _as_list(scene_payload.get("filters")),
        },
        "permission_surface": _as_dict(scene_payload.get("access")),
        "workflow_surface": {},
        "meta": {
            "input_target": target,
            "input_tiles": _as_list(scene_payload.get("tiles")),
        },
    }


def grammar_validate(ast: Dict[str, Any]) -> Tuple[bool, List[str]]:
    issues: List[str] = []
    scene = _as_dict(ast.get("scene"))
    page = _as_dict(ast.get("page"))
    if not _text(scene.get("key")):
        issues.append("scene.key is required")
    zones = _as_list(page.get("zones"))
    for row in zones:
        payload = _as_dict(row)
        name = _text(payload.get("name"))
        if not name:
            issues.append("zone.name is required")
            continue
        if name not in ALLOWED_ZONES:
            issues.append(f"invalid zone name: {name}")
    blocks = _as_list(ast.get("blocks"))
    for row in blocks:
        payload = _as_dict(row)
        if not _text(payload.get("type")):
            issues.append("block.type is required")
    return len(issues) == 0, issues


def semantic_validate(ast: Dict[str, Any], ctx: CompileContext) -> Tuple[bool, List[str]]:
    issues: List[str] = []
    blocks = _as_list(ast.get("blocks"))
    for row in blocks:
        payload = _as_dict(row)
        provider = _text(payload.get("provider"))
        source = _text(payload.get("source"))
        if provider and provider not in ctx.provider_registry:
            issues.append(f"provider not registered: {provider}")
        if source.startswith("ui_base_contract") and not ctx.ui_base_contract:
            issues.append("ui_base_contract missing for source binding")
    return len(issues) == 0, issues


def context_bind(ast: Dict[str, Any], ctx: CompileContext) -> Dict[str, Any]:
    bound = dict(ast)
    blocks_out: List[Dict[str, Any]] = []
    base_bound_count = 0
    for row in _as_list(ast.get("blocks")):
        payload = dict(_as_dict(row))
        source = _text(payload.get("source"))
        bound_source = None
        if source.startswith("ui_base_contract") and ctx.ui_base_contract:
            normalized = source.replace("ui_base_contract.", "", 1)
            bound_source = _resolve_path(ctx.ui_base_contract, normalized)
            if bound_source is not None:
                base_bound_count += 1
        payload["bound_source"] = bound_source
        blocks_out.append(payload)
    bound["blocks"] = blocks_out
    meta = _as_dict(bound.get("meta"))
    meta["binding"] = {
        "base_contract_bound_block_count": base_bound_count,
        "block_count": len(blocks_out),
    }
    bound["meta"] = meta
    return bound


def generate_surfaces(bound_ast: Dict[str, Any], ctx: CompileContext) -> Dict[str, Any]:
    out = dict(bound_ast)
    search_surface = _as_dict(out.get("search_surface"))
    permission_surface = _as_dict(out.get("permission_surface"))
    workflow_surface = _as_dict(out.get("workflow_surface"))

    if ctx.ui_base_contract:
        base_search = _as_dict(ctx.ui_base_contract.get("search"))
        base_permissions = _as_dict(ctx.ui_base_contract.get("permissions"))
        base_workflow = _as_dict(ctx.ui_base_contract.get("workflow"))
        if not search_surface.get("fields") and base_search:
            search_surface["fields"] = _as_list(base_search.get("fields"))
        if not permission_surface and base_permissions:
            permission_surface = dict(base_permissions)
        if not workflow_surface and base_workflow:
            workflow_surface = dict(base_workflow)

    out["search_surface"] = search_surface
    out["permission_surface"] = permission_surface
    out["workflow_surface"] = workflow_surface
    return out


def block_expand(bound_ast: Dict[str, Any]) -> Dict[str, Any]:
    out = dict(bound_ast)
    expanded_blocks: List[Dict[str, Any]] = []
    for row in _as_list(bound_ast.get("blocks")):
        payload = _as_dict(row)
        block_type = _text(payload.get("type"))
        expanded = {
            "block_type": "list" if block_type == "list_block" else block_type,
            "zone": _text(payload.get("zone") or "main") or "main",
            "model": _text(payload.get("model")),
            "provider": _text(payload.get("provider")) or None,
            "fields": _as_list(payload.get("fields")),
        }
        bound_source = payload.get("bound_source")
        if isinstance(bound_source, dict):
            src_fields = _as_list(bound_source.get("fields"))
            if src_fields and not expanded["fields"]:
                expanded["fields"] = src_fields
        expanded_blocks.append(expanded)
    out["blocks"] = expanded_blocks
    return out


def action_compile(bound_ast: Dict[str, Any]) -> Dict[str, Any]:
    out = dict(bound_ast)
    actions_out: List[Dict[str, Any]] = []
    for row in _as_list(bound_ast.get("actions")):
        payload = _as_dict(row)
        key = _text(payload.get("key"))
        if not key:
            continue
        actions_out.append(
            {
                "key": key,
                "label": _text(payload.get("label") or key),
                "intent": _text(payload.get("intent") or "ui.contract"),
                "placement": _text(payload.get("placement") or "toolbar") or "toolbar",
                "target": _as_dict(payload.get("target")),
            }
        )
    out["actions"] = actions_out
    return out


def scene_compile(scene_payload: Dict[str, Any], *, scene_key: str, ui_base_contract: Dict[str, Any] | None = None,
                  provider_registry: Dict[str, Any] | None = None) -> Dict[str, Any]:
    ctx = CompileContext(
        scene_key=scene_key,
        ui_base_contract=_as_dict(ui_base_contract),
        provider_registry=_as_dict(provider_registry),
    )
    ast = parse_scene_dsl(scene_payload, scene_key=scene_key)
    grammar_ok, grammar_issues = grammar_validate(ast)
    semantic_ok, semantic_issues = semantic_validate(ast, ctx)

    compiled = ast
    if grammar_ok and semantic_ok:
        compiled = context_bind(compiled, ctx)
        compiled = generate_surfaces(compiled, ctx)
        compiled = block_expand(compiled)
        compiled = action_compile(compiled)

    meta = _as_dict(compiled.get("meta"))
    meta["compile_pipeline"] = [
        "dsl_parser",
        "grammar_validator",
        "semantic_validator",
        "context_binder",
        "surface_generator",
        "block_expansion",
        "action_compiler",
        "scene_compiler",
    ]
    meta["compile_verdict"] = {
        "ok": bool(grammar_ok and semantic_ok),
        "grammar_ok": bool(grammar_ok),
        "semantic_ok": bool(semantic_ok),
        "grammar_issues": grammar_issues,
        "semantic_issues": semantic_issues,
        "base_contract_bound": bool(_as_dict(meta.get("binding")).get("base_contract_bound_block_count", 0)),
    }
    compiled["meta"] = meta
    return {
        "scene": _as_dict(compiled.get("scene")),
        "page": _as_dict(compiled.get("page")),
        "blocks": _as_list(compiled.get("blocks")),
        "actions": _as_list(compiled.get("actions")),
        "search_surface": _as_dict(compiled.get("search_surface")),
        "workflow_surface": _as_dict(compiled.get("workflow_surface")),
        "permission_surface": _as_dict(compiled.get("permission_surface")),
        "meta": _as_dict(compiled.get("meta")),
    }
