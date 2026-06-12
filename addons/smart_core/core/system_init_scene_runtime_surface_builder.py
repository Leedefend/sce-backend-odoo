# -*- coding: utf-8 -*-
from __future__ import annotations

from odoo.addons.smart_core.core.system_init_scene_runtime_semantic_bridge import (
    apply_system_init_scene_runtime_semantic_bridge,
)
from odoo.addons.smart_core.core.source_authority import build_source_authority_contract

SOURCE_KIND = "system_init_scene_runtime_surface_projection_builder"
SOURCE_AUTHORITIES = (
    "delivery_policy_runtime",
    "scene_ready_contract",
    "scene_navigation_contract",
    "ui_base_contract_asset_binding",
)
NO_BUSINESS_FACT_AUTHORITY = True


def _scene_ready_mode(params: dict | None) -> str:
    raw = str((params or {}).get("scene_ready_mode") or "").strip().lower()
    if raw in {"registry", "summary"}:
        return "registry"
    return "full"


def _as_int(value):
    try:
        number = int(value or 0)
    except (TypeError, ValueError):
        return None
    return number if number > 0 else None


def _build_scene_ready_registry_contract(
    scenes,
    *,
    scene_version=None,
    schema_version=None,
    scene_channel=None,
) -> dict:
    rows = []
    seen = set()
    for scene_row in scenes or []:
        if not isinstance(scene_row, dict):
            continue
        scene_key = str(scene_row.get("code") or scene_row.get("key") or "").strip()
        if not scene_key or scene_key in seen:
            continue
        seen.add(scene_key)
        target = scene_row.get("target") if isinstance(scene_row.get("target"), dict) else {}
        route = str(target.get("route") or scene_row.get("route") or f"/s/{scene_key}").strip()
        target_payload = {"route": route}
        for key in ("action_xmlid", "menu_xmlid", "model", "view_mode"):
            value = str(target.get(key) or scene_row.get(key) or "").strip()
            if value:
                target_payload[key] = value
        action_id = _as_int(target.get("action_id") or scene_row.get("action_id"))
        menu_id = _as_int(target.get("menu_id") or scene_row.get("menu_id"))
        if action_id:
            target_payload["action_id"] = action_id
        if menu_id:
            target_payload["menu_id"] = menu_id
        rows.append(
            {
                "scene": {
                    "key": scene_key,
                    "title": str(scene_row.get("name") or scene_row.get("title") or scene_key).strip(),
                },
                "page": {
                    "scene_key": scene_key,
                    "route": route,
                },
                "meta": {
                    "target": target_payload,
                    "mode": "registry",
                },
            }
        )
    return {
        "contract_version": "v1",
        "schema_version": "scene_ready_contract_v1",
        "source_schema_version": str(schema_version or ""),
        "scene_version": str(scene_version or ""),
        "scene_channel": str(scene_channel or ""),
        "scenes": rows,
        "meta": {
            "mode": "registry",
            "scene_count": len(rows),
            "generated_by": SOURCE_KIND,
        },
    }


def source_authority_contract() -> dict:
    return build_source_authority_contract(
        kind=SOURCE_KIND,
        authorities=SOURCE_AUTHORITIES,
        no_business_fact_authority=NO_BUSINESS_FACT_AUTHORITY,
        scene_runtime_surface_only=True,
    )


