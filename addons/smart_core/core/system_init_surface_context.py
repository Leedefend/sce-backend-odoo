# -*- coding: utf-8 -*-
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable


@dataclass
class SystemInitSurfaceContext:
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

    @property
    def apply_delivery_surface_governance_fn(self) -> Callable:
        return self.apply_contract_governance_fn
