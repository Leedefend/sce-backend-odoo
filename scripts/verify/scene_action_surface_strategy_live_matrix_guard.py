#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

import importlib.util
import json
import os
import sys
from pathlib import Path

from intent_smoke_utils import require_ok
from python_http_smoke_utils import get_base_url, http_post_json


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


def _fetch_live_strategy(strategy_inject: dict) -> dict:
    base_url = get_base_url()
    intent_url = f"{base_url}/api/v1/intent"
    db_name = os.getenv("E2E_DB") or os.getenv("DB_NAME") or ""
    login = os.getenv("E2E_LOGIN") or "admin"
    password = os.getenv("E2E_PASSWORD") or os.getenv("ADMIN_PASSWD") or "admin"

    status, login_resp = http_post_json(
        intent_url,
        {"intent": "login", "params": {"db": db_name, "login": login, "password": password}},
        headers={"X-Anonymous-Intent": "1"},
    )
    require_ok(status, login_resp, "login")
    token = _text(_as_dict(login_resp.get("data")).get("token"))
    if not token:
        raise RuntimeError("login response missing token")

    status, init_resp = http_post_json(
        intent_url,
        {
            "intent": "system.init",
            "params": {
                "contract_mode": "user",
                "scene_action_surface_strategy": strategy_inject,
            },
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    require_ok(status, init_resp, "system.init")
    return _as_dict(_as_dict(init_resp.get("data")).get("scene_action_surface_strategy"))


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

    live_case = _as_dict(baseline.get("live_case"))
    if live_case:
        live_errors: list[str] = []
        live_name = _text(live_case.get("name")) or "live_case"
        strategy_inject = _as_dict(live_case.get("strategy_inject"))
        runtime_context = _as_dict(live_case.get("runtime_context"))
        actions = _as_list(live_case.get("actions"))
        expected_tiers = _as_dict(live_case.get("expected_tiers"))
        expected_absent = [_text(item) for item in _as_list(live_case.get("expected_absent")) if _text(item)]
        require_live = _text(os.getenv("SC_SCENE_ACTION_STRATEGY_LIVE_MATRIX_REQUIRE_LIVE")).lower() in {"1", "true", "yes"}

        fetched_strategy: dict = {}
        live_error_text = ""
        try:
            fetched_strategy = _fetch_live_strategy(strategy_inject)
        except Exception as exc:
            live_error_text = str(exc)

        if not fetched_strategy:
            if require_live:
                live_errors.append(f"{live_name}: live strategy fetch failed: {live_error_text or 'unknown error'}")
            else:
                print("[scene_action_surface_strategy_live_matrix_guard] WARN live case skipped")
                if live_error_text:
                    print(f" - {live_error_text}")
        else:
            runtime = {
                "role_code": runtime_context.get("role_code"),
                "company_id": runtime_context.get("company_id"),
                "action_surface_strategy": fetched_strategy,
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
                    f"{live_name}: {expected_key} tier mismatch {keyed.get(expected_key)} != {expected_tier}",
                    live_errors,
                )
            for key in expected_absent:
                _assert(key not in keyed, f"{live_name}: key should be absent after strategy apply: {key}", live_errors)
        errors.extend(live_errors)

    if errors:
        print("[scene_action_surface_strategy_live_matrix_guard] FAIL")
        for item in errors:
            print(f" - {item}")
        return 1

    print("[scene_action_surface_strategy_live_matrix_guard] PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
