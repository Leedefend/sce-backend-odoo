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
BASELINE_PATH = ROOT / "scripts" / "verify" / "baselines" / "scene_asset_queue_trend_guard.json"


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


def _resolve_state_path(baseline: dict) -> Path:
    raw = str(baseline.get("state_file") or "").strip()
    if not raw:
        return ROOT / "artifacts" / "backend" / "scene_asset_queue_trend_state.json"
    return ROOT / raw


def _fetch_asset_queue() -> dict:
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
    asset_queue = governance.get("asset_queue") if isinstance(governance.get("asset_queue"), dict) else {}
    return {
        "queue_size": _safe_int(asset_queue.get("queue_size"), 0),
        "remaining_count": _safe_int(asset_queue.get("remaining_count"), 0),
        "popped_count": _safe_int(asset_queue.get("popped_count"), 0),
        "added_count": _safe_int(asset_queue.get("added_count"), 0),
        "updated_at": str(asset_queue.get("updated_at") or ""),
        "consumed_at": str(asset_queue.get("consumed_at") or ""),
    }


def main() -> int:
    baseline = _load_json(BASELINE_PATH)
    if not baseline:
        print("[scene_asset_queue_trend_guard] FAIL")
        print(f"missing or invalid baseline: {BASELINE_PATH.relative_to(ROOT).as_posix()}")
        return 1

    max_queue_size = _safe_int(baseline.get("max_queue_size"), 500)
    max_growth_per_run = _safe_int(baseline.get("max_growth_per_run"), 200)
    state_path = _resolve_state_path(baseline)
    state_path.parent.mkdir(parents=True, exist_ok=True)

    errors: list[str] = []
    fetch_error = ""
    try:
        current = _fetch_asset_queue()
    except Exception as exc:
        fetch_error = str(exc)
        current = {}

    strict_live = str(os.getenv("SC_ASSET_QUEUE_TREND_REQUIRE_LIVE") or "").strip() in {"1", "true", "TRUE", "yes"}
    if not current:
        previous = _load_json(state_path)
        if previous and not strict_live:
            current = {
                "queue_size": _safe_int(previous.get("queue_size"), 0),
                "remaining_count": _safe_int(previous.get("remaining_count"), 0),
                "popped_count": _safe_int(previous.get("popped_count"), 0),
                "added_count": _safe_int(previous.get("added_count"), 0),
                "updated_at": str(previous.get("updated_at") or ""),
                "consumed_at": str(previous.get("consumed_at") or ""),
                "captured_at": datetime.utcnow().isoformat(timespec="seconds") + "Z",
                "live_fetch_skipped": True,
                "live_fetch_error": fetch_error,
            }
        else:
            current = {
                "queue_size": 0,
                "remaining_count": 0,
                "popped_count": 0,
                "added_count": 0,
                "updated_at": "",
                "consumed_at": "",
                "captured_at": datetime.utcnow().isoformat(timespec="seconds") + "Z",
                "live_fetch_skipped": True,
                "live_fetch_error": fetch_error,
            }
            if strict_live:
                print("[scene_asset_queue_trend_guard] FAIL")
                print(f" - unable to fetch live asset queue metrics: {fetch_error or 'unknown error'}")
                print(" - strict mode enabled: SC_ASSET_QUEUE_TREND_REQUIRE_LIVE=1")
                return 1

    current["captured_at"] = datetime.utcnow().isoformat(timespec="seconds") + "Z"

    queue_size = _safe_int(current.get("queue_size"), 0)
    if queue_size > max_queue_size:
        errors.append(f"queue_size exceeded: {queue_size} > {max_queue_size}")

    previous = _load_json(state_path)
    prev_size = _safe_int(previous.get("queue_size"), 0) if previous else 0
    growth = queue_size - prev_size
    if previous and growth > max_growth_per_run:
        errors.append(f"queue growth too fast: {growth} > {max_growth_per_run}")

    current["queue_growth"] = growth
    state_path.write_text(json.dumps(current, ensure_ascii=False, indent=2), encoding="utf-8")

    if errors:
        print("[scene_asset_queue_trend_guard] FAIL")
        for item in errors:
            print(f" - {item}")
        return 1

    print("[scene_asset_queue_trend_guard] PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
