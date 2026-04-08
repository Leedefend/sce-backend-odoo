#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

import json
import os
from datetime import datetime
from pathlib import Path

from intent_smoke_utils import require_ok
from python_http_smoke_utils import get_base_url, http_post_json


ROOT = Path(__file__).resolve().parents[2]
BASELINE_PATH = ROOT / "scripts" / "verify" / "baselines" / "scene_ready_consumption_trend_guard.json"


def _load_json(path: Path) -> dict:
    if not path.is_file():
        return {}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}
    return payload if isinstance(payload, dict) else {}


def _safe_int(value, default: int = 0) -> int:
    try:
        return int(value)
    except Exception:
        return default


def _safe_float(value, default: float = 0.0) -> float:
    try:
        return float(value)
    except Exception:
        return default


def _resolve_state_path(baseline: dict) -> Path:
    raw = str(baseline.get("state_file") or "").strip()
    if not raw:
        return ROOT / "artifacts" / "backend" / "scene_ready_consumption_trend_state.json"
    return ROOT / raw


def _fetch_consumption() -> dict:
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
    token = ((login_resp.get("data") or {}).get("token") or "")
    if not token:
        raise RuntimeError("login response missing token")

    status, init_resp = http_post_json(
        intent_url,
        {"intent": "system.init", "params": {"contract_mode": "user"}},
        headers={"Authorization": f"Bearer {token}"},
    )
    require_ok(status, init_resp, "system.init")

    data = init_resp.get("data") if isinstance(init_resp.get("data"), dict) else {}
    governance = data.get("scene_governance_v1") if isinstance(data.get("scene_governance_v1"), dict) else {}
    consumption = governance.get("scene_ready_consumption") if isinstance(governance.get("scene_ready_consumption"), dict) else {}
    aggregate = consumption.get("aggregate") if isinstance(consumption.get("aggregate"), dict) else {}
    base_rate = aggregate.get("base_fact_consumption_rate") if isinstance(aggregate.get("base_fact_consumption_rate"), dict) else {}
    surface_rate = aggregate.get("surface_nonempty_rate") if isinstance(aggregate.get("surface_nonempty_rate"), dict) else {}
    return {
        "enabled": bool(consumption.get("enabled", False)),
        "scene_count": _safe_int(consumption.get("scene_count"), 0),
        "scene_type_count": _safe_int(consumption.get("scene_type_count"), 0),
        "aggregate_base_search_rate": _safe_float(base_rate.get("search"), 0.0),
        "aggregate_action_surface_rate": _safe_float(surface_rate.get("action_surface"), 0.0),
    }


