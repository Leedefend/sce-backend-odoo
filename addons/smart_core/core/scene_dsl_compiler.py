# -*- coding: utf-8 -*-
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Tuple

try:
    from .scene_merge_resolver import (
        MergeContext,
        apply_permission_gate,
        apply_policy,
        apply_profile,
        apply_provider_merge,
    )
except Exception:  # pragma: no cover - guard loader fallback
    import importlib.util
    from pathlib import Path

    _resolver_path = Path(__file__).resolve().with_name("scene_merge_resolver.py")
    _resolver_spec = importlib.util.spec_from_file_location("scene_merge_resolver_fallback", _resolver_path)
    if _resolver_spec is None or _resolver_spec.loader is None:
        raise RuntimeError(f"unable to load resolver: {_resolver_path}")
    _resolver_module = importlib.util.module_from_spec(_resolver_spec)
    import sys

    sys.modules[_resolver_spec.name] = _resolver_module
    _resolver_spec.loader.exec_module(_resolver_module)

    MergeContext = _resolver_module.MergeContext
    apply_permission_gate = _resolver_module.apply_permission_gate
    apply_policy = _resolver_module.apply_policy
    apply_profile = _resolver_module.apply_profile
    apply_provider_merge = _resolver_module.apply_provider_merge


ALLOWED_ZONES = {"header", "toolbar", "search", "main", "sidebar", "footer"}


@dataclass
class CompileContext:
    scene_key: str
    ui_base_contract: Dict[str, Any]
    provider_registry: Dict[str, Any]
    profile: Dict[str, Any]
    policies: Dict[str, Any]
    providers: List[Dict[str, Any]]
    runtime: Dict[str, Any]


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


def _normalize_providers(raw: Any) -> List[Dict[str, Any]]:
    out: List[Dict[str, Any]] = []
    for row in _as_list(raw):
        if isinstance(row, str):
            key = _text(row)
            if key:
                out.append({"key": key})
            continue
        payload = _as_dict(row)
        if not payload:
            continue
        key = _text(payload.get("key") or payload.get("provider"))
        item = dict(payload)
        if key:
            item["key"] = key
        out.append(item)
    return out


def _extract_base_action_candidates(ui_base_contract: Dict[str, Any]) -> List[Dict[str, Any]]:
    candidates: List[Dict[str, Any]] = []
    actions_root = ui_base_contract.get("actions")
    if isinstance(actions_root, list):
        candidates.extend([_as_dict(row) for row in actions_root if isinstance(row, dict)])
    elif isinstance(actions_root, dict):
        for key in ("toolbar", "buttons", "items"):
            for row in _as_list(actions_root.get(key)):
                if isinstance(row, dict):
                    candidates.append(row)

    for key in ("toolbar", "buttons"):
        root = ui_base_contract.get(key)
        if isinstance(root, list):
            for row in root:
                if isinstance(row, dict):
                    candidates.append(row)
        elif isinstance(root, dict):
            for nested in ("items", "actions", "buttons"):
                for row in _as_list(root.get(nested)):
                    if isinstance(row, dict):
                        candidates.append(row)

    dedup: List[Dict[str, Any]] = []
    seen: set[str] = set()
    for row in candidates:
        key = _text(row.get("key") or row.get("name") or row.get("id"))
        if not key or key in seen:
            continue
        seen.add(key)
        dedup.append(row)
    return dedup


def _normalize_field_names(raw_fields: List[Any]) -> List[str]:
    names: List[str] = []
    for item in raw_fields:
        if isinstance(item, str):
            key = _text(item)
        elif isinstance(item, dict):
            payload = _as_dict(item)
            key = _text(payload.get("name") or payload.get("field") or payload.get("key"))
        else:
            key = ""
        if key:
            names.append(key)
    dedup: List[str] = []
    seen: set[str] = set()
    for key in names:
        if key in seen:
            continue
        seen.add(key)
        dedup.append(key)
    return dedup


