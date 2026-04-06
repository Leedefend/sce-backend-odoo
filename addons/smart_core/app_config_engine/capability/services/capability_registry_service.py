# -*- coding: utf-8 -*-
from __future__ import annotations

from typing import Any, Dict

from ..core.registry import CapabilityRegistry


class CapabilityRegistryService:
    def __init__(self, *, platform_owner: str = "smart_core"):
        self.registry = CapabilityRegistry(platform_owner=platform_owner)

    def get_registry_bundle(self, env, user=None) -> Dict[str, Any]:
        return self.registry.build(env, user=user)
