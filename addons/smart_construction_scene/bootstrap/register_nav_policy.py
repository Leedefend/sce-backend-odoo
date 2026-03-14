# -*- coding: utf-8 -*-
from __future__ import annotations

from pathlib import Path


def register_nav_product_policies(registry, addons_root: Path) -> None:
    """Register construction industry nav product policy providers."""

    scene_module = "smart_construction_scene"
    registry.register_spec(
        policy_key="scene_nav_v1",
        provider_key="construction.scene_nav_policy.v1",
        module_name=scene_module,
        provider_path=addons_root / scene_module / "profiles" / "nav_product_policy.py",
        priority=300,
        source="industry_registration",
        policy_version="v1",
        loader_name="build_nav_group_policy",
    )
