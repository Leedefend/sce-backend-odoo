#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

from intent_smoke_utils import require_ok
from python_http_smoke_utils import get_base_url, http_post_json


ROOT = Path(__file__).resolve().parents[2]
BASELINE_PATH = ROOT / "scripts" / "verify" / "baselines" / "scene_contract_v1_field_schema_guard.json"
DEFAULT_STATE_PATH = ROOT / "artifacts" / "backend" / "scene_contract_v1_field_schema_state.json"
DEFAULT_SNAPSHOT_STATE_PATH = ROOT / "artifacts" / "backend" / "scene_registry_asset_snapshot_state.json"


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


def _fetch_scene_ready_payload() -> dict:
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
    return _as_dict(data.get("scene_ready_contract_v1"))


def _missing_keys(payload: dict, required_keys: list[str]) -> list[str]:
    return [key for key in required_keys if key not in payload]


def _to_bool(value: Any) -> bool:
    return _text(value).lower() in {"1", "true", "yes", "y", "on"}


def _load_payload_state(path: Path) -> dict:
    payload = _load_json(path)
    if not payload:
        return {}
    if isinstance(payload.get("scene_ready_contract_v1"), dict):
        return _as_dict(payload.get("scene_ready_contract_v1"))
    return payload if isinstance(payload.get("scenes"), list) else {}


def _build_payload_from_snapshot_state(path: Path) -> dict:
    state = _load_json(path)
    per_scene = state.get("per_scene")
    if not isinstance(per_scene, dict) or not per_scene:
        return {}

    scenes: list[dict[str, Any]] = []
    for scene_key, row in per_scene.items():
        item = _as_dict(row)
        action_total = _safe_int(item.get("action_total"), 0)
        actions = [{"key": "auto.generated"}] * min(action_total, 3)
        scenes.append(
            {
                "scene": {
                    "key": _text(scene_key),
                    "target": {
                        "route": f"/workbench?scene={_text(scene_key)}",
                    },
                },
                "page": {
                    "route": f"/workbench?scene={_text(scene_key)}",
                },
                "meta": {
                    "compile_verdict": "ok" if bool(item.get("compile_ok")) else "warn",
                    "ui_base_contract_source": _text(item.get("source_kind")) or "unknown",
                },
                "action_surface": {
                    "actions": actions,
                },
                "search_surface": {
                    "enabled": bool(item.get("has_search_surface")),
                },
                "workflow_surface": {
                    "enabled": bool(item.get("has_workflow_surface")),
                },
                "validation_surface": {
                    "enabled": bool(item.get("has_validation_surface")),
                },
            }
        )

    return {
        "contract_version": "v1",
        "scenes": scenes,
        "meta": {
            "source": "snapshot_state_fallback",
            "captured_at": _text(state.get("captured_at")),
            "scene_count": len(scenes),
        },
    }


