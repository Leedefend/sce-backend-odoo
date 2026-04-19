# -*- coding: utf-8 -*-
from __future__ import annotations

import time
from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path
from typing import Any, Dict, List, Tuple

_SCENE_PROVIDER_REGISTRY_MODULES: dict[str, object] = {}
_SCENE_PROVIDER_REGISTRY_PATHS: dict[str, Path] = {}
_SCENE_REGISTRY_CONTENT_MODULES: dict[str, object] = {}


def _provider_registry_path(base_file: Path) -> Path:
    base_key = str(base_file)
    cached_path = _SCENE_PROVIDER_REGISTRY_PATHS.get(base_key)
    if cached_path is not None:
        return cached_path
    if base_file.is_absolute():
        registry_path = base_file.parents[1] / "smart_scene" / "core" / "scene_provider_registry.py"
    else:
        registry_path = base_file.resolve().parents[1] / "smart_scene" / "core" / "scene_provider_registry.py"
    _SCENE_PROVIDER_REGISTRY_PATHS[base_key] = registry_path
    return registry_path


def _load_scene_provider_registry(base_file: Path):
    registry_path = _provider_registry_path(base_file)
    cache_key = str(registry_path)
    cached_module = _SCENE_PROVIDER_REGISTRY_MODULES.get(cache_key)
    if cached_module is not None:
        return cached_module
    spec = spec_from_file_location("smart_scene_provider_registry_scene_registry_engine", registry_path)
    if spec is None or spec.loader is None:
        return None
    module = module_from_spec(spec)
    spec.loader.exec_module(module)
    _SCENE_PROVIDER_REGISTRY_MODULES[cache_key] = module
    return module


def load_scene_registry_content_module(
    base_file: Path,
    *,
    registry_module=None,
    provider_path: Path | None = None,
):
    resolved_provider_path = provider_path
    try:
        current_registry_module = registry_module or _load_scene_provider_registry(base_file)
        resolver = getattr(current_registry_module, "resolve_scene_provider_path", None) if current_registry_module else None
        if resolved_provider_path is None and callable(resolver):
            resolved_provider_path = resolver("scene.registry", base_file)
    except Exception:
        resolved_provider_path = None

    if resolved_provider_path is None:
        return None

    try:
        cache_key = str(resolved_provider_path)
        cached_module = _SCENE_REGISTRY_CONTENT_MODULES.get(cache_key)
        if cached_module is not None:
            return cached_module
        spec = spec_from_file_location("smart_construction_scene_registry_content", resolved_provider_path)
        if spec is None or spec.loader is None:
            return None
        module = module_from_spec(spec)
        spec.loader.exec_module(module)
        _SCENE_REGISTRY_CONTENT_MODULES[cache_key] = module
        return module
    except Exception:
        return None


def load_scene_registry_content_entries(base_file: Path) -> List[Dict[str, Any]]:
    rows, _timings = load_scene_registry_content_entries_with_timings(base_file)
    return rows


def load_scene_registry_content_entries_with_timings(base_file: Path) -> Tuple[List[Dict[str, Any]], dict[str, int]]:
    timings_ms: dict[str, int] = {}

    def _mark(stage: str, started_at: float) -> float:
        timings_ms[stage] = int((time.perf_counter() - started_at) * 1000)
        return time.perf_counter()

    stage_ts = time.perf_counter()
    registry_module = _load_scene_provider_registry(base_file)
    stage_ts = _mark("load_scene_provider_registry", stage_ts)
    provider_path = None
    resolver = getattr(registry_module, "resolve_scene_provider_path", None) if registry_module else None
    timed_resolver = getattr(registry_module, "resolve_scene_provider_with_timings", None) if registry_module else None
    if callable(resolver):
        stage_ts = time.perf_counter()
        try:
            if callable(timed_resolver):
                provider, resolver_timings = timed_resolver("scene.registry", base_file)
                provider_path = provider.provider_path if provider else None
                if isinstance(resolver_timings, dict):
                    for key, value in resolver_timings.items():
                        timings_ms[f"resolve.{key}"] = int(value)
            else:
                provider_path = resolver("scene.registry", base_file)
        except Exception:
            provider_path = None
        stage_ts = _mark("resolve_scene_provider_path", stage_ts)
    if provider_path is None:
        return [], timings_ms

    stage_ts = time.perf_counter()
    module = load_scene_registry_content_module(
        base_file,
        registry_module=registry_module,
        provider_path=provider_path,
    )
    stage_ts = _mark("load_scene_registry_content_module", stage_ts)
    if module is None:
        return [], timings_ms
    fn = getattr(module, "list_scene_entries", None)
    if not callable(fn):
        return [], timings_ms
    try:
        stage_ts = time.perf_counter()
        rows = fn()
        stage_ts = _mark("list_scene_entries", stage_ts)
        if not isinstance(rows, list):
            return [], timings_ms
        stage_ts = time.perf_counter()
        valid_rows = []
        for row in rows:
            if not isinstance(row, dict):
                continue
            code = str(row.get("code") or "").strip()
            target = row.get("target") if isinstance(row.get("target"), dict) else {}
            if not code:
                continue
            if not (
                target.get("route")
                or target.get("menu_xmlid")
                or target.get("action_xmlid")
                or target.get("menu_id")
                or target.get("action_id")
                or target.get("model")
            ):
                continue
            valid_rows.append(row)
        _mark("filter_valid_rows", stage_ts)
        return valid_rows, timings_ms
    except Exception:
        return [], timings_ms
