#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Any

from intent_smoke_utils import require_ok
from python_http_smoke_utils import get_base_url, http_post_json


ROOT = Path(__file__).resolve().parents[2]
BASELINE_PATH = ROOT / "scripts" / "verify" / "baselines" / "scene_registry_asset_snapshot_guard.json"


def _text(value: Any) -> str:
    return str(value or "").strip()


def _as_dict(value: Any) -> dict:
    return value if isinstance(value, dict) else {}


def _as_list(value: Any) -> list:
    return value if isinstance(value, list) else []


def _safe_int(value: Any, default: int = 0) -> int:
    try:
        return int(value)
    except Exception:
        return default


def _load_json(path: Path) -> dict:
    if not path.is_file():
        return {}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}
    return payload if isinstance(payload, dict) else {}


def _resolve_state_path(baseline: dict) -> Path:
    env_override = _text(os.getenv("SC_SCENE_REGISTRY_ASSET_SNAPSHOT_STATE_FILE"))
    if env_override:
        return ROOT / env_override
    raw = _text(baseline.get("state_file"))
    if not raw:
        return ROOT / "artifacts" / "backend" / "scene_registry_asset_snapshot_state.json"
    return ROOT / raw


def _fetch_live_snapshot() -> dict:
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
        {"intent": "system.init", "params": {"contract_mode": "user"}},
        headers={"Authorization": f"Bearer {token}"},
    )
    require_ok(status, init_resp, "system.init")

    data = _as_dict(init_resp.get("data"))
    nav_meta = _as_dict(data.get("nav_meta"))
    scene_ready = _as_dict(data.get("scene_ready_contract_v1"))
    scene_meta = _as_dict(scene_ready.get("meta"))
    scenes = _as_list(scene_ready.get("scenes"))

    scene_keys: list[str] = []
    per_scene: dict[str, dict[str, Any]] = {}
    source_kind_counts: dict[str, int] = {
        "asset": 0,
        "runtime_fallback": 0,
        "runtime_minimal": 0,
        "inline": 0,
        "none": 0,
        "other": 0,
    }
    for row in scenes:
        payload = _as_dict(row)
        scene_info = _as_dict(payload.get("scene"))
        scene_key = _text(scene_info.get("key"))
        if not scene_key:
            continue
        scene_keys.append(scene_key)
        meta = _as_dict(payload.get("meta"))
        verdict = _as_dict(meta.get("compile_verdict"))
        source_meta = _as_dict(meta.get("ui_base_contract_source"))
        source_kind = _text(source_meta.get("kind")) or "none"
        if source_kind not in source_kind_counts:
            source_kind = "other"
        source_kind_counts[source_kind] = _safe_int(source_kind_counts.get(source_kind), 0) + 1
        action_surface = _as_dict(payload.get("action_surface"))
        action_counts = _as_dict(action_surface.get("counts"))
        per_scene[scene_key] = {
            "base_contract_bound": bool(verdict.get("base_contract_bound")),
            "compile_ok": bool(verdict.get("ok")),
            "source_kind": source_kind,
            "action_total": _safe_int(action_counts.get("total"), 0),
            "has_search_surface": bool(_as_dict(payload.get("search_surface"))),
            "has_workflow_surface": bool(_as_dict(payload.get("workflow_surface"))),
            "has_validation_surface": bool(_as_dict(payload.get("validation_surface"))),
        }

    total_scene_count = _safe_int(scene_meta.get("scene_count"), len(scene_keys))
    denom = float(total_scene_count) if total_scene_count > 0 else 1.0
    source_kind_ratios = {
        key: float(_safe_int(value, 0)) / denom
        for key, value in source_kind_counts.items()
    }

    return {
        "runtime_env": _text(_as_dict(_as_dict(data.get("scene_governance_v1")).get("delivery_policy")).get("runtime_env")) or _text(os.getenv("ENV") or "dev"),
        "role_code": _text(nav_meta.get("role_surface_code")) or "unknown",
        "scene_count": total_scene_count,
        "base_contract_bound_scene_count": _safe_int(scene_meta.get("base_contract_bound_scene_count"), 0),
        "compile_issue_scene_count": _safe_int(scene_meta.get("compile_issue_scene_count"), 0),
        "scene_keys": sorted(set(scene_keys)),
        "source_kind_counts": source_kind_counts,
        "source_kind_ratios": source_kind_ratios,
        "per_scene": per_scene,
    }


