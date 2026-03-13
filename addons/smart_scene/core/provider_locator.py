# -*- coding: utf-8 -*-
from __future__ import annotations

from pathlib import Path
from typing import Optional


def resolve_workspace_home_provider_path(base_dir: Path) -> Optional[Path]:
    """Resolve workspace-home scene content provider path by layer order.

    Layer order:
    1) industry content provider (smart_construction_scene)
    2) legacy compatibility provider (smart_core)
    """
    addons_root = base_dir.resolve().parents[2]
    candidates = [
        addons_root / "smart_construction_scene" / "profiles" / "workspace_home_scene_content.py",
        addons_root / "smart_construction_scene" / "services" / "workspace_home_scene_content.py",
        addons_root / "smart_core" / "core" / "workspace_home_data_provider.py",
    ]
    for candidate in candidates:
        if candidate.exists() and candidate.is_file():
            return candidate
    return None


def resolve_project_dashboard_scene_content_path(base_dir: Path) -> Optional[Path]:
    """Resolve project.dashboard scene content path by layer order.

    Layer order:
    1) industry content provider (smart_construction_scene)
    """
    addons_root = base_dir.resolve().parents[2]
    candidates = [
        addons_root / "smart_construction_scene" / "profiles" / "project_dashboard_scene_content.py",
        addons_root / "smart_construction_scene" / "services" / "project_dashboard_scene_content.py",
    ]
    for candidate in candidates:
        if candidate.exists() and candidate.is_file():
            return candidate
    return None


def resolve_scene_registry_content_path(base_dir: Path) -> Optional[Path]:
    """Resolve industry scene-registry content provider path."""
    addons_root = base_dir.resolve().parents[2]
    candidates = [
        addons_root / "smart_construction_scene" / "profiles" / "scene_registry_content.py",
        addons_root / "smart_construction_scene" / "services" / "scene_registry_content.py",
    ]
    for candidate in candidates:
        if candidate.exists() and candidate.is_file():
            return candidate
    return None