def _infer_scene_type(bound_ast: Dict[str, Any], ctx: CompileContext) -> str:
    scene = _as_dict(bound_ast.get("scene"))
    layout = _as_dict(scene.get("layout"))
    scene_key = _text(scene.get("key") or ctx.scene_key).lower()
    layout_kind = _text(layout.get("kind") or layout.get("mode") or layout.get("type")).lower()
    if layout_kind in {"list", "form", "kanban", "workspace", "ledger", "record"}:
        return layout_kind
    block_types = {
        _infer_block_type(_as_dict(row))
        for row in _as_list(bound_ast.get("blocks"))
    }
    if "form" in block_types:
        return "form"
    if "kanban" in block_types:
        return "kanban"
    if scene_key.startswith("workspace.") or "workspace" in scene_key:
        return "workspace"
    return "list"


def _collect_block_field_scope(bound_ast: Dict[str, Any]) -> List[str]:
    names: List[str] = []
    for row in _as_list(bound_ast.get("blocks")):
        payload = _as_dict(row)
        names.extend(_normalize_field_names(_as_list(payload.get("fields"))))
        bound_source = _as_dict(payload.get("bound_source"))
        names.extend(_normalize_field_names(_as_list(bound_source.get("fields"))))
    return _normalize_field_names(names)


def _collect_explicit_form_field_scope(bound_ast: Dict[str, Any]) -> List[str]:
    names: List[str] = []
    for row in _as_list(bound_ast.get("blocks")):
        payload = _as_dict(row)
        if _infer_block_type(payload) != "form":
            continue
        names.extend(_normalize_field_names(_as_list(payload.get("fields"))))
    return _normalize_field_names(names)


def _shape_search_surface(scene_type: str, base: Dict[str, Any]) -> Dict[str, Any]:
    out = dict(base)
    if scene_type in {"form", "record"}:
        out["group_by"] = []
    elif scene_type == "workspace":
        out["fields"] = []
        out["group_by"] = []
        out["filters"] = _as_list(out.get("filters"))[:8]
    return out


def _shape_workflow_surface(scene_type: str, base: Dict[str, Any]) -> Dict[str, Any]:
    out = dict(base)
    if scene_type == "workspace":
        out["transitions"] = []
    return out


def _shape_validation_surface(scene_type: str, base: Dict[str, Any], field_scope: List[str]) -> Dict[str, Any]:
    out = dict(base)
    required_fields = _normalize_field_names(_as_list(out.get("required_fields")))
    if scene_type in {"form", "record"} and field_scope:
        scoped_set = set(field_scope)
        scoped = [name for name in required_fields if name in scoped_set]
        out["required_fields"] = scoped or required_fields
    elif scene_type not in {"form", "record"}:
        out["required_fields"] = []
    return out


