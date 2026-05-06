# -*- coding: utf-8 -*-
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable

from odoo.addons.smart_core.core.source_authority import build_source_authority_contract

SOURCE_KIND = "system_init_surface_context_carrier"
SOURCE_AUTHORITIES = ("system_init_payload", "capability_surface", "identity_surface", "navigation_tree")
NO_BUSINESS_FACT_AUTHORITY = True


def source_authority_contract() -> dict:
    return build_source_authority_contract(
        kind=SOURCE_KIND,
        authorities=SOURCE_AUTHORITIES,
        no_business_fact_authority=NO_BUSINESS_FACT_AUTHORITY,
        runtime_carrier="system_init_surface_context",
    )


@dataclass
class SystemInitSurfaceContext:
    SOURCE_KIND = SOURCE_KIND
    SOURCE_AUTHORITIES = SOURCE_AUTHORITIES
    NO_BUSINESS_FACT_AUTHORITY = NO_BUSINESS_FACT_AUTHORITY

    @classmethod
    def source_authority_contract(cls) -> dict:
        return source_authority_contract()

    data: dict
    contract_mode: str
    scene_diagnostics: dict
    capability_surface_engine: Any
    identity_resolver: Any
    user_groups_xmlids: list
    nav_tree: list
    scene_diagnostics_builder: Any
    build_capability_groups_fn: Callable
    apply_contract_governance_fn: Callable
