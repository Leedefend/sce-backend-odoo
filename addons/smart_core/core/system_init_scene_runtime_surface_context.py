# -*- coding: utf-8 -*-
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable

from odoo.addons.smart_core.core.source_authority import build_source_authority_contract

SOURCE_KIND = "system_init_scene_runtime_surface_context_carrier"
SOURCE_AUTHORITIES = (
    "system_init_payload",
    "scene_runtime_surface",
    "delivery_policy_runtime",
    "scene_navigation_contract",
)
NO_BUSINESS_FACT_AUTHORITY = True


def source_authority_contract() -> dict:
    return build_source_authority_contract(
        kind=SOURCE_KIND,
        authorities=SOURCE_AUTHORITIES,
        no_business_fact_authority=NO_BUSINESS_FACT_AUTHORITY,
        runtime_carrier="system_init_scene_runtime_surface_context",
    )


@dataclass
class SystemInitSceneRuntimeSurfaceContext:
    SOURCE_KIND = SOURCE_KIND
    SOURCE_AUTHORITIES = SOURCE_AUTHORITIES
    NO_BUSINESS_FACT_AUTHORITY = NO_BUSINESS_FACT_AUTHORITY

    @classmethod
    def source_authority_contract(cls) -> dict:
        return source_authority_contract()

    env: Any
    params: dict
    data: dict
    role_surface: dict
    contract_mode: str
    scene_channel: str
    nav_tree: list
    platform_minimum_surface_mode: bool
    build_platform_minimum_nav_contract_fn: Callable
    resolve_delivery_policy_runtime_fn: Callable
    filter_delivery_scenes_fn: Callable
    startup_scene_subset_resolver_fn: Callable
    filter_startup_scenes_for_preload_fn: Callable
    bind_scene_assets_fn: Callable
    build_scene_ready_contract_fn: Callable
    build_scene_nav_contract_fn: Callable
