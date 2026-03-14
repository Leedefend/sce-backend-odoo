# -*- coding: utf-8 -*-
from __future__ import annotations

from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path
from typing import Optional


def _load_scene_provider_registry(base_dir: Path):
    registry_path = _resolve_addons_root(base_dir) / "smart_scene" / "core" / "scene_provider_registry.py"
    spec = spec_from_file_location("smart_scene_scene_provider_registry_locator", registry_path)
    if spec is None or spec.loader is None:
        return None
    module = module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _resolve_by_registry(scene_key: str, base_dir: Path) -> Optional[Path]:
    try:
        module = _load_scene_provider_registry(base_dir)
        resolver = getattr(module, "resolve_scene_provider_path", None) if module else None
        if callable(resolver):
            return resolver(scene_key, base_dir)
    except Exception:
        return None
    return None


def _resolve_addons_root(base_dir: Path) -> Path:
    current = base_dir.resolve()
    if current.is_file():
        current = current.parent
    for parent in [current] + list(current.parents):
        if parent.name == "addons":
            return parent
    return base_dir.resolve().parents[2]


def resolve_workspace_home_provider_path(base_dir: Path) -> Optional[Path]:
    """Deprecated shim: resolve workspace-home provider via scene provider registry only."""
    return _resolve_by_registry("workspace.home", base_dir)


def resolve_project_dashboard_scene_content_path(base_dir: Path) -> Optional[Path]:
    """Deprecated shim: resolve project.dashboard provider via scene provider registry only."""
    return _resolve_by_registry("project.dashboard", base_dir)


def resolve_scene_registry_content_path(base_dir: Path) -> Optional[Path]:
    """Deprecated shim: resolve scene.registry provider via scene provider registry only."""
    return _resolve_by_registry("scene.registry", base_dir)
