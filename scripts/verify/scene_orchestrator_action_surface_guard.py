#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

import importlib.util
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[2]
COMPILER = ROOT / "addons" / "smart_core" / "core" / "scene_dsl_compiler.py"


def _assert(condition: bool, message: str, errors: list[str]) -> None:
    if not condition:
        errors.append(message)


def _load_scene_compile():
    spec = importlib.util.spec_from_file_location("scene_dsl_compiler_action_surface_guard", COMPILER)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"spec unavailable: {COMPILER}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    fn = getattr(module, "scene_compile", None)
    if not callable(fn):
        raise RuntimeError("scene_compile not found")
    return fn


def main() -> int:
    errors: list[str] = []
    if not COMPILER.is_file():
        errors.append(f"missing file: {COMPILER}")
    if errors:
        print("[scene_orchestrator_action_surface_guard] FAIL")
        for item in errors:
            print(f" - {item}")
        return 1

    compiler_text = COMPILER.read_text(encoding="utf-8")
    for token in (
        "_infer_action_tier",
        "_build_action_surface",
        '"action_surface": _as_dict(compiled.get("action_surface"))',
        "action_surface_counts",
    ):
        _assert(token in compiler_text, f"compiler missing action surface token: {token}", errors)

    try:
        scene_compile = _load_scene_compile()
        base_contract = {
            "actions": {
                "items": [
                    {"key": "create_project", "label": "新建", "placement": "toolbar"},
                    {"key": "batch_archive", "label": "归档", "placement": "row"},
                    {"key": "export_projects", "label": "导出", "placement": "toolbar"},
                ]
            },
            "permissions": {"allowed": True},
        }
        payload = {
            "code": "projects.list",
            "layout": {"kind": "list"},
            "actions": [
                {"key": "create_project", "label": "新建项目"},
                {"key": "open_detail", "label": "详情", "placement": "row"},
            ],
        }
        compiled = scene_compile(payload, scene_key="projects.list", ui_base_contract=base_contract, provider_registry={})
        action_surface = compiled.get("action_surface") if isinstance(compiled.get("action_surface"), dict) else {}
        counts = action_surface.get("counts") if isinstance(action_surface.get("counts"), dict) else {}
        primary = action_surface.get("primary") if isinstance(action_surface.get("primary"), list) else []
        contextual = action_surface.get("contextual") if isinstance(action_surface.get("contextual"), list) else []
        _assert(action_surface.get("scene_type") == "list", "action surface scene_type mismatch", errors)
        _assert(len(primary) >= 1, "action surface primary bucket should not be empty", errors)
        _assert(len(contextual) >= 1, "action surface contextual bucket should not be empty", errors)
        _assert(int(counts.get("total") or 0) == len(compiled.get("actions") or []), "action surface total count mismatch", errors)
    except Exception as exc:
        errors.append(f"runtime sample failed: {exc}")

    if errors:
        print("[scene_orchestrator_action_surface_guard] FAIL")
        for item in errors:
            print(f" - {item}")
        return 1

    print("[scene_orchestrator_action_surface_guard] PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

