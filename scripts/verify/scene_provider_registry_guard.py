#!/usr/bin/env python3
from __future__ import annotations

from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[2]
REGISTRY = ROOT / "addons/smart_scene/core/scene_provider_registry.py"
BOOTSTRAP = ROOT / "addons/smart_construction_scene/bootstrap/register_scene_providers.py"


def _load(path: Path, module_name: str):
    spec = spec_from_file_location(module_name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"spec unavailable: {path.as_posix()}")
    module = module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _fail(errors: list[str]) -> int:
    print("[verify.scene.provider.registry.guard] FAIL")
    for err in errors:
        print(f"- {err}")
    return 1


def main() -> int:
    errors: list[str] = []
    if not REGISTRY.is_file():
        errors.append(f"missing registry file: {REGISTRY.relative_to(ROOT).as_posix()}")
    if not BOOTSTRAP.is_file():
        errors.append(f"missing bootstrap file: {BOOTSTRAP.relative_to(ROOT).as_posix()}")
    if errors:
        return _fail(errors)

    module = _load(REGISTRY, "smart_scene_provider_registry_guard")
    build_registry = getattr(module, "build_scene_provider_registry", None)
    if not callable(build_registry):
        errors.append("missing callable: build_scene_provider_registry")
        return _fail(errors)

    registry = build_registry(ROOT / "addons")
    get_provider = getattr(registry, "get_provider", None)
    if not callable(get_provider):
        errors.append("registry missing callable: get_provider")
        return _fail(errors)

    expectations = {
        "workspace.home": "smart_construction_scene/profiles/workspace_home_scene_content.py",
        "project.dashboard": "smart_construction_scene/profiles/project_dashboard_scene_content.py",
        "scene.registry": "smart_construction_scene/profiles/scene_registry_content.py",
    }
    for scene_key, suffix in expectations.items():
        provider = get_provider(scene_key)
        if provider is None:
            errors.append(f"provider missing for scene: {scene_key}")
            continue
        path_text = str(getattr(provider, "provider_path", ""))
        if suffix not in path_text.replace("\\", "/"):
            errors.append(f"scene {scene_key} provider mismatch: {path_text}")

    if errors:
        return _fail(errors)

    print("[verify.scene.provider.registry.guard] PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())

