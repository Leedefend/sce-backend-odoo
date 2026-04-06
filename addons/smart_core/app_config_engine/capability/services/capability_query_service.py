# -*- coding: utf-8 -*-
from __future__ import annotations

from typing import Any, Dict, List

from .capability_registry_service import CapabilityRegistryService
from ..projection.capability_list_projection import build_capability_list_projection
from ..projection.capability_matrix_projection import build_capability_matrix_projection


class CapabilityQueryService:
    def __init__(self, *, platform_owner: str = "smart_core"):
        self.registry_service = CapabilityRegistryService(platform_owner=platform_owner)

    def list_capabilities_for_user(self, env, user=None) -> List[Dict[str, Any]]:
        bundle = self.registry_service.get_registry_bundle(env, user=user)
        rows = bundle.get("rows") if isinstance(bundle, dict) else []
        return build_capability_list_projection(rows)

    def build_capability_matrix_for_user(self, env, user=None) -> Dict[str, Any]:
        bundle = self.registry_service.get_registry_bundle(env, user=user)
        rows = bundle.get("rows") if isinstance(bundle, dict) else []
        return build_capability_matrix_projection(rows)
