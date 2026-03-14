# -*- coding: utf-8 -*-
from __future__ import annotations

from pathlib import Path


def register_scene_content_providers(registry, addons_root: Path) -> None:
    """Register construction-domain scene content providers.

    This module is loaded by `smart_scene` platform registry engine.
    """

    scene_module = "smart_construction_scene"

    registry.register_spec(
        scene_key="workspace.home",
        provider_key="construction.workspace_home.v1",
        module_name=scene_module,
        provider_path=addons_root / scene_module / "profiles" / "workspace_home_scene_content.py",
        priority=300,
        source="industry_registration",
    )
    registry.register_spec(
        scene_key="project.dashboard",
        provider_key="construction.project_dashboard.v1",
        module_name=scene_module,
        provider_path=addons_root / scene_module / "profiles" / "project_dashboard_scene_content.py",
        priority=300,
        source="industry_registration",
    )
    registry.register_spec(
        scene_key="scene.registry",
        provider_key="construction.scene_registry.v1",
        module_name=scene_module,
        provider_path=addons_root / scene_module / "profiles" / "scene_registry_content.py",
        priority=300,
        source="industry_registration",
    )
