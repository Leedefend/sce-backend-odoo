# -*- coding: utf-8 -*-
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable

SOURCE_KIND = "system_init_runtime_context_carrier"
SOURCE_AUTHORITIES = ("system_init_request", "scene_runtime_dependencies")
NO_BUSINESS_FACT_AUTHORITY = True


def source_authority_contract() -> dict:
    return {
        "kind": SOURCE_KIND,
        "authorities": list(SOURCE_AUTHORITIES),
        "projection_only": True,
        "rebuildable": True,
        "no_business_fact_authority": NO_BUSINESS_FACT_AUTHORITY,
        "runtime_carrier": "system_init_runtime_context",
    }


@dataclass
class SystemInitRuntimeContext:
    SOURCE_KIND = SOURCE_KIND
    SOURCE_AUTHORITIES = SOURCE_AUTHORITIES
    NO_BUSINESS_FACT_AUTHORITY = NO_BUSINESS_FACT_AUTHORITY

    @classmethod
    def source_authority_contract(cls) -> dict:
        return source_authority_contract()

    env: Any
    user: Any
    params: dict
    data: dict
    nav_tree: list
    scene_channel: str
    rollback_active: bool
    trace_id: str
    diagnostics_collector: Any
    scene_diagnostics: dict
    load_scene_contract_fn: Callable
    load_scenes_fallback_fn: Callable
    merge_missing_scenes_fn: Callable
    append_resolve_error_fn: Callable
