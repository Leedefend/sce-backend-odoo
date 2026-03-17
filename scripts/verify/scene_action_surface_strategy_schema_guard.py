#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[2]
SYSTEM_INIT_PATH = ROOT / "addons" / "smart_core" / "handlers" / "system_init.py"
COMPILER_PATH = ROOT / "addons" / "smart_core" / "core" / "scene_dsl_compiler.py"
BASELINE_PATH = ROOT / "scripts" / "verify" / "baselines" / "scene_action_surface_strategy_schema_guard.json"


def _assert(condition: bool, message: str, errors: list[str]) -> None:
    if not condition:
        errors.append(message)


def _index_of(text: str, token: str) -> int:
    try:
        return text.index(token)
    except ValueError:
        return -1


def _load_scene_compiler_module():
    spec = importlib.util.spec_from_file_location("scene_dsl_compiler_action_strategy_schema_guard", COMPILER_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"spec unavailable: {COMPILER_PATH}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def main() -> int:
    errors: list[str] = []
    for path in (SYSTEM_INIT_PATH, COMPILER_PATH, BASELINE_PATH):
        if not path.is_file():
            errors.append(f"missing file: {path}")
    if errors:
        print("[scene_action_surface_strategy_schema_guard] FAIL")
        for item in errors:
            print(f" - {item}")
        return 1

    baseline = json.loads(BASELINE_PATH.read_text(encoding="utf-8"))
    required_top_keys = baseline.get("required_top_keys") if isinstance(baseline.get("required_top_keys"), list) else []
    required_strategy_keys = baseline.get("required_strategy_keys") if isinstance(baseline.get("required_strategy_keys"), list) else []

    system_init_text = SYSTEM_INIT_PATH.read_text(encoding="utf-8")
    compiler_text = COMPILER_PATH.read_text(encoding="utf-8")

    _assert("_normalize_scene_action_surface_strategy" in system_init_text, "system.init missing action strategy normalize function", errors)
    for key in required_top_keys:
        _assert(f'"{key}"' in system_init_text, f"system.init normalize whitelist missing top key: {key}", errors)

    params_idx = _index_of(system_init_text, 'params.get("scene_action_surface_strategy")')
    ext_idx = _index_of(system_init_text, 'ext_facts.get("scene_action_surface_strategy")')
    icp_idx = _index_of(system_init_text, 'smart_core.scene_action_surface_strategy_json')
    _assert(params_idx >= 0, "system.init missing params strategy source", errors)
    _assert(ext_idx >= 0, "system.init missing ext_facts strategy source", errors)
    _assert(icp_idx >= 0, "system.init missing icp strategy source", errors)
    if params_idx >= 0 and ext_idx >= 0 and icp_idx >= 0:
        _assert(params_idx < ext_idx < icp_idx, "system.init strategy source priority invalid", errors)

    for token in (
        "_resolve_action_surface_strategy",
        "_apply_action_surface_strategy",
        "_merge_action_surface_strategy",
    ):
        _assert(token in compiler_text, f"compiler missing strategy token: {token}", errors)
    for key in required_strategy_keys:
        _assert(f'"{key}"' in compiler_text, f"compiler strategy missing key support: {key}", errors)

    try:
        module = _load_scene_compiler_module()
        resolve_strategy = getattr(module, "_resolve_action_surface_strategy", None)
        apply_strategy = getattr(module, "_apply_action_surface_strategy", None)
        _assert(callable(resolve_strategy), "compiler strategy resolver is not callable", errors)
        _assert(callable(apply_strategy), "compiler strategy apply is not callable", errors)
        if callable(resolve_strategy) and callable(apply_strategy):
            runtime = {
                "role_code": "manager",
                "company_id": 2,
                "action_surface_strategy": {
                    "default": {"force_secondary_keys": ["create"]},
                    "by_role": {"manager": {"force_primary_keys": ["open"]}},
                    "by_company": {"2": {"hide_keys": ["submit"]}},
                    "by_company_role": {"2:manager": {"force_contextual_keys": ["create"]}},
                },
            }
            strategy = resolve_strategy(runtime)
            actions = [
                {"key": "create", "tier": "secondary"},
                {"key": "open", "tier": "secondary"},
                {"key": "submit", "tier": "primary"},
            ]
            resolved_actions = apply_strategy(actions, strategy)
            rows = {str(item.get("key") or ""): str(item.get("tier") or "") for item in resolved_actions if isinstance(item, dict)}
            _assert("submit" not in rows, "strategy hide_keys should remove submit", errors)
            _assert(rows.get("open") == "primary", "role override should force open to primary", errors)
            _assert(rows.get("create") == "contextual", "company-role override should force create to contextual", errors)
    except Exception as exc:
        errors.append(f"runtime sample failed: {exc}")

    if errors:
        print("[scene_action_surface_strategy_schema_guard] FAIL")
        for item in errors:
            print(f" - {item}")
        return 1

    print("[scene_action_surface_strategy_schema_guard] PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