def _assert(condition: bool, message: str, errors: list[str]) -> None:
    if not condition:
        errors.append(message)


def main() -> int:
    baseline = _load_json(BASELINE_PATH)
    if not baseline:
        print("[scene_registry_asset_snapshot_guard] FAIL")
        print(f" - missing or invalid baseline: {BASELINE_PATH.relative_to(ROOT).as_posix()}")
        return 1

    required_scene_keys = [_text(item) for item in _as_list(baseline.get("required_scene_keys")) if _text(item)]
    min_scene_count = _safe_int(baseline.get("min_scene_count"), 1)
    min_bound_scene_count = _safe_int(baseline.get("min_base_contract_bound_scene_count"), 1)
    min_matched_required_scene_count = _safe_int(baseline.get("min_matched_required_scene_count"), 1)
    state_path = _resolve_state_path(baseline)
    state_path.parent.mkdir(parents=True, exist_ok=True)

    errors: list[str] = []
    warnings: list[str] = []
    live_error = ""
    snapshot: dict = {}
    try:
        snapshot = _fetch_live_snapshot()
    except Exception as exc:
        live_error = str(exc)

    strict_live = _text(os.getenv("SC_SCENE_REGISTRY_ASSET_SNAPSHOT_REQUIRE_LIVE")).lower() in {"1", "true", "yes"}
    if not snapshot:
        previous = _load_json(state_path)
        if previous and not strict_live:
            snapshot = dict(previous)
            snapshot["live_fetch_skipped"] = True
            snapshot["live_fetch_error"] = live_error
        elif strict_live:
            print("[scene_registry_asset_snapshot_guard] FAIL")
            print(f" - unable to fetch live snapshot: {live_error or 'unknown error'}")
            return 1
        else:
            snapshot = {
                "runtime_env": _text(os.getenv("ENV") or "dev"),
                "role_code": "unknown",
                "scene_count": 0,
                "base_contract_bound_scene_count": 0,
                "compile_issue_scene_count": 0,
                "scene_keys": [],
                "per_scene": {},
                "live_fetch_skipped": True,
                "live_fetch_error": live_error,
            }

    scene_count = _safe_int(snapshot.get("scene_count"), 0)
    bound_scene_count = _safe_int(snapshot.get("base_contract_bound_scene_count"), 0)
    scene_keys = [_text(item) for item in _as_list(snapshot.get("scene_keys")) if _text(item)]
    matched_required_scene_keys = [key for key in required_scene_keys if key in scene_keys]
    matched_required_scene_count = len(matched_required_scene_keys)

    live_available = not bool(snapshot.get("live_fetch_skipped", False))
    if live_available and scene_count > 0:
        _assert(scene_count >= min_scene_count, f"scene_count below threshold: {scene_count} < {min_scene_count}", errors)
        _assert(
            bound_scene_count >= min_bound_scene_count,
            f"base_contract_bound_scene_count below threshold: {bound_scene_count} < {min_bound_scene_count}",
            errors,
        )
        _assert(
            matched_required_scene_count >= min_matched_required_scene_count,
            "matched required scenes below threshold: "
            f"{matched_required_scene_count} < {min_matched_required_scene_count}; "
            f"matched={matched_required_scene_keys}",
            errors,
        )
    elif live_available and scene_count <= 0:
        warnings.append("live snapshot has no scenes; threshold checks skipped")

    snapshot["matched_required_scene_keys"] = matched_required_scene_keys
    snapshot["matched_required_scene_count"] = matched_required_scene_count
    snapshot["captured_at"] = datetime.utcnow().isoformat(timespec="seconds") + "Z"
    state_path.write_text(json.dumps(snapshot, ensure_ascii=False, indent=2), encoding="utf-8")

    if errors:
        print("[scene_registry_asset_snapshot_guard] FAIL")
        for item in errors:
            print(f" - {item}")
        return 1

    if not live_available:
        print("[scene_registry_asset_snapshot_guard] WARN live check skipped")
        if live_error:
            print(f" - {live_error}")
    for warning in warnings:
        print(f"[scene_registry_asset_snapshot_guard] WARN {warning}")
    print("[scene_registry_asset_snapshot_guard] PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
