#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
COMPILER_PATH = ROOT / "addons" / "smart_core" / "core" / "scene_dsl_compiler.py"
READY_BUILDER_PATH = ROOT / "addons" / "smart_core" / "core" / "scene_ready_contract_builder.py"
SYSTEM_INIT_PATH = ROOT / "addons" / "smart_core" / "handlers" / "system_init.py"


def _assert(condition: bool, message: str, errors: list[str]) -> None:
    if not condition:
        errors.append(message)


def main() -> int:
    errors: list[str] = []
    for path in (COMPILER_PATH, READY_BUILDER_PATH, SYSTEM_INIT_PATH):
        if not path.is_file():
            errors.append(f"missing file: {path}")
    if errors:
        print("[scene_orchestrator_output_schema_guard] FAIL")
        for item in errors:
            print(f" - {item}")
        return 1

    compiler_text = COMPILER_PATH.read_text(encoding="utf-8")
    for key in (
        '"scene": _as_dict(compiled.get("scene"))',
        '"page": _as_dict(compiled.get("page"))',
        '"blocks": _as_list(compiled.get("blocks"))',
        '"actions": _as_list(compiled.get("actions"))',
        '"action_surface": _as_dict(compiled.get("action_surface"))',
        '"search_surface": _as_dict(compiled.get("search_surface"))',
        '"workflow_surface": _as_dict(compiled.get("workflow_surface"))',
        '"permission_surface": _as_dict(compiled.get("permission_surface"))',
        '"validation_surface": _as_dict(compiled.get("validation_surface"))',
        '"meta": _as_dict(compiled.get("meta"))',
    ):
        _assert(key in compiler_text, f"scene_compile output missing key mapping: {key}", errors)

    ready_text = READY_BUILDER_PATH.read_text(encoding="utf-8")
    _assert('"schema_version": "scene_ready_contract_v1"' in ready_text, "scene_ready schema_version missing", errors)
    _assert('"scenes": entries' in ready_text, "scene_ready scenes payload missing", errors)

    init_text = SYSTEM_INIT_PATH.read_text(encoding="utf-8")
    _assert('data["scene_ready_contract_v1"]' in init_text, "system_init missing scene_ready_contract_v1 assignment", errors)

    if errors:
        print("[scene_orchestrator_output_schema_guard] FAIL")
        for item in errors:
            print(f" - {item}")
        return 1

    print("[scene_orchestrator_output_schema_guard] PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
