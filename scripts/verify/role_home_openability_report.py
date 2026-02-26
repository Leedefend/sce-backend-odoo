#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

import hashlib
import json
import os
import time
from pathlib import Path

from python_http_smoke_utils import get_base_url, http_post_json


ROOT = Path(__file__).resolve().parents[2]
ROLE_SOURCE_JSON = ROOT / "docs" / "product" / "delivery" / "v1" / "role_package_source_v1.json"
ROLE_FLOOR_JSON = ROOT / "artifacts" / "backend" / "role_capability_floor_prod_like.json"
SCENE_MAP_JSON = ROOT / "artifacts" / "backend" / "scene_domain_mapping.json"
REPORT_JSON = ROOT / "artifacts" / "product" / "role_home_openability_report.json"
REPORT_MD = ROOT / "docs" / "ops" / "audit" / "role_home_openability_report.md"


def _load(path: Path) -> dict:
    if not path.is_file():
        return {}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}
    return payload if isinstance(payload, dict) else {}


def _norm(v: object) -> str:
    return str(v or "").strip()


def _intent(url: str, token: str | None, intent: str, params: dict, anonymous: bool = False):
    headers = {}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    if anonymous:
        headers["X-Anonymous-Intent"] = "1"
    ts0 = time.perf_counter()
    status, payload = http_post_json(url, {"intent": intent, "params": params}, headers=headers)
    latency = (time.perf_counter() - ts0) * 1000.0
    return int(status), payload if isinstance(payload, dict) else {}, round(latency, 2)


def _login(intent_url: str, db_name: str, login: str, password: str) -> tuple[bool, str]:
    st, body, _ = _intent(intent_url, None, "login", {"db": db_name, "login": login, "password": password}, True)
    if st >= 400 or body.get("ok") is not True:
        return False, ""
    token = _norm(((body.get("data") or {}).get("token")))
    return bool(token), token


def _trace(role_key: str, scene_key: str, status: int, reason: str, mode: str) -> str:
    seed = f"{role_key}|{scene_key}|{status}|{reason}|{mode}"
    return hashlib.sha256(seed.encode("utf-8")).hexdigest()[:16]


