#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SYSTEM_INIT_PATH = ROOT / "addons" / "smart_core" / "handlers" / "system_init.py"
REPOSITORY_PATH = ROOT / "addons" / "smart_core" / "core" / "ui_base_contract_asset_repository.py"
READY_BUILDER_PATH = ROOT / "addons" / "smart_core" / "core" / "scene_ready_contract_builder.py"
COMPILER_PATH = ROOT / "addons" / "smart_core" / "core" / "scene_dsl_compiler.py"


def _assert(condition: bool, message: str, errors: list[str]) -> None:
    if not condition:
        errors.append(message)


def main() -> int:
    errors: list[str] = []
    for path in (SYSTEM_INIT_PATH, REPOSITORY_PATH, READY_BUILDER_PATH, COMPILER_PATH):
        if not path.is_file():
            errors.append(f"missing file: {path}")
    if errors:
        print("[scene_orchestrator_base_fact_binding_guard] FAIL")
        for item in errors:
            print(f" - {item}")
        return 1

    init_text = SYSTEM_INIT_PATH.read_text(encoding="utf-8")
    _assert("bind_scene_assets(" in init_text, "system_init missing bind_scene_assets call", errors)
    _assert('"ui_base_contract_bound_scene_count"' in init_text, "system_init missing nav_meta asset binding metrics", errors)

    repo_text = REPOSITORY_PATH.read_text(encoding="utf-8")
    _assert('entry["ui_base_contract"] = asset.get("payload") or {}' in repo_text, "asset repository missing ui_base_contract injection", errors)

    compiler_text = COMPILER_PATH.read_text(encoding="utf-8")
    _assert('"base_contract_bound_block_count"' in compiler_text, "compiler missing base contract binding metrics", errors)
    _assert('"base_contract_bound"' in compiler_text, "compiler missing compile_verdict.base_contract_bound", errors)

    ready_text = READY_BUILDER_PATH.read_text(encoding="utf-8")
    _assert('"base_contract_bound_scene_count"' in ready_text, "scene_ready builder missing base_contract_bound_scene_count", errors)

    if errors:
        print("[scene_orchestrator_base_fact_binding_guard] FAIL")
        for item in errors:
            print(f" - {item}")
        return 1

    print("[scene_orchestrator_base_fact_binding_guard] PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