def _shape_base_actions(scene_type: str, candidates: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    if scene_type == "workspace":
        preferred = []
        fallback = []
        for row in candidates:
            payload = _as_dict(row)
            placement = _text(payload.get("placement")).lower()
            if placement in {"toolbar", "header", "primary"}:
                preferred.append(payload)
            else:
                fallback.append(payload)
        return preferred or fallback
    return candidates


def _infer_block_type(payload: Dict[str, Any]) -> str:
    block_type = _text(payload.get("type") or payload.get("block_type"))
    source = _text(payload.get("source"))
    if block_type in {"form_block", "form"} or source.endswith(".form"):
        return "form"
    if block_type in {"kanban_block", "kanban"} or source.endswith(".kanban"):
        return "kanban"
    if block_type in {"list_block", "tree_block", "list", "tree"} or source.endswith(".tree"):
        return "list"
    return block_type or "list"


def _infer_intent_from_action(payload: Dict[str, Any]) -> str:
    explicit = _text(payload.get("intent"))
    if explicit:
        return explicit

    key = _text(payload.get("key") or payload.get("name") or payload.get("id")).lower()
    label = _text(payload.get("label") or payload.get("string")).lower()
    action_type = _text(payload.get("type") or payload.get("action_type")).lower()
    token = f"{key} {label} {action_type}".strip()

    if any(flag in token for flag in ("create", "new", "add", "新增", "创建")):
        return "record.create"
    if any(flag in token for flag in ("edit", "update", "write", "编辑", "更新")):
        return "record.update"
    if any(flag in token for flag in ("delete", "remove", "unlink", "删除", "移除")):
        return "record.delete"
    if any(flag in token for flag in ("export", "导出")):
        return "record.export"
    if any(flag in token for flag in ("import", "导入")):
        return "record.import"
    if any(flag in token for flag in ("approve", "confirm", "批准", "确认")):
        return "workflow.approve"
    if any(flag in token for flag in ("submit", "提交")):
        return "workflow.submit"
    if any(flag in token for flag in ("reject", "驳回")):
        return "workflow.reject"
    if any(flag in token for flag in ("cancel", "作废", "取消")):
        return "workflow.cancel"
    if any(flag in token for flag in ("search", "filter", "查询", "筛选")):
        return "record.search"
    return "ui.contract"


def _infer_action_tier(scene_type: str, payload: Dict[str, Any]) -> str:
    placement = _text(payload.get("placement")).lower()
    key = _text(payload.get("key") or payload.get("name")).lower()
    intent = _text(payload.get("intent")).lower()

    if placement in {"context", "row", "inline", "menu"}:
        return "contextual"
    if placement in {"primary", "header", "toolbar"}:
        return "primary"
    if scene_type == "workspace":
        if any(token in key for token in ("open", "create", "launch")):
            return "primary"
        return "secondary"
    if scene_type in {"form", "record"}:
        if any(token in key for token in ("save", "submit", "approve", "confirm")):
            return "primary"
        if any(token in intent for token in ("submit", "approve", "confirm", "update")):
            return "primary"
    if scene_type in {"list", "kanban", "ledger"}:
        if any(token in key for token in ("create", "new", "import", "export", "search")):
            return "primary"
    return "secondary"


def _ensure_action_density(scene_type: str, actions: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    target_min = 2 if scene_type in {"list", "form", "workspace", "record", "ledger"} else 1
    if len(actions) >= target_min:
        return actions
    seen = {_text(_as_dict(row).get("key")) for row in actions if _text(_as_dict(row).get("key"))}
    fillers: List[Dict[str, Any]] = [
        {
            "key": "quick_search",
            "label": "快速检索",
            "intent": "record.search",
            "placement": "toolbar",
            "tier": "secondary",
            "target": {},
        },
        {
            "key": "open_help",
            "label": "使用指引",
            "intent": "ui.contract",
            "placement": "toolbar",
            "tier": "secondary",
            "target": {},
        },
    ]
    out = list(actions)
    for row in fillers:
        key = _text(row.get("key"))
        if not key or key in seen:
            continue
        out.append(row)
        seen.add(key)
        if len(out) >= target_min:
            break
    return out


def _build_action_surface(scene_type: str, actions: List[Dict[str, Any]]) -> Dict[str, Any]:
    primary: List[Dict[str, Any]] = []
    secondary: List[Dict[str, Any]] = []
    contextual: List[Dict[str, Any]] = []
    for row in actions:
        payload = _as_dict(row)
        tier = _text(payload.get("tier")) or _infer_action_tier(scene_type, payload)
        if tier == "primary":
            primary.append(payload)
        elif tier == "contextual":
            contextual.append(payload)
        else:
            secondary.append(payload)

    if scene_type == "workspace" and len(primary) > 3:
        secondary = primary[3:] + secondary
        primary = primary[:3]

    return {
        "scene_type": scene_type,
        "primary": primary,
        "secondary": secondary,
        "contextual": contextual,
        "counts": {
            "primary": len(primary),
            "secondary": len(secondary),
            "contextual": len(contextual),
            "total": len(actions),
        },
    }


def _normalize_action_key_list(payload: Dict[str, Any], keys: tuple[str, ...]) -> List[str]:
    rows: List[str] = []
    for key in keys:
        rows.extend([_text(item) for item in _as_list(payload.get(key)) if _text(item)])
    dedup: List[str] = []
    seen: set[str] = set()
    for item in rows:
        if item in seen:
            continue
        seen.add(item)
        dedup.append(item)
    return dedup


def _merge_action_surface_strategy(base: Dict[str, Any], ext: Dict[str, Any]) -> Dict[str, Any]:
    out = dict(base)
    if not ext:
        return out
    out["force_primary_keys"] = _normalize_action_key_list(ext, ("force_primary_keys", "primary_keys")) or _as_list(base.get("force_primary_keys"))
    out["force_secondary_keys"] = _normalize_action_key_list(ext, ("force_secondary_keys", "secondary_keys")) or _as_list(base.get("force_secondary_keys"))
    out["force_contextual_keys"] = _normalize_action_key_list(ext, ("force_contextual_keys", "contextual_keys")) or _as_list(base.get("force_contextual_keys"))
    out["hide_keys"] = _normalize_action_key_list(ext, ("hide_keys", "hidden_keys", "force_hide_keys")) or _as_list(base.get("hide_keys"))
    return out


def _resolve_action_surface_strategy(runtime: Dict[str, Any]) -> Dict[str, Any]:
    payload = _as_dict(runtime.get("action_surface_strategy"))
    role_code = _text(runtime.get("role_code") or runtime.get("roleCode")).lower()
    company_id = int(runtime.get("company_id") or runtime.get("companyId") or 0)
    company_key = str(company_id) if company_id > 0 else ""

    base = _merge_action_surface_strategy(
        {
            "force_primary_keys": [],
            "force_secondary_keys": [],
            "force_contextual_keys": [],
            "hide_keys": [],
        },
        _as_dict(payload.get("default")),
    )
    resolved = dict(base)
    by_company = _as_dict(payload.get("by_company"))
    by_role = _as_dict(payload.get("by_role"))
    by_company_role = _as_dict(payload.get("by_company_role"))
    if company_key and company_key in by_company:
        resolved = _merge_action_surface_strategy(resolved, _as_dict(by_company.get(company_key)))
    if role_code and role_code in by_role:
        resolved = _merge_action_surface_strategy(resolved, _as_dict(by_role.get(role_code)))
    if company_key and role_code:
        scoped_key = f"{company_key}:{role_code}"
        if scoped_key in by_company_role:
            resolved = _merge_action_surface_strategy(resolved, _as_dict(by_company_role.get(scoped_key)))
    return resolved


def _apply_action_surface_strategy(actions: List[Dict[str, Any]], strategy: Dict[str, Any]) -> List[Dict[str, Any]]:
    hide_keys = set(_normalize_action_key_list(strategy, ("hide_keys",)))
    primary_keys = set(_normalize_action_key_list(strategy, ("force_primary_keys",)))
    secondary_keys = set(_normalize_action_key_list(strategy, ("force_secondary_keys",)))
    contextual_keys = set(_normalize_action_key_list(strategy, ("force_contextual_keys",)))
    out: List[Dict[str, Any]] = []
    for row in actions:
        payload = dict(_as_dict(row))
        key = _text(payload.get("key"))
        if key and key in hide_keys:
            continue
        if key and key in contextual_keys:
            payload["tier"] = "contextual"
        elif key and key in primary_keys:
            payload["tier"] = "primary"
        elif key and key in secondary_keys:
            payload["tier"] = "secondary"
        out.append(payload)
    return out


def _resolve_effective_rights(permission_surface: Dict[str, Any]) -> Dict[str, bool]:
    effective = _as_dict(permission_surface.get("effective"))
    rights = _as_dict(effective.get("rights"))
    create = bool(rights.get("create", permission_surface.get("create", True)))
    write = bool(rights.get("write", permission_surface.get("write", True)))
    unlink = bool(rights.get("unlink", rights.get("delete", permission_surface.get("delete", True))))
    return {"create": create, "write": write, "unlink": unlink}


def _workflow_action_allowed(action: Dict[str, Any], workflow_surface: Dict[str, Any], runtime: Dict[str, Any]) -> bool:
    intent = _text(action.get("intent")).lower()
    key = _text(action.get("key")).lower()
    if not intent.startswith("workflow.") and not any(token in key for token in ("approve", "submit", "reject", "cancel")):
        return True
    transitions: List[str] = []
    for row in _as_list(workflow_surface.get("transitions")):
        if isinstance(row, dict):
            payload = _as_dict(row)
            transition_key = _text(payload.get("key") or payload.get("name") or payload.get("id")).lower()
            transition_intent = _text(payload.get("intent")).lower()
            from_state = _text(payload.get("from") or payload.get("from_state") or payload.get("source")).lower()
            to_state = _text(payload.get("to") or payload.get("to_state") or payload.get("target")).lower()
            if transition_key:
                transitions.append(transition_key)
            if transition_intent:
                transitions.append(transition_intent)
                if transition_intent.startswith("workflow."):
                    transitions.append(transition_intent.split(".")[-1])
            if from_state and to_state:
                transitions.append(f"{from_state}->{to_state}")
            continue
        token = _text(row).lower()
        if token:
            transitions.append(token)
    if not transitions:
        return True
    target = intent.split(".")[-1] if intent.startswith("workflow.") else key
    state = _text(_as_dict(runtime).get("current_state")).lower()
    if state and f"{state}->{target}" in transitions:
        return True
    return any(target in row for row in transitions)


def action_permission_workflow_gate(compiled_ast: Dict[str, Any], ctx: CompileContext) -> Dict[str, Any]:
    out = dict(compiled_ast)
    actions = [_as_dict(row) for row in _as_list(out.get("actions")) if isinstance(row, dict)]
    permission_surface = _as_dict(out.get("permission_surface"))
    workflow_surface = _as_dict(out.get("workflow_surface"))
    allowed = bool(permission_surface.get("allowed", True))
    rights = _resolve_effective_rights(permission_surface)

    if not allowed:
        filtered: List[Dict[str, Any]] = []
    else:
        filtered = []
        for row in actions:
            intent = _text(row.get("intent")).lower()
            if intent == "record.create" and not rights["create"]:
                continue
            if intent in {"record.update", "record.edit"} and not rights["write"]:
                continue
            if intent in {"record.delete", "record.unlink"} and not rights["unlink"]:
                continue
            if not _workflow_action_allowed(row, workflow_surface, _as_dict(ctx.runtime)):
                continue
            filtered.append(row)

    strategy = _resolve_action_surface_strategy(_as_dict(ctx.runtime))
    filtered = _apply_action_surface_strategy(filtered, strategy)
    out["actions"] = filtered
    scene_type = _text(_as_dict(_as_dict(out.get("meta")).get("surface_profile")).get("scene_type")) or "list"
    out["action_surface"] = _build_action_surface(scene_type, filtered)
    meta = _as_dict(out.get("meta"))
    meta["action_runtime_gate"] = {
        "allowed": allowed,
        "before": len(actions),
        "after": len(filtered),
        "filtered_count": max(len(actions) - len(filtered), 0),
        "rights": rights,
        "strategy_applied": bool(
            _as_list(strategy.get("force_primary_keys"))
            or _as_list(strategy.get("force_secondary_keys"))
            or _as_list(strategy.get("force_contextual_keys"))
            or _as_list(strategy.get("hide_keys"))
        ),
        "strategy": strategy,
    }
    meta["action_surface_counts"] = _as_dict(_as_dict(out.get("action_surface")).get("counts"))
    out["meta"] = meta
    return out


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


def profile_apply(bound_ast: Dict[str, Any], ctx: CompileContext) -> Dict[str, Any]:
    return apply_profile(bound_ast, _as_dict(ctx.profile))


def policy_apply(compiled_ast: Dict[str, Any], ctx: CompileContext) -> Dict[str, Any]:
    return apply_policy(compiled_ast, _as_dict(ctx.policies), _as_dict(ctx.runtime))


def _resolve_provider_payload(provider: Dict[str, Any], ctx: CompileContext, compiled_ast: Dict[str, Any]) -> Dict[str, Any]:
    key = _text(provider.get("key"))
    inline_payload = _as_dict(provider.get("payload"))
    if inline_payload:
        return inline_payload
    if not key:
        return {}
    entry = ctx.provider_registry.get(key)
    if callable(entry):
        try:
            payload = entry(scene_key=ctx.scene_key, runtime=_as_dict(ctx.runtime), context={"ast": compiled_ast})
        except Exception:
            return {}
        return _as_dict(payload)
    return _as_dict(entry)


def provider_merge(compiled_ast: Dict[str, Any], ctx: CompileContext) -> Dict[str, Any]:
    merge_ctx = MergeContext(
        scene_key=ctx.scene_key,
        runtime=_as_dict(ctx.runtime),
        provider_registry=_as_dict(ctx.provider_registry),
    )
    return apply_provider_merge(compiled_ast, _as_list(ctx.providers), merge_ctx)


def permission_workflow_gate(compiled_ast: Dict[str, Any]) -> Dict[str, Any]:
    return apply_permission_gate(compiled_ast)


def generate_surfaces(bound_ast: Dict[str, Any], ctx: CompileContext) -> Dict[str, Any]:
    out = dict(bound_ast)
    search_surface = _as_dict(out.get("search_surface"))
    permission_surface = _as_dict(out.get("permission_surface"))
    workflow_surface = _as_dict(out.get("workflow_surface"))
    validation_surface = _as_dict(out.get("validation_surface"))
    meta = _as_dict(out.get("meta"))
    scene_type = _infer_scene_type(bound_ast, ctx)
    field_scope = _collect_block_field_scope(bound_ast)
    explicit_form_field_scope = _collect_explicit_form_field_scope(bound_ast)

    if ctx.ui_base_contract:
        base_views = _as_dict(ctx.ui_base_contract.get("views"))
        base_fields = _as_dict(ctx.ui_base_contract.get("fields"))
        base_search = _as_dict(ctx.ui_base_contract.get("search"))
        base_permissions = _as_dict(ctx.ui_base_contract.get("permissions"))
        base_workflow = _as_dict(ctx.ui_base_contract.get("workflow"))
        base_validator = _as_dict(ctx.ui_base_contract.get("validator") or ctx.ui_base_contract.get("validation"))
        base_action_candidates = _extract_base_action_candidates(ctx.ui_base_contract)

        if not search_surface.get("fields") and base_search:
            search_surface["fields"] = _as_list(base_search.get("fields"))
        if not search_surface.get("filters") and base_search:
            search_surface["filters"] = _as_list(base_search.get("filters"))
        if not search_surface.get("group_by") and base_search:
            search_surface["group_by"] = _as_list(base_search.get("group_by"))
        if not search_surface.get("searchpanel") and base_search:
            search_surface["searchpanel"] = _as_list(base_search.get("searchpanel"))
        if not search_surface.get("mode") and base_search.get("mode"):
            search_surface["mode"] = base_search.get("mode")
        if not permission_surface and base_permissions:
            permission_surface = dict(base_permissions)
        if not workflow_surface and base_workflow:
            workflow_surface = dict(base_workflow)

        if base_validator and not validation_surface:
            validation_surface = dict(base_validator)

        base_action_candidates = _shape_base_actions(scene_type, base_action_candidates)
        meta["base_facts"] = {
            "views": bool(base_views),
            "fields": bool(base_fields),
            "search": bool(base_search),
            "permissions": bool(base_permissions),
            "workflow": bool(base_workflow),
            "validator": bool(base_validator),
            "actions": bool(base_action_candidates),
        }
        if base_action_candidates:
            out["base_action_candidates"] = base_action_candidates

    search_surface = _shape_search_surface(scene_type, search_surface)
    workflow_surface = _shape_workflow_surface(scene_type, workflow_surface)
    validation_scope = explicit_form_field_scope if explicit_form_field_scope else field_scope
    validation_surface = _shape_validation_surface(scene_type, validation_surface, validation_scope)
    meta["surface_profile"] = {
        "scene_type": scene_type,
        "field_scope_count": len(field_scope),
        "search_filter_count": len(_as_list(search_surface.get("filters"))),
        "search_group_by_count": len(_as_list(search_surface.get("group_by"))),
        "search_searchpanel_count": len(_as_list(search_surface.get("searchpanel"))),
        "workflow_transition_count": len(_as_list(workflow_surface.get("transitions"))),
        "validation_required_count": len(_as_list(validation_surface.get("required_fields"))),
        "base_action_candidate_count": len(_as_list(out.get("base_action_candidates"))),
    }

    out["search_surface"] = search_surface
    out["permission_surface"] = permission_surface
    out["workflow_surface"] = workflow_surface
    out["validation_surface"] = validation_surface
    out["meta"] = meta
    return out


def block_expand(bound_ast: Dict[str, Any], ctx: CompileContext | None = None) -> Dict[str, Any]:
    out = dict(bound_ast)
    expanded_blocks: List[Dict[str, Any]] = []
    base_fields = _as_dict(_as_dict(ctx.ui_base_contract).get("fields")) if ctx else {}
    for row in _as_list(bound_ast.get("blocks")):
        payload = _as_dict(row)
        block_type = _infer_block_type(payload)
        model = _text(payload.get("model"))
        if not model and ctx:
            model = _text(ctx.ui_base_contract.get("model"))
        expanded = {
            "block_type": block_type,
            "zone": _text(payload.get("zone") or "main") or "main",
            "model": model,
            "provider": _text(payload.get("provider")) or None,
            "fields": _normalize_field_names(_as_list(payload.get("fields"))),
        }
        bound_source = payload.get("bound_source")
        if isinstance(bound_source, dict):
            src_fields = _normalize_field_names(_as_list(bound_source.get("fields")))
            if src_fields and not expanded["fields"]:
                expanded["fields"] = src_fields

        if block_type == "form":
            expanded["form"] = {
                "field_count": len(expanded["fields"]),
                "fields": [
                    {
                        "name": key,
                        "type": _text(_as_dict(base_fields.get(key)).get("type")),
                        "readonly": bool(_as_dict(base_fields.get(key)).get("readonly", False)),
                        "required": bool(_as_dict(base_fields.get(key)).get("required", False)),
                    }
                    for key in expanded["fields"]
                ],
            }
        elif block_type == "kanban":
            expanded["kanban"] = {
                "field_count": len(expanded["fields"]),
                "has_template": bool(_as_dict(bound_source).get("template") or _as_dict(bound_source).get("arch")),
            }
        expanded_blocks.append(expanded)
    out["blocks"] = expanded_blocks
    return out


def action_compile(bound_ast: Dict[str, Any]) -> Dict[str, Any]:
    out = dict(bound_ast)
    scene_type = _text(_as_dict(_as_dict(out.get("meta")).get("surface_profile")).get("scene_type")) or "list"
    actions_out: List[Dict[str, Any]] = []
    seen_action_keys: set[str] = set()
    explicit_intent_count = 0
    mapped_intent_count = 0
    for row in _as_list(bound_ast.get("actions")):
        payload = _as_dict(row)
        key = _text(payload.get("key"))
        if not key:
            continue
        intent = _infer_intent_from_action(payload)
        if _text(payload.get("intent")):
            explicit_intent_count += 1
        else:
            mapped_intent_count += 1
        actions_out.append(
            {
                "key": key,
                "label": _text(payload.get("label") or key),
                "intent": intent,
                "placement": _text(payload.get("placement") or "toolbar") or "toolbar",
                "tier": _infer_action_tier(scene_type, payload),
                "target": _as_dict(payload.get("target")),
            }
        )
        seen_action_keys.add(key)

    for row in _as_list(bound_ast.get("base_action_candidates")):
        payload = _as_dict(row)
        key = _text(payload.get("key") or payload.get("name") or payload.get("id"))
        if not key or key in seen_action_keys:
            continue
        intent = _infer_intent_from_action(payload)
        if _text(payload.get("intent")):
            explicit_intent_count += 1
        else:
            mapped_intent_count += 1
        actions_out.append(
            {
                "key": key,
                "label": _text(payload.get("label") or payload.get("string") or key),
                "intent": intent,
                "placement": _text(payload.get("placement") or "toolbar") or "toolbar",
                "tier": _infer_action_tier(scene_type, payload),
                "target": _as_dict(payload.get("target")),
            }
        )
        seen_action_keys.add(key)

    actions_out = _ensure_action_density(scene_type, actions_out)
    out["actions"] = actions_out
    out["action_surface"] = _build_action_surface(scene_type, actions_out)
    meta = _as_dict(out.get("meta"))
    meta["action_intent_resolution"] = {
        "explicit_intent_count": explicit_intent_count,
        "mapped_intent_count": mapped_intent_count,
        "action_count": len(actions_out),
    }
    meta["action_surface_counts"] = _as_dict(_as_dict(out.get("action_surface")).get("counts"))
    out["meta"] = meta
    return out


def scene_compile(scene_payload: Dict[str, Any], *, scene_key: str, ui_base_contract: Dict[str, Any] | None = None,
                  provider_registry: Dict[str, Any] | None = None) -> Dict[str, Any]:
    ctx = CompileContext(
        scene_key=scene_key,
        ui_base_contract=_as_dict(ui_base_contract),
        provider_registry=_as_dict(provider_registry),
        profile=_as_dict(scene_payload.get("profile")),
        policies=_as_dict(scene_payload.get("policies") or scene_payload.get("policy")),
        providers=_normalize_providers(scene_payload.get("providers")),
        runtime=_as_dict(scene_payload.get("runtime")),
    )
    ast = parse_scene_dsl(scene_payload, scene_key=scene_key)
    grammar_ok, grammar_issues = grammar_validate(ast)
    semantic_ok, semantic_issues = semantic_validate(ast, ctx)

    compiled = ast
    if grammar_ok and semantic_ok:
        compiled = context_bind(compiled, ctx)
        compiled = profile_apply(compiled, ctx)
        compiled = policy_apply(compiled, ctx)
        compiled = provider_merge(compiled, ctx)
        compiled = generate_surfaces(compiled, ctx)
        compiled = permission_workflow_gate(compiled)
        compiled = block_expand(compiled, ctx)
        compiled = action_compile(compiled)
        compiled = action_permission_workflow_gate(compiled, ctx)

    meta = _as_dict(compiled.get("meta"))
    meta["compile_pipeline"] = [
        "dsl_parser",
        "grammar_validator",
        "semantic_validator",
        "context_binder",
        "profile_apply",
        "policy_apply",
        "provider_merge",
        "surface_generator",
        "permission_workflow_gate",
        "block_expansion",
        "action_compiler",
        "action_permission_workflow_gate",
        "scene_compiler",
    ]
    binding_meta = _as_dict(meta.get("binding"))
    base_facts_meta = _as_dict(meta.get("base_facts"))
    base_contract_bound = bool(binding_meta.get("base_contract_bound_block_count", 0)) or any(
        bool(base_facts_meta.get(key))
        for key in ("views", "fields", "search", "permissions", "workflow", "validator", "actions")
    ) or bool(ctx.ui_base_contract)
    meta["compile_verdict"] = {
        "ok": bool(grammar_ok and semantic_ok),
        "grammar_ok": bool(grammar_ok),
        "semantic_ok": bool(semantic_ok),
        "grammar_issues": grammar_issues,
        "semantic_issues": semantic_issues,
        "base_contract_bound": base_contract_bound,
    }
    compiled["meta"] = meta
    return {
        "scene": _as_dict(compiled.get("scene")),
        "page": _as_dict(compiled.get("page")),
        "blocks": _as_list(compiled.get("blocks")),
        "actions": _as_list(compiled.get("actions")),
        "action_surface": _as_dict(compiled.get("action_surface")),
        "search_surface": _as_dict(compiled.get("search_surface")),
        "workflow_surface": _as_dict(compiled.get("workflow_surface")),
        "permission_surface": _as_dict(compiled.get("permission_surface")),
        "validation_surface": _as_dict(compiled.get("validation_surface")),
        "meta": _as_dict(compiled.get("meta")),
    }
