#!/usr/bin/env python3
"""Compute scene delivery gap from fallback scene registry."""
from __future__ import annotations

import ast
import argparse
import json
import os
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
SCENE_REGISTRY_PATH = REPO_ROOT / "addons" / "smart_construction_scene" / "scene_registry.py"
SCENE_BUILDER_PATH = REPO_ROOT / "addons" / "smart_core" / "core" / "scene_nav_contract_builder.py"


def _load_fallback_scenes() -> list[dict]:
    source = SCENE_REGISTRY_PATH.read_text(encoding="utf-8")
    module = ast.parse(source)
    for node in module.body:
        if not isinstance(node, ast.FunctionDef) or node.name != "load_scene_configs":
            continue
        for stmt in node.body:
            if not isinstance(stmt, ast.Assign):
                continue
            for target in stmt.targets:
                if isinstance(target, ast.Name) and target.id == "fallback":
                    return ast.literal_eval(stmt.value)
    raise RuntimeError("failed to locate fallback scene list in scene_registry.py")


def _default_include_tests() -> bool:
    runtime_env = str(os.environ.get("ENV") or "").strip().lower()
    if runtime_env in {"prod", "production"}:
        return False
    return runtime_env in {"dev", "test"}


def _filter_test_scenes(items: list[dict], include_tests: bool) -> list[dict]:
    if include_tests:
        return list(items or [])
    return [row for row in (items or []) if isinstance(row, dict) and not bool(row.get("is_test"))]


def main() -> None:
    parser = argparse.ArgumentParser(description="Scene delivery-gap audit report")
    parser.add_argument("--include-tests", action="store_true", help="Include is_test scenes in audit input")
    args = parser.parse_args()

    import importlib.util

    spec = importlib.util.spec_from_file_location("scene_nav_contract_builder", SCENE_BUILDER_PATH)
    if not spec or not spec.loader:
        raise RuntimeError("failed to load scene_nav_contract_builder module")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    fallback_scenes = _load_fallback_scenes()
    include_tests = bool(args.include_tests or _default_include_tests())
    effective_scenes = _filter_test_scenes(fallback_scenes, include_tests=include_tests)
    report = module.build_scene_delivery_report(effective_scenes)
    output = {
        "source": str(SCENE_REGISTRY_PATH),
        "fallback_scene_total": len(fallback_scenes),
        "effective_scene_total": len(effective_scenes),
        "include_tests": include_tests,
        **report,
    }
    print(json.dumps(output, ensure_ascii=False, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
