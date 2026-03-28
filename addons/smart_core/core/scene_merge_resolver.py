# -*- coding: utf-8 -*-
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List


def _text(value: Any) -> str:
    return str(value or "").strip()


def _as_dict(value: Any) -> Dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _as_list(value: Any) -> List[Any]:
    return list(value) if isinstance(value, list) else []


@dataclass
class MergeContext:
    scene_key: str
    runtime: Dict[str, Any]
    provider_registry: Dict[str, Any]


def _record_conflict(meta: Dict[str, Any], *, layer: str, field: str, from_layer: str) -> None:
    resolver = _as_dict(meta.get("merge_resolver"))
    conflicts = _as_list(resolver.get("conflicts"))
    conflicts.append(
        {
            "layer": layer,
            "field": field,
            "overrides": from_layer,
        }
    )
    resolver["conflicts"] = conflicts
    resolver["conflict_count"] = len(conflicts)
    resolver["priority"] = ["platform", "base", "profile", "policy", "provider", "permission"]
    meta["merge_resolver"] = resolver


def apply_profile(compiled_ast: Dict[str, Any], profile: Dict[str, Any]) -> Dict[str, Any]:
    out = dict(compiled_ast)
    profile = _as_dict(profile)
    if not profile:
        return out

    scene = _as_dict(out.get("scene"))
    page = _as_dict(out.get("page"))

    title = _text(profile.get("title"))
    if title and scene.get("title") and scene.get("title") != title:
        _record_conflict(_as_dict(out.get("meta")), layer="profile", field="scene.title", from_layer="platform")
    if title:
        scene["title"] = title

    layout = _as_dict(profile.get("layout"))
    if layout:
        scene["layout"] = dict(layout)

    zones_profile = _as_list(profile.get("zones"))
    if zones_profile:
        zones: List[Dict[str, Any]] = []
        for row in zones_profile:
            if isinstance(row, str):
                zones.append({"name": _text(row), "blocks": []})
            elif isinstance(row, dict):
                zones.append(
                    {
                        "name": _text(row.get("name") or row.get("zone") or row.get("key")),
                        "blocks": _as_list(row.get("blocks")),
                    }
                )
        if zones:
            page["zones"] = zones

    out["scene"] = scene
    out["page"] = page
    meta = _as_dict(out.get("meta"))
    meta["profile"] = {
        "applied": True,
        "scene_type": _text(profile.get("scene_type")),
    }
    out["meta"] = meta
    return out


def apply_policy(compiled_ast: Dict[str, Any], policies: Dict[str, Any], runtime: Dict[str, Any]) -> Dict[str, Any]:
    out = dict(compiled_ast)
    policies = _as_dict(policies)
    if not policies:
        return out
    action_policy = _as_dict(policies.get("action_policy"))
    search_policy = _as_dict(policies.get("search_policy"))
    workflow_policy = _as_dict(policies.get("workflow_policy"))
    navigation_policy = _as_dict(policies.get("navigation_policy"))

    role_code = _text(_as_dict(runtime).get("role_code"))
    hidden_by_role = _as_dict(action_policy.get("hidden_by_role"))
    hidden_keys = {_text(item) for item in _as_list(hidden_by_role.get(role_code)) if _text(item)}
    if hidden_keys:
        actions = [row for row in _as_list(out.get("actions")) if _text(_as_dict(row).get("key")) not in hidden_keys]
        out["actions"] = actions

    search_surface = _as_dict(out.get("search_surface"))
    default_filters = _as_list(search_policy.get("default_filters"))
    if default_filters:
        if _as_list(search_surface.get("filters")):
            _record_conflict(_as_dict(out.get("meta")), layer="policy", field="search_surface.filters", from_layer="base")
        search_surface["filters"] = default_filters
    default_group_by = _as_list(search_policy.get("default_group_by"))
    if default_group_by:
        if _as_list(search_surface.get("group_by")):
            _record_conflict(_as_dict(out.get("meta")), layer="policy", field="search_surface.group_by", from_layer="base")
        search_surface["group_by"] = default_group_by
    default_searchpanel = _as_list(search_policy.get("default_searchpanel"))
    if default_searchpanel:
        if _as_list(search_surface.get("searchpanel")):
            _record_conflict(_as_dict(out.get("meta")), layer="policy", field="search_surface.searchpanel", from_layer="base")
        search_surface["searchpanel"] = default_searchpanel
    default_mode = _text(search_policy.get("default_mode"))
    if default_mode:
        if _text(search_surface.get("mode")):
            _record_conflict(_as_dict(out.get("meta")), layer="policy", field="search_surface.mode", from_layer="base")
        search_surface["mode"] = default_mode
    out["search_surface"] = search_surface

    workflow_surface = _as_dict(out.get("workflow_surface"))
    highlight_states = _as_list(workflow_policy.get("highlight_states"))
    if highlight_states:
        if _as_list(workflow_surface.get("highlight_states")):
            _record_conflict(_as_dict(out.get("meta")), layer="policy", field="workflow_surface.highlight_states", from_layer="base")
        workflow_surface["highlight_states"] = highlight_states
    out["workflow_surface"] = workflow_surface

    meta = _as_dict(out.get("meta"))
    meta["policy"] = {
        "applied": True,
        "hidden_action_count": len(hidden_keys),
        "navigation_priority": int(navigation_policy.get("priority") or 0),
    }
    out["meta"] = meta
    return out


