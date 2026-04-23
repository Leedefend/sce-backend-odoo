# -*- coding: utf-8 -*-
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable


@dataclass
class SystemInitSceneRuntimeSurfaceContext:
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