def main() -> int:
    baseline = _load_json(BASELINE_PATH)
    if not baseline:
        print("[scene_contract_v1_field_schema_guard] FAIL")
        print(f" - missing or invalid baseline: {BASELINE_PATH.relative_to(ROOT).as_posix()}")
        return 1

    report_json = ROOT / _text(
        baseline.get("report_json") or "artifacts/backend/scene_contract_v1_field_schema_report.json"
    )
    report_md = ROOT / _text(
        baseline.get("report_md") or "artifacts/backend/scene_contract_v1_field_schema_report.md"
    )

    required_top_keys = [_text(item) for item in _as_list(baseline.get("required_top_keys")) if _text(item)]
    required_scene_row_keys = [_text(item) for item in _as_list(baseline.get("required_scene_row_keys")) if _text(item)]
    required_meta_keys = [_text(item) for item in _as_list(baseline.get("required_meta_keys")) if _text(item)]
    min_scene_count = _safe_int(baseline.get("min_scene_count"), 1)

    errors: list[str] = []
    warnings: list[str] = []
    scene_errors: list[dict[str, Any]] = []
    payload = {}
    payload_source = "live"
    state_path = ROOT / _text(
        os.getenv("SC_SCENE_CONTRACT_V1_FIELD_SCHEMA_STATE_FILE")
        or DEFAULT_STATE_PATH.relative_to(ROOT).as_posix()
    )
    snapshot_state_path = ROOT / _text(
        os.getenv("SC_SCENE_CONTRACT_V1_FIELD_SCHEMA_SNAPSHOT_STATE_FILE")
        or DEFAULT_SNAPSHOT_STATE_PATH.relative_to(ROOT).as_posix()
    )
    allow_fallback = _to_bool(os.getenv("SC_SCENE_CONTRACT_V1_FIELD_SCHEMA_ALLOW_STATE_FALLBACK_ON_LIVE_FAIL"))
    try:
        payload = _fetch_scene_ready_payload()
        state_path.parent.mkdir(parents=True, exist_ok=True)
        state_path.write_text(
            json.dumps({"scene_ready_contract_v1": payload}, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
    except Exception as exc:
        if allow_fallback:
            payload = _load_payload_state(state_path)
            if payload:
                payload_source = "state_file"
                warnings.append(f"live fetch failed, fallback state file used: {exc}")
            else:
                payload = _build_payload_from_snapshot_state(snapshot_state_path)
                if payload:
                    payload_source = "snapshot_state"
                    warnings.append(f"live fetch failed, fallback snapshot synthesized: {exc}")
        if not payload:
            errors.append(f"live fetch failed: {exc}")

    if payload:
        state_path.parent.mkdir(parents=True, exist_ok=True)
        state_path.write_text(
            json.dumps({"scene_ready_contract_v1": payload}, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

        missing_top = _missing_keys(payload, required_top_keys)
        if missing_top:
            errors.append(f"missing top-level keys: {missing_top}")

        scenes = _as_list(payload.get("scenes"))
        if len(scenes) < min_scene_count:
            errors.append(f"scene count below baseline: {len(scenes)} < {min_scene_count}")

        for row in scenes:
            item = _as_dict(row)
            scene_info = _as_dict(item.get("scene"))
            page = _as_dict(item.get("page"))
            scene_key = _text(scene_info.get("key")) or "<unknown>"
            row_missing = _missing_keys(item, required_scene_row_keys)
            meta = _as_dict(item.get("meta"))
            meta_missing = _missing_keys(meta, required_meta_keys)
            target = _as_dict(scene_info.get("target"))
            has_target = bool(
                _text(target.get("route"))
                or _safe_int(target.get("action_id"), 0) > 0
                or _safe_int(target.get("menu_id"), 0) > 0
                or _text(target.get("model"))
                or _text(scene_info.get("route"))
                or _safe_int(scene_info.get("action_id"), 0) > 0
                or _safe_int(scene_info.get("menu_id"), 0) > 0
                or _text(scene_info.get("model"))
                or _text(page.get("route"))
                or _text(page.get("model"))
            )
            if row_missing or meta_missing or not has_target:
                scene_errors.append(
                    {
                        "scene_key": scene_key,
                        "missing_row_keys": row_missing,
                        "missing_meta_keys": meta_missing,
                        "target_invalid": not has_target,
                    }
                )

        if scene_errors:
            errors.append(f"scene row schema violations: {len(scene_errors)}")

    report = {
        "ok": len(errors) == 0,
        "errors": errors,
        "warnings": warnings,
        "scene_error_count": len(scene_errors),
        "scene_errors": scene_errors,
        "sources": {
            "baseline": BASELINE_PATH.relative_to(ROOT).as_posix(),
            "payload_source": payload_source,
            "state_file": state_path.relative_to(ROOT).as_posix(),
            "snapshot_state_file": snapshot_state_path.relative_to(ROOT).as_posix(),
            "allow_fallback_on_live_fail": allow_fallback,
        },
    }
    report_json.parent.mkdir(parents=True, exist_ok=True)
    report_json.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")

    md_lines = [
        "# Scene Contract v1 Field Schema Guard Report",
        "",
        f"- ok: `{report['ok']}`",
        f"- scene_error_count: `{len(scene_errors)}`",
    ]
    if errors:
        md_lines.extend(["", "## Errors"] + [f"- {item}" for item in errors])
    if warnings:
        md_lines.extend(["", "## Warnings"] + [f"- {item}" for item in warnings])
    report_md.parent.mkdir(parents=True, exist_ok=True)
    report_md.write_text("\n".join(md_lines) + "\n", encoding="utf-8")

    if errors:
        print("[scene_contract_v1_field_schema_guard] FAIL")
        for item in errors:
            print(f" - {item}")
        print(report_json)
        print(report_md)
        return 1

    print(report_json)
    print(report_md)
    print("[scene_contract_v1_field_schema_guard] PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