def _resolve_provider_payload(provider: Dict[str, Any], ctx: MergeContext, compiled_ast: Dict[str, Any]) -> Dict[str, Any]:
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


def apply_provider_merge(compiled_ast: Dict[str, Any], providers: List[Dict[str, Any]], ctx: MergeContext) -> Dict[str, Any]:
    out = dict(compiled_ast)
    provider_hits: List[str] = []
    for provider in _as_list(providers):
        payload = _as_dict(provider)
        if not payload:
            continue
        key = _text(payload.get("key")) or "inline"
        resolved = _resolve_provider_payload(payload, ctx, out)
        if not resolved:
            continue
        if _as_list(resolved.get("blocks")):
            out["blocks"] = _as_list(out.get("blocks")) + _as_list(resolved.get("blocks"))
        if _as_list(resolved.get("actions")):
            out["actions"] = _as_list(out.get("actions")) + _as_list(resolved.get("actions"))

        search_surface = _as_dict(out.get("search_surface"))
        resolved_search = _as_dict(resolved.get("search_surface"))
        for field in ("filters", "group_by", "fields", "searchpanel", "mode"):
            if field in resolved_search and field in search_surface and search_surface.get(field) != resolved_search.get(field):
                _record_conflict(_as_dict(out.get("meta")), layer="provider", field=f"search_surface.{field}", from_layer="policy")
        search_surface.update(resolved_search)
        out["search_surface"] = search_surface

        workflow_surface = _as_dict(out.get("workflow_surface"))
        resolved_workflow = _as_dict(resolved.get("workflow_surface"))
        if "highlight_states" in resolved_workflow and workflow_surface.get("highlight_states") != resolved_workflow.get("highlight_states"):
            _record_conflict(_as_dict(out.get("meta")), layer="provider", field="workflow_surface.highlight_states", from_layer="policy")
        workflow_surface.update(resolved_workflow)
        out["workflow_surface"] = workflow_surface

        permission_surface = _as_dict(out.get("permission_surface"))
        resolved_permission = _as_dict(resolved.get("permission_surface"))
        if "allowed" in resolved_permission and permission_surface.get("allowed") != resolved_permission.get("allowed"):
            _record_conflict(_as_dict(out.get("meta")), layer="provider", field="permission_surface.allowed", from_layer="base")
        permission_surface.update(resolved_permission)
        out["permission_surface"] = permission_surface
        provider_hits.append(key)

    if provider_hits:
        meta = _as_dict(out.get("meta"))
        meta["provider"] = {
            "applied": True,
            "provider_hits": provider_hits,
        }
        out["meta"] = meta
    return out


def apply_permission_gate(compiled_ast: Dict[str, Any]) -> Dict[str, Any]:
    out = dict(compiled_ast)
    permission_surface = _as_dict(out.get("permission_surface"))
    actions = _as_list(out.get("actions"))
    allowed = bool(permission_surface.get("allowed", True))
    if not allowed and actions:
        out["actions"] = []
    meta = _as_dict(out.get("meta"))
    meta["permission_gate"] = {
        "allowed": allowed,
        "actions_pruned": len(actions) if (not allowed and actions) else 0,
    }
    out["meta"] = meta
    return out
