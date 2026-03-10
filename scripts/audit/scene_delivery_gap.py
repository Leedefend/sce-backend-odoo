#!/usr/bin/env python3
"""Compute scene delivery gap from fallback scene registry."""
from __future__ import annotations

import ast
import json
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


def main() -> None:
    import importlib.util

    spec = importlib.util.spec_from_file_location("scene_nav_contract_builder", SCENE_BUILDER_PATH)
    if not spec or not spec.loader:
        raise RuntimeError("failed to load scene_nav_contract_builder module")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    fallback_scenes = _load_fallback_scenes()
    report = module.build_scene_delivery_report(fallback_scenes)
    output = {
        "source": str(SCENE_REGISTRY_PATH),
        "fallback_scene_total": len(fallback_scenes),
        **report,
    }
    print(json.dumps(output, ensure_ascii=False, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
