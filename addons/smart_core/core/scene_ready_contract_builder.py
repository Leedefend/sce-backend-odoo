# -*- coding: utf-8 -*-
from __future__ import annotations

from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path
from typing import Any, Dict, List
from odoo.addons.smart_core.core.scene_dsl_compiler import scene_compile
from odoo.addons.smart_core.core.ui_base_contract_adapter import adapt_ui_base_contract


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
                "title": "工作台：先处理高优先级行动",
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
            "primary_action": {"label": "返回工作台", "target": "/my-work"},
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
    merged_form_surface = _merge_form_surface(compiled_form_surface, seeded_form_surface)
    if _form_surface_nonempty(merged_form_surface):
        compiled["form_surface"] = merged_form_surface
    elif _form_surface_nonempty(seeded_form_surface):
        compiled["form_surface"] = seeded_form_surface
    optimization_composition = _normalize_optimization_composition(compiled)
    if _optimization_composition_nonempty(optimization_composition):
        compiled["optimization_composition"] = optimization_composition
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
            "scene_count": len(entries),
            "mode": "dual_track",
            "base_contract_bound_scene_count": base_bound_scene_count,
            "compile_issue_scene_count": compile_issue_scene_count,
            "scene_type_consumption_metrics": _scene_type_consumption_metrics(entries),
        },
    }
