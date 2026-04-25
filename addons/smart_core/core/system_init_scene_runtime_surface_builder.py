# -*- coding: utf-8 -*-
from __future__ import annotations

from odoo.addons.smart_core.core.system_init_scene_runtime_semantic_bridge import (
    apply_system_init_scene_runtime_semantic_bridge,
)


class SystemInitSceneRuntimeSurfaceBuilder:
    @staticmethod
    def apply(*, surface_ctx):
        env = surface_ctx.env
        params = surface_ctx.params
        data = surface_ctx.data
        role_surface = surface_ctx.role_surface if isinstance(surface_ctx.role_surface, dict) else {}
        contract_mode = surface_ctx.contract_mode
        scene_channel = surface_ctx.scene_channel

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

        nav_contract_input = dict(data)
        nav_contract_input["scenes"] = preload_scenes
        nav_contract_input["delivery_policy_applied"] = bool(delivery_result.get("meta", {}).get("enabled"))
        role_code = str(role_surface.get("role_code") or "").strip()
        bind_result = surface_ctx.bind_scene_assets_fn(
            env,
            scenes=nav_contract_input.get("scenes") if isinstance(nav_contract_input.get("scenes"), list) else [],
            role_code=role_code or None,
            company_id=env.company.id if env.company else None,
        )
        if isinstance(bind_result, dict) and bind_result:
            nav_contract_input["scenes"] = bind_result.get("scenes") or nav_contract_input.get("scenes") or []

        data["scene_ready_contract_v1"] = surface_ctx.build_scene_ready_contract_fn(
            scenes=nav_contract_input.get("scenes") if isinstance(nav_contract_input.get("scenes"), list) else [],
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