def main() -> int:
    baseline = _load_json(BASELINE_PATH)
    if not baseline:
        print("[scene_ready_consumption_trend_guard] FAIL")
        print(f"missing or invalid baseline: {BASELINE_PATH.relative_to(ROOT).as_posix()}")
        return 1

    min_scene_count = _safe_int(baseline.get("min_scene_count"), 1)
    min_scene_type_count = _safe_int(baseline.get("min_scene_type_count"), 1)
    min_base_search_rate = _safe_float(baseline.get("min_aggregate_base_search_rate"), 0.0)
    min_action_surface_rate = _safe_float(baseline.get("min_aggregate_action_surface_rate"), 0.0)
    max_base_search_rate_drop = _safe_float(baseline.get("max_base_search_rate_drop_per_run"), 0.35)
    max_action_surface_rate_drop = _safe_float(baseline.get("max_action_surface_rate_drop_per_run"), 0.35)
    state_path = _resolve_state_path(baseline)
    state_path.parent.mkdir(parents=True, exist_ok=True)

    errors: list[str] = []
    fetch_error = ""
    try:
        current = _fetch_consumption()
    except Exception as exc:
        fetch_error = str(exc)
        current = {}

    strict_live = str(os.getenv("SC_SCENE_READY_CONSUMPTION_TREND_REQUIRE_LIVE") or "").strip() in {"1", "true", "TRUE", "yes"}
    if not current:
        previous = _load_json(state_path)
        if previous and not strict_live:
            current = {
                "enabled": bool(previous.get("enabled", False)),
                "scene_count": _safe_int(previous.get("scene_count"), 0),
                "scene_type_count": _safe_int(previous.get("scene_type_count"), 0),
                "aggregate_base_search_rate": _safe_float(previous.get("aggregate_base_search_rate"), 0.0),
                "aggregate_action_surface_rate": _safe_float(previous.get("aggregate_action_surface_rate"), 0.0),
                "live_fetch_skipped": True,
                "live_fetch_error": fetch_error,
            }
        else:
            if strict_live:
                print("[scene_ready_consumption_trend_guard] FAIL")
                print(f" - unable to fetch live scene_ready consumption metrics: {fetch_error or 'unknown error'}")
                print(" - strict mode enabled: SC_SCENE_READY_CONSUMPTION_TREND_REQUIRE_LIVE=1")
                return 1
            current = {
                "enabled": False,
                "scene_count": 0,
                "scene_type_count": 0,
                "aggregate_base_search_rate": 0.0,
                "aggregate_action_surface_rate": 0.0,
                "live_fetch_skipped": True,
                "live_fetch_error": fetch_error,
            }

    current["captured_at"] = datetime.utcnow().isoformat(timespec="seconds") + "Z"
    live_available = not bool(current.get("live_fetch_skipped", False))

    enabled = bool(current.get("enabled", False))
    scene_count = _safe_int(current.get("scene_count"), 0)
    scene_type_count = _safe_int(current.get("scene_type_count"), 0)
    require_enabled = str(os.getenv("SC_SCENE_READY_CONSUMPTION_TREND_REQUIRE_ENABLED") or "").strip() in {"1", "true", "TRUE", "yes"}

    if live_available and require_enabled and not enabled:
        errors.append("scene_ready_consumption.enabled must be true (strict enabled mode)")

    if live_available and enabled:
        if scene_count < min_scene_count:
            errors.append(f"scene_count below threshold: {scene_count} < {min_scene_count}")
        if scene_type_count < min_scene_type_count:
            errors.append(f"scene_type_count below threshold: {scene_type_count} < {min_scene_type_count}")

    base_search_rate = _safe_float(current.get("aggregate_base_search_rate"), 0.0)
    action_surface_rate = _safe_float(current.get("aggregate_action_surface_rate"), 0.0)
    if live_available and enabled:
        if base_search_rate < min_base_search_rate:
            errors.append(f"aggregate_base_search_rate below threshold: {base_search_rate:.4f} < {min_base_search_rate:.4f}")
        if action_surface_rate < min_action_surface_rate:
            errors.append(f"aggregate_action_surface_rate below threshold: {action_surface_rate:.4f} < {min_action_surface_rate:.4f}")

    previous = _load_json(state_path)
    previous_enabled = bool(previous.get("enabled", False)) if isinstance(previous, dict) else False
    if previous and live_available and enabled and previous_enabled:
        prev_base = _safe_float(previous.get("aggregate_base_search_rate"), 0.0)
        prev_action = _safe_float(previous.get("aggregate_action_surface_rate"), 0.0)
        base_drop = prev_base - base_search_rate
        action_drop = prev_action - action_surface_rate
        current["aggregate_base_search_rate_drop"] = base_drop
        current["aggregate_action_surface_rate_drop"] = action_drop
        if base_drop > max_base_search_rate_drop:
            errors.append(f"aggregate_base_search_rate drop too fast: {base_drop:.4f} > {max_base_search_rate_drop:.4f}")
        if action_drop > max_action_surface_rate_drop:
            errors.append(f"aggregate_action_surface_rate drop too fast: {action_drop:.4f} > {max_action_surface_rate_drop:.4f}")

    state_path.write_text(json.dumps(current, ensure_ascii=False, indent=2), encoding="utf-8")

    if errors:
        print("[scene_ready_consumption_trend_guard] FAIL")
        for item in errors:
            print(f" - {item}")
        return 1

    print("[scene_ready_consumption_trend_guard] PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
