#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SYSTEM_INIT_PATH = ROOT / "addons" / "smart_core" / "handlers" / "system_init.py"
READY_BUILDER_PATH = ROOT / "addons" / "smart_core" / "core" / "scene_ready_contract_builder.py"
COMPILER_PATH = ROOT / "addons" / "smart_core" / "core" / "scene_dsl_compiler.py"


def _assert(condition: bool, message: str, errors: list[str]) -> None:
    if not condition:
        errors.append(message)


def _index_of(text: str, token: str) -> int:
    try:
        return text.index(token)
    except ValueError:
        return -1


def main() -> int:
    errors: list[str] = []
    for path in (SYSTEM_INIT_PATH, READY_BUILDER_PATH, COMPILER_PATH):
        if not path.is_file():
            errors.append(f"missing file: {path}")
    if errors:
        print("[scene_action_surface_strategy_wiring_guard] FAIL")
        for item in errors:
            print(f" - {item}")
        return 1

    system_init_text = SYSTEM_INIT_PATH.read_text(encoding="utf-8")
    builder_text = READY_BUILDER_PATH.read_text(encoding="utf-8")
    compiler_text = COMPILER_PATH.read_text(encoding="utf-8")

    params_idx = _index_of(system_init_text, 'params.get("scene_action_surface_strategy")')
    ext_idx = _index_of(system_init_text, 'ext_facts.get("scene_action_surface_strategy")')
    icp_idx = _index_of(system_init_text, 'smart_core.scene_action_surface_strategy_json')
    _assert(params_idx >= 0, "system.init missing action surface strategy params source", errors)
    _assert(ext_idx >= 0, "system.init missing action surface strategy ext_facts source", errors)
    _assert(icp_idx >= 0, "system.init missing action surface strategy icp source", errors)
    if params_idx >= 0 and ext_idx >= 0 and icp_idx >= 0:
        _assert(params_idx < ext_idx < icp_idx, "system.init action surface strategy source priority invalid", errors)

    _assert('data["scene_action_surface_strategy"]' in system_init_text, "system.init missing scene_action_surface_strategy output", errors)
    _assert("action_surface_strategy=data.get(\"scene_action_surface_strategy\")" in system_init_text, "system.init missing action strategy pass-through to scene_ready builder", errors)

    _assert("action_surface_strategy: Dict[str, Any] | None" in builder_text, "scene_ready builder missing action_surface_strategy arg", errors)
    _assert('runtime_merged["action_surface_strategy"] = strategy_payload' in builder_text, "scene_ready builder missing strategy runtime injection", errors)
    _assert('runtime_merged["role_code"] = role_code' in builder_text, "scene_ready builder missing role runtime injection", errors)
    _assert('runtime_merged["company_id"] = company_id' in builder_text, "scene_ready builder missing company runtime injection", errors)

    _assert("_resolve_action_surface_strategy" in compiler_text, "compiler missing runtime strategy resolver", errors)
    _assert("_apply_action_surface_strategy" in compiler_text, "compiler missing runtime strategy apply", errors)
    _assert('runtime.get("action_surface_strategy")' in compiler_text, "compiler missing runtime action surface strategy read", errors)

    if errors:
        print("[scene_action_surface_strategy_wiring_guard] FAIL")
        for item in errors:
            print(f" - {item}")
        return 1

    print("[scene_action_surface_strategy_wiring_guard] PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

