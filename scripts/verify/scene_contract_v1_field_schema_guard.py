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
    scene_errors: list[dict[str, Any]] = []
    payload = {}
    try:
        payload = _fetch_scene_ready_payload()
    except Exception as exc:
        errors.append(f"live fetch failed: {exc}")

    if payload:
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
        "scene_error_count": len(scene_errors),
        "scene_errors": scene_errors,
        "sources": {
            "baseline": BASELINE_PATH.relative_to(ROOT).as_posix(),
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
