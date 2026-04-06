# -*- coding: utf-8 -*-
from __future__ import annotations

from typing import Any, Dict

from .capability_registry_service import CapabilityRegistryService
from ..projection.workspace_projection import build_workspace_projection
from ..projection.governance_projection import build_governance_projection


class CapabilityRuntimeService:
    def __init__(self, *, platform_owner: str = "smart_core"):
        self.registry_service = CapabilityRegistryService(platform_owner=platform_owner)

    def build_workspace_capability_surface(self, env, user=None) -> Dict[str, Any]:
        bundle = self.registry_service.get_registry_bundle(env, user=user)
        rows = bundle.get("rows") if isinstance(bundle, dict) else []
        return {"tiles": build_workspace_projection(rows)}

    def build_governance_surface(self, env, user=None) -> Dict[str, Any]:
        bundle = self.registry_service.get_registry_bundle(env, user=user)
        rows = bundle.get("rows") if isinstance(bundle, dict) else []
        errors = bundle.get("errors") if isinstance(bundle, dict) else {}
        return build_governance_projection(rows, errors)
