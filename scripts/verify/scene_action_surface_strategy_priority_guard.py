#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

import importlib
import json
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[2]
COMPILER_PATH = ROOT / "addons" / "smart_core" / "core" / "scene_dsl_compiler.py"
BASELINE_PATH = ROOT / "scripts" / "verify" / "baselines" / "scene_action_surface_strategy_priority_guard.json"


def _assert(condition: bool, message: str, errors: list[str]) -> None:
    if not condition:
        errors.append(message)


def _load_compiler_module():
    addons_path = str(ROOT / "addons")
    if addons_path not in sys.path:
        sys.path.insert(0, addons_path)
    return importlib.import_module("smart_core.core.scene_dsl_compiler")


def main() -> int:
    errors: list[str] = []
    for path in (COMPILER_PATH, BASELINE_PATH):
        if not path.is_file():
            errors.append(f"missing file: {path}")
    if errors:
        print("[scene_action_surface_strategy_priority_guard] FAIL")
        for item in errors:
            print(f" - {item}")
        return 1

    compiler_text = COMPILER_PATH.read_text(encoding="utf-8")
    for token in (
        "_resolve_action_surface_strategy",
        "if company_key and company_key in by_company",
        "if role_code and role_code in by_role",
        "if company_key and role_code",
    ):
        _assert(token in compiler_text, f"compiler missing strategy precedence token: {token}", errors)

    try:
        baseline = json.loads(BASELINE_PATH.read_text(encoding="utf-8"))
        module = _load_compiler_module()
        resolve_strategy = getattr(module, "_resolve_action_surface_strategy", None)
        apply_strategy = getattr(module, "_apply_action_surface_strategy", None)
        _assert(callable(resolve_strategy), "strategy resolver not callable", errors)
        _assert(callable(apply_strategy), "strategy apply not callable", errors)
        if callable(resolve_strategy) and callable(apply_strategy):
            runtime_context = baseline.get("runtime_context") if isinstance(baseline.get("runtime_context"), dict) else {}
            strategy = baseline.get("strategy") if isinstance(baseline.get("strategy"), dict) else {}
            expected = baseline.get("expected") if isinstance(baseline.get("expected"), dict) else {}

            runtime = {
                "role_code": runtime_context.get("role_code"),
                "company_id": runtime_context.get("company_id"),
                "action_surface_strategy": strategy,
            }
            resolved = resolve_strategy(runtime)
            actions = [
                {"key": "same_key", "tier": "secondary"},
                {"key": "same_secondary", "tier": "primary"},
                {"key": "hide_me", "tier": "primary"},
                {"key": "company_hide", "tier": "secondary"},
                {"key": "role_hide", "tier": "contextual"},
            ]
            out = apply_strategy(actions, resolved)
            keyed = {str(item.get("key") or ""): str(item.get("tier") or "") for item in out if isinstance(item, dict)}

            for key, tier in expected.items():
                if key == "hide_absent":
                    continue
                _assert(keyed.get(str(key)) == str(tier), f"priority mismatch: {key} -> {keyed.get(str(key))} != {tier}", errors)

            for key in expected.get("hide_absent") if isinstance(expected.get("hide_absent"), list) else []:
                _assert(str(key) not in keyed, f"hidden key should be absent: {key}", errors)
    except Exception as exc:
        errors.append(f"runtime sample failed: {exc}")

    if errors:
        print("[scene_action_surface_strategy_priority_guard] FAIL")
        for item in errors:
            print(f" - {item}")
        return 1

    print("[scene_action_surface_strategy_priority_guard] PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
