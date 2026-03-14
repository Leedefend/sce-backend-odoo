# -*- coding: utf-8 -*-
from __future__ import annotations

from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path
from typing import Any, Dict, List


def _load_scene_provider_registry(base_file: Path):
    registry_path = base_file.resolve().parents[1] / "smart_scene" / "core" / "scene_provider_registry.py"
    spec = spec_from_file_location("smart_scene_provider_registry_scene_registry_engine", registry_path)
    if spec is None or spec.loader is None:
        return None
    module = module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def load_scene_registry_content_module(base_file: Path):
    provider_path = None
    try:
        registry_module = _load_scene_provider_registry(base_file)
        resolver = getattr(registry_module, "resolve_scene_provider_path", None) if registry_module else None
        if callable(resolver):
            provider_path = resolver("scene.registry", base_file)
    except Exception:
        provider_path = None

    if provider_path is None:
        return None

    try:
        spec = spec_from_file_location("smart_construction_scene_registry_content", provider_path)
        if spec is None or spec.loader is None:
            return None
        module = module_from_spec(spec)
        spec.loader.exec_module(module)
        return module
    except Exception:
        return None


def load_scene_registry_content_entries(base_file: Path) -> List[Dict[str, Any]]:
    module = load_scene_registry_content_module(base_file)
    if module is None:
        return []
    fn = getattr(module, "list_scene_entries", None)
    if not callable(fn):
        return []
    try:
        rows = fn()
        if not isinstance(rows, list):
            return []
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
        return valid_rows
    except Exception:
        return []