class SystemInitSceneRuntimeSurfaceBuilder:
    SOURCE_KIND = SOURCE_KIND
    SOURCE_AUTHORITIES = SOURCE_AUTHORITIES
    NO_BUSINESS_FACT_AUTHORITY = NO_BUSINESS_FACT_AUTHORITY

    @classmethod
    def source_authority_contract(cls) -> dict:
        return source_authority_contract()

    @staticmethod
    def apply(*, surface_ctx):
        env = surface_ctx.env
        params = surface_ctx.params
        data = surface_ctx.data
        role_surface = surface_ctx.role_surface if isinstance(surface_ctx.role_surface, dict) else {}
        contract_mode = surface_ctx.contract_mode
        scene_channel = surface_ctx.scene_channel
        scene_ready_mode = _scene_ready_mode(params)

        delivery_runtime = surface_ctx.resolve_delivery_policy_runtime_fn(env, params)
        delivery_result = surface_ctx.filter_delivery_scenes_fn(
            data.get("scenes") if isinstance(data, dict) else [],
            surface=delivery_runtime.get("surface") or "default",
            role_surface=role_surface,
            contract_mode=contract_mode,
            runtime_env=delivery_runtime.get("runtime_env") or "dev",
            enabled=bool(delivery_runtime.get("enabled")),
            env=env,
        )
        if isinstance(data.get("nav_meta"), dict):
            data["nav_meta"]["delivery_policy"] = delivery_result.get("meta") or {}

        startup_scene_subset = surface_ctx.startup_scene_subset_resolver_fn(data, params=params)
        preload_scenes = surface_ctx.filter_startup_scenes_for_preload_fn(
            delivery_result.get("delivery_scenes") if isinstance(delivery_result, dict) else [],
            startup_scene_subset,
        )
        scene_ready_input = []
        scene_ready_seen = set()
        for scene_row in list(preload_scenes or []) + list(delivery_result.get("deep_link_scenes") or []):
            if not isinstance(scene_row, dict):
                continue
            scene_key = str(scene_row.get("code") or scene_row.get("key") or "").strip()
            if not scene_key or scene_key in scene_ready_seen:
                continue
            scene_ready_seen.add(scene_key)
            scene_ready_input.append(scene_row)
        requested_scene_key = str(params.get("scene_key") or "").strip()
        if requested_scene_key and requested_scene_key not in scene_ready_seen:
            scene_catalog = data.get("scenes") if isinstance(data.get("scenes"), list) else []
            requested_scene_found = False
            for scene_row in scene_catalog:
                if not isinstance(scene_row, dict):
                    continue
                scene_key = str(scene_row.get("code") or scene_row.get("key") or "").strip()
                if scene_key != requested_scene_key:
                    continue
                scene_ready_seen.add(scene_key)
                scene_ready_input.append(scene_row)
                requested_scene_found = True
                break
            if not requested_scene_found:
                scene_ready_seen.add(requested_scene_key)
                scene_ready_input.append(
                    {
                        "code": requested_scene_key,
                        "name": requested_scene_key,
                        "layout": {"kind": "workspace"},
                        "target": {"route": f"/s/{requested_scene_key}"},
                    }
                )

        nav_contract_input = dict(data)
        nav_contract_input["scenes"] = preload_scenes
        nav_contract_input["delivery_policy_applied"] = bool(delivery_result.get("meta", {}).get("enabled"))
        role_code = str(role_surface.get("role_code") or "").strip()
        bind_result = {}
        if scene_ready_mode == "registry":
            data["scene_ready_contract_v1"] = _build_scene_ready_registry_contract(
                scene_ready_input,
                scene_version=data.get("scene_version"),
                schema_version=data.get("schema_version"),
                scene_channel=scene_channel,
            )
            if isinstance(data.get("nav_meta"), dict):
                data["nav_meta"]["scene_ready_mode"] = "registry"
        else:
            bind_result = surface_ctx.bind_scene_assets_fn(
                env,
                scenes=scene_ready_input,
                role_code=role_code or None,
                company_id=env.company.id if env.company else None,
            )
            if isinstance(bind_result, dict) and bind_result:
                scene_ready_input = bind_result.get("scenes") or scene_ready_input

            data["scene_ready_contract_v1"] = surface_ctx.build_scene_ready_contract_fn(
                scenes=scene_ready_input,
                role_surface=role_surface,
                scene_version=data.get("scene_version"),
                schema_version=data.get("schema_version"),
                scene_channel=scene_channel,
                action_surface_strategy=data.get("scene_action_surface_strategy")
                if isinstance(data.get("scene_action_surface_strategy"), dict)
                else {},
                runtime_context={
                    "role_code": role_code,
                    "company_id": env.company.id if env.company else None,
                },
            )
            default_route = data.get("default_route") if isinstance(data.get("default_route"), dict) else {}
            active_scene_key = str(
                default_route.get("scene_key") or role_surface.get("landing_scene_key") or ""
            ).strip()
            data = apply_system_init_scene_runtime_semantic_bridge(data, active_scene_key=active_scene_key)

        scene_nav_contract = surface_ctx.build_scene_nav_contract_fn(nav_contract_input)
        if isinstance(scene_nav_contract, dict) and isinstance(scene_nav_contract.get("nav"), list):
            # Scene nav remains available as an auxiliary contract for workbench/scene entry use.
            # The primary app sidebar must continue to consume legacy menu navigation until
            # scene navigation can represent the full business nav surface without pruning it.
            data["nav_legacy"] = data.get("nav") or []
            data["nav_contract"] = scene_nav_contract
            if isinstance(data.get("nav_meta"), dict):
                data["nav_meta"]["scene_nav_contract_available"] = True
                data["nav_meta"]["scene_ready_contract_v1"] = bool(
                    isinstance(data.get("scene_ready_contract_v1"), dict)
                    and ((data.get("scene_ready_contract_v1") or {}).get("scenes"))
                )
                contract_meta = scene_nav_contract.get("meta")
                if isinstance(contract_meta, dict):
                    data["nav_meta"]["scene_nav_meta"] = contract_meta

        if surface_ctx.platform_minimum_surface_mode:
            minimum_nav_contract = surface_ctx.build_platform_minimum_nav_contract_fn()
            data["nav_legacy"] = data.get("nav") or []
            data["nav_contract"] = minimum_nav_contract
            data["nav"] = minimum_nav_contract.get("nav") or []
            minimum_default_route = {
                "menu_id": None,
                "scene_key": "workspace.home",
                "route": "/",
                "reason": "platform_minimum_surface",
            }
            data["default_route"] = minimum_default_route
            if isinstance(minimum_nav_contract, dict):
                minimum_nav_contract["default_route"] = dict(minimum_default_route)
                nav_contract_meta = minimum_nav_contract.get("meta")
                if isinstance(nav_contract_meta, dict):
                    nav_contract_meta["platform_minimum_surface"] = True
            if isinstance(data.get("nav_meta"), dict):
                data["nav_meta"]["platform_minimum_surface"] = True
                data["nav_meta"]["platform_minimum_reason"] = "industry_modules_absent"
                data["nav_meta"]["nav_source"] = "platform_minimum_surface"

        return {
            "data": data,
            "delivery_result": delivery_result,
            "scene_nav_contract": scene_nav_contract if isinstance(scene_nav_contract, dict) else {},
            "bind_result": bind_result if isinstance(bind_result, dict) else {},
        }
