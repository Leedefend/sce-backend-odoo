# -*- coding: utf-8 -*-
from __future__ import annotations

from typing import Any, Callable


def build_runtime_fetch_bootstrap_surface(
    *,
    data: dict[str, Any],
    env,
    user,
    contract_mode: str,
    components: dict[str, Any],
    identity_resolver,
    user_groups_xmlids,
    build_capability_groups_fn: Callable[..., Any],
    apply_contract_governance_fn: Callable[..., Any],
    scene_diagnostics_builder,
    run_extension_hooks_fn: Callable[..., Any],
    merge_extension_facts_fn: Callable[..., Any],
    surface_context_cls,
    surface_builder,
) -> dict[str, Any]:
    run_extension_hooks_fn(env, "smart_core_extend_system_init", data, env, user)
    merge_extension_facts_fn(data)
    surface_ctx = surface_context_cls(
        data=data,
        contract_mode=contract_mode,
        scene_diagnostics={},
        capability_surface_engine=components["capability_surface_engine"],
        identity_resolver=identity_resolver,
        user_groups_xmlids=user_groups_xmlids,
        nav_tree=[],
        scene_diagnostics_builder=scene_diagnostics_builder,
        build_capability_groups_fn=build_capability_groups_fn,
        apply_contract_governance_fn=apply_contract_governance_fn,
    )
    surfaced_data, _ = surface_builder.apply(surface_ctx=surface_ctx)
    return surfaced_data
