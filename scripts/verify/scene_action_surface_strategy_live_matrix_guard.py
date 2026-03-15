#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
COMPILER_PATH = ROOT / "addons" / "smart_core" / "core" / "scene_dsl_compiler.py"
BASELINE_PATH = ROOT / "scripts" / "verify" / "baselines" / "scene_action_surface_strategy_live_matrix_guard.json"


def _as_dict(value):
    return value if isinstance(value, dict) else {}


def _as_list(value):
    return value if isinstance(value, list) else []


def _text(value) -> str:
    return str(value or "").strip()


def _assert(condition: bool, message: str, errors: list[str]) -> None:
    if not condition:
        errors.append(message)


def _load_compiler_module():
    spec = importlib.util.spec_from_file_location("scene_dsl_compiler_action_strategy_live_matrix_guard", COMPILER_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"spec unavailable: {COMPILER_PATH}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def main() -> int:
    errors: list[str] = []
    if not COMPILER_PATH.is_file():
        errors.append(f"missing file: {COMPILER_PATH}")
    if not BASELINE_PATH.is_file():
        errors.append(f"missing file: {BASELINE_PATH}")
    if errors:
        print("[scene_action_surface_strategy_live_matrix_guard] FAIL")
        for item in errors:
            print(f" - {item}")
        return 1

    try:
        baseline = json.loads(BASELINE_PATH.read_text(encoding="utf-8"))
    except Exception as exc:
        print("[scene_action_surface_strategy_live_matrix_guard] FAIL")
        print(f" - invalid baseline json: {exc}")
        return 1

    cases = _as_list(baseline.get("cases"))
    if not cases:
        print("[scene_action_surface_strategy_live_matrix_guard] FAIL")
        print(" - baseline.cases is empty")
        return 1

    module = _load_compiler_module()
    resolve_strategy = getattr(module, "_resolve_action_surface_strategy", None)
    apply_strategy = getattr(module, "_apply_action_surface_strategy", None)
    _assert(callable(resolve_strategy), "strategy resolver not callable", errors)
    _assert(callable(apply_strategy), "strategy apply not callable", errors)
    if errors:
        print("[scene_action_surface_strategy_live_matrix_guard] FAIL")
        for item in errors:
            print(f" - {item}")
        return 1

    for index, case in enumerate(cases):
        row = _as_dict(case)
        name = _text(row.get("name")) or f"case_{index + 1}"
        runtime_context = _as_dict(row.get("runtime_context"))
        strategy = _as_dict(row.get("strategy"))
        actions = _as_list(row.get("actions"))
        expected_tiers = _as_dict(row.get("expected_tiers"))
        expected_absent = [_text(item) for item in _as_list(row.get("expected_absent")) if _text(item)]

        runtime = {
            "role_code": runtime_context.get("role_code"),
            "company_id": runtime_context.get("company_id"),
            "action_surface_strategy": strategy,
        }
        resolved = resolve_strategy(runtime)
        output = apply_strategy(actions, resolved)
        keyed = {
            _text(_as_dict(item).get("key")): _text(_as_dict(item).get("tier"))
            for item in output
            if isinstance(item, dict) and _text(_as_dict(item).get("key"))
        }

        for key, tier in expected_tiers.items():
            expected_key = _text(key)
            expected_tier = _text(tier)
            _assert(
                keyed.get(expected_key) == expected_tier,
                f"{name}: {expected_key} tier mismatch {keyed.get(expected_key)} != {expected_tier}",
                errors,
            )
        for key in expected_absent:
            _assert(key not in keyed, f"{name}: key should be absent after strategy apply: {key}", errors)

    if errors:
        print("[scene_action_surface_strategy_live_matrix_guard] FAIL")
        for item in errors:
            print(f" - {item}")
        return 1

    print("[scene_action_surface_strategy_live_matrix_guard] PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

