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


def _scene_ready_entry(
    item: Dict[str, Any],
    *,
    runtime_context: Dict[str, Any] | None = None,
    action_surface_strategy: Dict[str, Any] | None = None,
) -> Dict[str, Any]:
    scene_key = _text(item.get("code") or item.get("key"))
    scene_payload = dict(item)

    if scene_key == "finance.payment_requests" and not isinstance(scene_payload.get("actions"), list):
        scene_payload["actions"] = [
            {
                "key": "approve_payment_request",
                "label": "批准",
                "intent": "record.update",
                "placement": "toolbar",
                "target": {
                    "mutation": {
                        "type": "transition",
                        "model": "finance.payment.request",
                        "operation": "approve",
                        "payload_schema": {
                            "required": ["record_id"],
                        },
                    },
                    "refresh_policy": {
                        "on_success": ["scene_projection", "workbench_projection"],
                        "scope": "local",
                    },
                },
            },
            {
                "key": "reject_payment_request",
                "label": "驳回",
                "intent": "record.update",
                "placement": "toolbar",
                "target": {
                    "mutation": {
                        "type": "transition",
                        "model": "finance.payment.request",
                        "operation": "reject",
                        "payload_schema": {
                            "required": ["record_id", "reason"],
                        },
                    },
                    "refresh_policy": {
                        "on_success": ["scene_projection", "workbench_projection"],
                        "scope": "local",
                    },
                },
            },
            {
                "key": "assign_payment_request",
                "label": "指派",
                "intent": "record.update",
                "placement": "toolbar",
                "target": {
                    "mutation": {
                        "type": "assign",
                        "model": "finance.payment.request",
                        "operation": "assign",
                        "payload_schema": {
                            "required": ["record_id", "assignee_id"],
                        },
                    },
                    "refresh_policy": {
                        "on_success": ["scene_projection", "workbench_projection"],
                        "scope": "local",
                    },
                },
            },
        ]

    if scene_key == "risk.center" and not isinstance(scene_payload.get("actions"), list):
        scene_payload["actions"] = [
            {
                "key": "claim_risk_action",
                "label": "认领",
                "intent": "record.update",
                "placement": "toolbar",
                "target": {
                    "mutation": {
                        "type": "transition",
                        "model": "project.risk.action",
                        "operation": "claim",
                        "payload_schema": {
                            "required": ["risk_action_id"],
                        },
                    },
                    "refresh_policy": {
                        "on_success": ["scene_projection", "workbench_projection"],
                        "scope": "local",
                    },
                },
            },
            {
                "key": "escalate_risk_action",
                "label": "升级",
                "intent": "record.update",
                "placement": "toolbar",
                "target": {
                    "mutation": {
                        "type": "transition",
                        "model": "project.risk.action",
                        "operation": "escalate",
                        "payload_schema": {
                            "required": ["risk_action_id", "note"],
                        },
                    },
                    "refresh_policy": {
                        "on_success": ["scene_projection", "workbench_projection"],
                        "scope": "local",
                    },
                },
            },
            {
                "key": "close_risk_action",
                "label": "关闭",
                "intent": "record.update",
                "placement": "toolbar",
                "target": {
                    "mutation": {
                        "type": "transition",
                        "model": "project.risk.action",
                        "operation": "close",
                        "payload_schema": {
                            "required": ["risk_action_id"],
                        },
                    },
                    "refresh_policy": {
                        "on_success": ["scene_projection", "workbench_projection"],
                        "scope": "local",
                    },
                },
            },
        ]

    base_contract_raw = item.get("ui_base_contract") if isinstance(item.get("ui_base_contract"), dict) else {}
    base_contract_adapted = adapt_ui_base_contract(base_contract_raw, scene_key=scene_key)
    ui_base_contract = (
        base_contract_adapted.get("normalized_contract")
        if isinstance(base_contract_adapted.get("normalized_contract"), dict)
        else {}
    )
    runtime_payload = scene_payload.get("runtime") if isinstance(scene_payload.get("runtime"), dict) else {}
    runtime_merged = dict(runtime_payload)
    runtime_ctx = runtime_context if isinstance(runtime_context, dict) else {}
    role_code = _text(runtime_ctx.get("role_code"))
    if role_code:
        runtime_merged["role_code"] = role_code
    company_id = int(runtime_ctx.get("company_id") or 0)
    if company_id > 0:
        runtime_merged["company_id"] = company_id
    strategy_payload = action_surface_strategy if isinstance(action_surface_strategy, dict) else {}
    if strategy_payload:
        runtime_merged["action_surface_strategy"] = strategy_payload

    scene_provider_payload = _resolve_scene_provider_payload(scene_key, runtime_ctx)
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

    next_scene_key = _text(item.get("next_scene") or item.get("next_scene_key"))
    next_scene_route = _text(item.get("next_scene_route"))
    if not next_scene_key and isinstance(item.get("runtime"), dict):
        next_scene_key = _text(item.get("runtime", {}).get("next_scene") or item.get("runtime", {}).get("next_scene_key"))
    if not next_scene_route and isinstance(item.get("runtime"), dict):
        next_scene_route = _text(item.get("runtime", {}).get("next_scene_route"))
    if not next_scene_key and isinstance(item.get("policies"), dict):
        nav_policy = item.get("policies", {}).get("navigation_policy") if isinstance(item.get("policies", {}).get("navigation_policy"), dict) else {}
        next_scene_key = _text(nav_policy.get("next_scene") or nav_policy.get("next_scene_key"))
        next_scene_route = next_scene_route or _text(nav_policy.get("next_scene_route"))

    if not next_scene_key and not next_scene_route:
        provider_next_key, provider_next_route = _resolve_next_scene_from_providers()
        next_scene_key = next_scene_key or provider_next_key
        next_scene_route = next_scene_route or provider_next_route

    if not next_scene_key and scene_key == "projects.intake":
        next_scene_key = "project.management"
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

    entries = [
        _scene_ready_entry(
            row,
            runtime_context=runtime_context,
            action_surface_strategy=action_surface_strategy,
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
