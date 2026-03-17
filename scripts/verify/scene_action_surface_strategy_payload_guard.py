#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

import json
import os
from pathlib import Path

from intent_smoke_utils import require_ok
from python_http_smoke_utils import get_base_url, http_post_json


ROOT = Path(__file__).resolve().parents[2]
SYSTEM_INIT_PATH = ROOT / "addons" / "smart_core" / "handlers" / "system_init.py"
BASELINE_PATH = ROOT / "scripts" / "verify" / "baselines" / "scene_action_surface_strategy_payload_guard.json"


def _text(value) -> str:
    return str(value or "").strip()


def _as_dict(value):
    return value if isinstance(value, dict) else {}


def _as_list(value):
    return value if isinstance(value, list) else []


def _load_json(path: Path) -> dict:
    if not path.is_file():
        return {}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}
    return payload if isinstance(payload, dict) else {}


def _assert(condition: bool, message: str, errors: list[str]) -> None:
    if not condition:
        errors.append(message)


def _validate_strategy_shape(payload: dict, required_top_keys: list[str], required_strategy_keys: list[str], errors: list[str], *, context: str) -> None:
    for key in payload.keys():
        _assert(key in required_top_keys, f"{context} invalid top key: {key}", errors)
    for top_key, top_value in payload.items():
        top_payload = _as_dict(top_value)
        if top_key == "default":
            for rule_key, rule_value in top_payload.items():
                _assert(rule_key in required_strategy_keys, f"{context} default invalid strategy key: {rule_key}", errors)
                _assert(isinstance(rule_value, list), f"{context} default.{rule_key} must be list", errors)
            continue
        for scope_key, scope_rule in top_payload.items():
            _assert(bool(_text(scope_key)), f"{context} {top_key} has empty scope key", errors)
            scope_payload = _as_dict(scope_rule)
            for rule_key, rule_value in scope_payload.items():
                _assert(rule_key in required_strategy_keys, f"{context} {top_key}.{scope_key} invalid strategy key: {rule_key}", errors)
                _assert(isinstance(rule_value, list), f"{context} {top_key}.{scope_key}.{rule_key} must be list", errors)


def _fetch_strategy(sample_input: dict) -> dict:
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
    token = _text((_as_dict(login_resp.get("data"))).get("token"))
    if not token:
        raise RuntimeError("login response missing token")

    status, init_resp = http_post_json(
        intent_url,
        {
            "intent": "system.init",
            "params": {
                "contract_mode": "user",
                "scene_action_surface_strategy": sample_input,
            },
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    require_ok(status, init_resp, "system.init")

    data = _as_dict(init_resp.get("data"))
    return _as_dict(data.get("scene_action_surface_strategy"))


def main() -> int:
    errors: list[str] = []
    if not SYSTEM_INIT_PATH.is_file():
        errors.append(f"missing file: {SYSTEM_INIT_PATH}")
    baseline = _load_json(BASELINE_PATH)
    if not baseline:
        errors.append(f"missing or invalid baseline: {BASELINE_PATH.relative_to(ROOT).as_posix()}")
    if errors:
        print("[scene_action_surface_strategy_payload_guard] FAIL")
        for item in errors:
            print(f" - {item}")
        return 1

    required_top_keys = [_text(item) for item in _as_list(baseline.get("required_top_keys")) if _text(item)]
    required_strategy_keys = [_text(item) for item in _as_list(baseline.get("required_strategy_keys")) if _text(item)]
    sample_input = _as_dict(baseline.get("sample_input_strategy"))
    expected_output = _as_dict(baseline.get("expected_normalized_strategy"))

    system_init_text = SYSTEM_INIT_PATH.read_text(encoding="utf-8")
    _assert('data["scene_action_surface_strategy"]' in system_init_text, "system.init missing scene_action_surface_strategy payload output", errors)
    for token in ("_normalize_scene_action_surface_strategy", "force_primary_keys", "force_secondary_keys", "force_contextual_keys", "hide_keys"):
        _assert(token in system_init_text, f"system.init missing strategy normalize token: {token}", errors)

    _validate_strategy_shape(expected_output, required_top_keys, required_strategy_keys, errors, context="baseline.expected_normalized_strategy")

    live_payload: dict = {}
    live_error = ""
    try:
        live_payload = _fetch_strategy(sample_input)
    except Exception as exc:
        live_error = str(exc)

    require_live = _text(os.getenv("SC_SCENE_ACTION_SURFACE_STRATEGY_PAYLOAD_REQUIRE_LIVE")).lower() in {"1", "true", "yes"}
    if not live_payload:
        if require_live:
            errors.append(f"unable to fetch live strategy payload: {live_error or 'unknown error'}")
        else:
            print("[scene_action_surface_strategy_payload_guard] WARN live check skipped")
            if live_error:
                print(f" - {live_error}")
    else:
        _validate_strategy_shape(live_payload, required_top_keys, required_strategy_keys, errors, context="system.init.scene_action_surface_strategy")
        if live_payload != expected_output:
            errors.append(
                "system.init.scene_action_surface_strategy mismatch expected normalized baseline"
            )

    if errors:
        print("[scene_action_surface_strategy_payload_guard] FAIL")
        for item in errors:
            print(f" - {item}")
        return 1

    print("[scene_action_surface_strategy_payload_guard] PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

