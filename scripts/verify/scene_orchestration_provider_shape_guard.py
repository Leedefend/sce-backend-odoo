#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path
from typing import Any, Dict, Iterable, List
import sys


ROOT = Path(__file__).resolve().parents[2]
REGISTRY = ROOT / "addons" / "smart_scene" / "core" / "scene_provider_registry.py"
WORKSPACE_BUILDER = ROOT / "addons" / "smart_core" / "core" / "workspace_home_contract_builder.py"
PROJECT_DASHBOARD_SERVICE = ROOT / "addons" / "smart_construction_core" / "services" / "project_dashboard_service.py"
SCENE_REGISTRY = ROOT / "addons" / "smart_construction_scene" / "scene_registry.py"


def _load_module(path: Path, module_name: str):
    spec = spec_from_file_location(module_name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"spec unavailable: {path.as_posix()}")
    module = module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _fail(errors: List[str]) -> int:
    print("[scene_orchestration_provider_shape_guard] FAIL")
    for error in errors:
        print(f"- {error}")
    return 1


def _must_be_profile_path(path: Path, label: str, errors: List[str]) -> None:
    rel = path.relative_to(ROOT).as_posix()
    if "/profiles/" not in f"/{rel}":
        errors.append(f"{label} must resolve to profiles/* provider, got: {rel}")


def _require_keys(payload: Dict[str, Any], keys: Iterable[str], label: str, errors: List[str]) -> None:
    for key in keys:
        if key not in payload:
            errors.append(f"{label} missing key: {key}")


def main() -> int:
    errors: List[str] = []
    if not REGISTRY.is_file():
        return _fail([f"missing registry: {REGISTRY.relative_to(ROOT).as_posix()}"])

    registry_module = _load_module(REGISTRY, "smart_scene_provider_registry_guard")
    resolve_provider_path = getattr(registry_module, "resolve_scene_provider_path", None)
    if not callable(resolve_provider_path):
        return _fail(["scene provider registry missing resolve_scene_provider_path"])

    workspace_provider_path = resolve_provider_path("workspace.home", WORKSPACE_BUILDER)
    project_provider_path = resolve_provider_path("project.dashboard", PROJECT_DASHBOARD_SERVICE)
    registry_provider_path = resolve_provider_path("scene.registry", SCENE_REGISTRY)

    if not isinstance(workspace_provider_path, Path) or not workspace_provider_path.is_file():
        errors.append("workspace provider path not resolved")
    if not isinstance(project_provider_path, Path) or not project_provider_path.is_file():
        errors.append("project dashboard provider path not resolved")
    if not isinstance(registry_provider_path, Path) or not registry_provider_path.is_file():
        errors.append("scene registry provider path not resolved")
    if errors:
        return _fail(errors)

    _must_be_profile_path(workspace_provider_path, "workspace provider", errors)
    _must_be_profile_path(project_provider_path, "project dashboard provider", errors)
    _must_be_profile_path(registry_provider_path, "scene registry provider", errors)

    workspace_module = _load_module(workspace_provider_path, "workspace_scene_content_guard")
    project_module = _load_module(project_provider_path, "project_dashboard_scene_content_guard")
    registry_module = _load_module(registry_provider_path, "scene_registry_content_guard")

    workspace_symbols = (
        "build_today_actions",
        "build_advice_items",
        "build_role_focus_config",
        "build_v1_focus_map",
        "build_v1_page_profile",
        "build_v1_data_sources",
        "build_v1_state_schema",
        "build_v1_action_specs",
        "build_v1_zones",
        "build_legacy_zones",
        "build_legacy_blocks",
    )
    for symbol in workspace_symbols:
        if not callable(getattr(workspace_module, symbol, None)):
            errors.append(f"workspace provider missing callable: {symbol}")

    project_builder = getattr(project_module, "build_project_dashboard_scene_content", None)
    if not callable(project_builder):
        errors.append("project dashboard provider missing callable: build_project_dashboard_scene_content")
    else:
        project_payload = project_builder()
        if not isinstance(project_payload, dict):
            errors.append("project dashboard scene content must return object")
        else:
            _require_keys(project_payload, ("scene", "page", "zone_blocks"), "project dashboard scene content", errors)
            zone_blocks = project_payload.get("zone_blocks")
            if not isinstance(zone_blocks, list) or not zone_blocks:
                errors.append("project dashboard scene content zone_blocks must be non-empty list")

    registry_builder = getattr(registry_module, "list_scene_entries", None)
    if not callable(registry_builder):
        errors.append("scene registry provider missing callable: list_scene_entries")
    else:
        entries = registry_builder()
        if not isinstance(entries, list) or not entries:
            errors.append("scene registry provider must return non-empty entries list")
        else:
            for idx, row in enumerate(entries):
                if not isinstance(row, dict):
                    errors.append(f"scene registry entry[{idx}] must be object")
                    continue
                if not str(row.get("code") or "").strip():
                    errors.append(f"scene registry entry[{idx}] missing code")
                target = row.get("target")
                if not isinstance(target, dict):
                    errors.append(f"scene registry entry[{idx}] missing target object")

    if errors:
        return _fail(errors)

    print("[scene_orchestration_provider_shape_guard] PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