def main() -> int:
    errors: list[str] = []
    warnings: list[str] = []

    role_src = _load(ROLE_SOURCE_JSON)
    role_floor = _load(ROLE_FLOOR_JSON)
    scene_map = _load(SCENE_MAP_JSON)
    roles = role_src.get("roles") if isinstance(role_src.get("roles"), list) else []
    floor_rows = role_floor.get("roles") if isinstance(role_floor.get("roles"), list) else []
    floor_by_login = {_norm(r.get("login")): r for r in floor_rows if isinstance(r, dict) and _norm(r.get("login"))}
    scene_rows = scene_map.get("scene_to_domain") if isinstance(scene_map.get("scene_to_domain"), list) else []
    valid_scenes = {
        _norm(r.get("canonical_scene"))
        for r in scene_rows
        if isinstance(r, dict) and _norm(r.get("canonical_scene"))
    }

    db_name = _norm(os.getenv("DB_NAME") or os.getenv("ODOO_DB") or "sc_dev")
    probe_password = _norm(os.getenv("ROLE_PROBE_PASSWORD") or os.getenv("E2E_PASSWORD") or "prod_like")
    live_probe_enabled = _norm(os.getenv("ROLE_HOME_LIVE_PROBE") or "0") == "1"

    base_url = get_base_url()
    intent_url = f"{base_url}/api/v1/intent"

    rows = []
    live_probe_ok = 0
    for role in roles:
        if not isinstance(role, dict):
            continue
        role_key = _norm(role.get("role_key"))
        role_name = _norm(role.get("role_name"))
        scene_key = _norm(role.get("default_scene"))
        login = _norm(role.get("probe_login"))
        if not role_key or not scene_key:
            errors.append(f"invalid_role_record={role_key or role_name or 'unknown'}")
            continue

        entry = {
            "role_key": role_key,
            "role_name": role_name,
            "default_scene": scene_key,
            "probe_login": login,
            "status": 0,
            "openable": False,
            "reason": "",
            "trace_id": "",
            "latency_ms": 0.0,
            "evidence_mode": "",
        }

        live_done = False
        if live_probe_enabled and login:
            try:
                ok, token = _login(intent_url, db_name, login, probe_password)
                if ok and token:
                    st, body, latency = _intent(
                        intent_url,
                        token,
                        "ui.contract",
                        {"op": "model", "model": "project.project", "view_type": "form"},
                    )
                    entry["status"] = st
                    entry["openable"] = (200 <= st < 300) and bool(body.get("ok"))
                    entry["reason"] = "ok" if entry["openable"] else _norm(body.get("error", {}).get("code") if isinstance(body.get("error"), dict) else "ui.contract_not_ok")
                    entry["latency_ms"] = latency
                    entry["evidence_mode"] = "live_probe"
                    entry["trace_id"] = _trace(role_key, scene_key, st, entry["reason"], "live_probe")
                    live_done = True
                    live_probe_ok += 1
                else:
                    warnings.append(f"login_failed_for_live_probe={role_key}:{login}")
            except Exception:
                warnings.append(f"live_probe_unavailable={role_key}:{login}")

        if not live_done:
            floor = floor_by_login.get(login, {}) if login else {}
            journey = floor.get("journey") if isinstance(floor.get("journey"), list) else []
            ui_step = None
            for step in journey:
                if isinstance(step, dict) and _norm(step.get("intent")) == "ui.contract":
                    ui_step = step
                    break
            ok = bool(ui_step.get("ok")) if isinstance(ui_step, dict) else False
            reason = _norm(ui_step.get("reason")) if isinstance(ui_step, dict) else "no_floor_evidence"
            scene_valid = scene_key in valid_scenes
            entry["status"] = 200 if (ok and scene_valid) else 403
            entry["openable"] = bool(ok and scene_valid)
            entry["reason"] = reason or ("ok" if ok else "blocked")
            if ok and not scene_valid:
                entry["reason"] = "scene_not_in_runtime_mapping"
            entry["latency_ms"] = 0.0
            entry["evidence_mode"] = "artifact_reuse"
            entry["trace_id"] = _trace(role_key, scene_key, entry["status"], entry["reason"], "artifact_reuse")

        if not entry["openable"] and role_key in {"pm", "finance", "purchase_manager", "executive", "ops"}:
            errors.append(f"default_home_not_openable={role_key}:{scene_key}")

        rows.append(entry)

    payload = {
        "ok": len(errors) == 0,
        "summary": {
            "role_count": len(rows),
            "openable_count": sum(1 for r in rows if r["openable"]),
            "live_probe_count": live_probe_ok,
            "error_count": len(errors),
            "warning_count": len(warnings),
        },
        "rows": rows,
        "errors": errors,
        "warnings": warnings,
    }

    REPORT_JSON.parent.mkdir(parents=True, exist_ok=True)
    REPORT_JSON.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    lines = [
        "# Role Home Openability Report",
        "",
        f"- role_count: {payload['summary']['role_count']}",
        f"- openable_count: {payload['summary']['openable_count']}",
        f"- live_probe_count: {payload['summary']['live_probe_count']}",
        f"- error_count: {payload['summary']['error_count']}",
        f"- warning_count: {payload['summary']['warning_count']}",
        "",
        "| role | default_scene | status | openable | trace_id | evidence_mode |",
        "|---|---|---:|---|---|---|",
    ]
    for row in rows:
        lines.append(
            f"| {row['role_name']} ({row['role_key']}) | {row['default_scene']} | {row['status']} | "
            f"{'PASS' if row['openable'] else 'FAIL'} | {row['trace_id']} | {row['evidence_mode']} |"
        )
    REPORT_MD.parent.mkdir(parents=True, exist_ok=True)
    REPORT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")

    print(str(REPORT_MD))
    print(str(REPORT_JSON))
    if errors:
        print("[role_home_openability_report] FAIL")
        return 2
    print("[role_home_openability_report] PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
