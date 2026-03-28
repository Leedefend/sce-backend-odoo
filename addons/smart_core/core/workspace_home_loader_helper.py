# -*- coding: utf-8 -*-
from __future__ import annotations

from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path
from typing import Any, Callable


def _load_module(module_name: str, file_path: Path):
    spec = spec_from_file_location(module_name, file_path)
    if spec is None or spec.loader is None:
        raise RuntimeError("spec unavailable")
    module = module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def resolve_action_target(
    action_key: str,
    page_key: str,
    *,
    cached_resolver: Callable[[str, str], dict[str, Any]] | None = None,
    base_path: Path | None = None,
):
    if callable(cached_resolver):
        return cached_resolver(action_key, page_key), cached_resolver
    helper_path = (base_path or Path(__file__)).with_name("action_target_schema.py")
    try:
        module = _load_module("smart_core_action_target_schema_workspace_home", helper_path)
        resolver = getattr(module, "resolve_action_target", None)
        if callable(resolver):
            return resolver(action_key, page_key), resolver
    except Exception:
        pass
    fallback_scene = str(page_key or "").strip().lower() or "workspace.home"
    return {"kind": "scene.key", "scene_key": fallback_scene}, None


def load_workspace_data_provider(
    *,
    cached_module: Any = None,
    base_path: Path | None = None,
):
    if cached_module is not None:
        return cached_module

    current_path = base_path or Path(__file__)
    provider_path = None
    try:
        registry_path = current_path.resolve().parents[2] / "smart_scene" / "core" / "scene_provider_registry.py"
        module = _load_module("smart_scene_provider_registry_workspace_home", registry_path)
        resolver = getattr(module, "resolve_scene_provider_path", None)
        if callable(resolver):
            provider_path = resolver("workspace.home", current_path)
    except Exception:
        provider_path = None

    if provider_path is None:
        provider_path = current_path.with_name("workspace_home_data_provider.py")

    try:
        return _load_module("smart_core_workspace_home_data_provider", Path(provider_path))
    except Exception:
        return False


def load_workspace_scene_engine(
    *,
    cached_module: Any = None,
    base_path: Path | None = None,
):
    if cached_module is not None:
        return cached_module
    current_path = base_path or Path(__file__)
    engine_path = current_path.resolve().parents[2] / "smart_scene" / "core" / "scene_engine.py"
    try:
        return _load_module("smart_scene_core_scene_engine_workspace_home", engine_path)
    except Exception:
        return False
