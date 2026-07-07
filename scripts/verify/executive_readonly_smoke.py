#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from python_http_smoke_utils import get_base_url, http_post_json


ROOT = Path(__file__).resolve().parents[2]
REPORT_JSON = ROOT / "artifacts" / "backend" / "executive_readonly_smoke.json"
SEED_REPORT_PATH = ROOT / "artifacts" / "backend" / "executive_readonly_seed.json"

DB_NAME = os.getenv("DB_NAME") or os.getenv("E2E_DB") or "sc_demo"
LOGIN = os.getenv("ROLE_EXECUTIVE_READONLY_LOGIN") or "executive_readonly_smoke"
PASSWORD = os.getenv("ROLE_EXECUTIVE_READONLY_PASSWORD") or os.getenv("E2E_PASSWORD") or "demo"

EXECUTIVE_SCENES = [
    "portal.dashboard",
    "finance.operating_metrics",
    "portal.capability_matrix",
]
OPTIONAL_EXECUTIVE_SCENES = [
    "projects.dashboard_focus",
]
FINANCE_MODEL = "sc.operating.metrics.project"
READ_FIELDS = [
    "id",
    "display_name",
    "project_id",
    "receipt_amount",
    "settlement_amount_total",
    "net_cash_amount",
]
WRITE_DENIAL_MARKER = "executive-readonly-smoke-denied"


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _intent_url() -> str:
    return f"{get_base_url().rstrip('/')}/api/v1/intent?db={DB_NAME}"


def _headers(token: str | None = None, *, anonymous: bool = False) -> dict[str, str]:
    headers = {"X-Odoo-DB": DB_NAME}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    if anonymous:
        headers["X-Anonymous-Intent"] = "1"
    return headers


def _intent(intent: str, params: dict | None = None, token: str | None = None, *, anonymous: bool = False) -> tuple[int, dict]:
    status, payload = http_post_json(
        _intent_url(),
        {"intent": intent, "params": params or {}},
        headers=_headers(token, anonymous=anonymous),
    )
    return status, payload if isinstance(payload, dict) else {}


def _login() -> str:
    status, payload = _intent(
        "login",
        {"db": DB_NAME, "login": LOGIN, "password": PASSWORD},
        anonymous=True,
    )
    data = payload.get("data") if isinstance(payload.get("data"), dict) else {}
    token = str(data.get("token") or "").strip()
    if status >= 400 or payload.get("ok") is not True or not token:
        raise AssertionError(f"login failed status={status} error={payload.get('error')}")
    return token


def _load_seed() -> dict:
    if not SEED_REPORT_PATH.exists():
        return {}
    try:
        payload = json.loads(SEED_REPORT_PATH.read_text(encoding="utf-8"))
    except Exception:
        return {}
    return payload if isinstance(payload, dict) else {}


def _seed_action_id(seed: dict, scene_key: str) -> int:
    rows = seed.get("actions") if isinstance(seed.get("actions"), list) else []
    for row in rows:
        if isinstance(row, dict) and row.get("scene_key") == scene_key:
            try:
                return int(row.get("action_id") or 0)
            except Exception:
                return 0
    return 0


def _records(payload: dict) -> list[dict]:
    data = payload.get("data") if isinstance(payload.get("data"), dict) else {}
    rows = data.get("records") if isinstance(data.get("records"), list) else []
    return [row for row in rows if isinstance(row, dict)]


def _contract_model(payload: dict) -> str:
    data = payload.get("data") if isinstance(payload.get("data"), dict) else {}
    action = data.get("action") if isinstance(data.get("action"), dict) else {}
    entry = data.get("entry") if isinstance(data.get("entry"), dict) else {}
    return str(action.get("res_model") or entry.get("model") or data.get("model") or "").strip()


def _walk(value: Any):
    yield value
    if isinstance(value, dict):
        for child in value.values():
            yield from _walk(child)
    elif isinstance(value, list):
        for child in value:
            yield from _walk(child)


def _scene_values(payload: dict) -> set[str]:
    values: set[str] = set()
    scene_keys = {"scene_key", "sceneKey", "scene", "code", "key"}
    for item in _walk(payload):
        if isinstance(item, dict):
            for key, value in item.items():
                if key in scene_keys and isinstance(value, str) and "." in value:
                    values.add(value.strip())
    return values


def _assert_denied(status: int, payload: dict) -> tuple[bool, str]:
    if status >= 400:
        return True, f"http_{status}"
    if payload.get("ok") is not True:
        error = payload.get("error")
        if isinstance(error, dict):
            return True, str(error.get("code") or error.get("message") or "intent_denied")
        return True, str(error or "intent_denied")
    return False, "unexpected_success"


def _startup_scene_check(token: str, seed: dict) -> dict:
    status, payload = _intent("system.init", {"scene_key": "portal.dashboard", "with_preload": False}, token)
    scenes = _scene_values(payload)
    missing = [scene for scene in EXECUTIVE_SCENES if scene not in scenes]
    optional_available = [scene for scene in OPTIONAL_EXECUTIVE_SCENES if _seed_action_id(seed, scene) > 0]
    optional_unavailable = [scene for scene in OPTIONAL_EXECUTIVE_SCENES if _seed_action_id(seed, scene) <= 0]
    optional_missing = [scene for scene in optional_available if scene not in scenes]
    ok = status < 400 and payload.get("ok") is True and not missing
    return {
        "step": "system.init.executive_scenes",
        "ok": ok,
        "status": status,
        "required_scenes": EXECUTIVE_SCENES,
        "optional_scenes": OPTIONAL_EXECUTIVE_SCENES,
        "found_scenes": sorted(scene for scene in scenes if scene in set(EXECUTIVE_SCENES)),
        "optional_found_scenes": sorted(scene for scene in scenes if scene in set(OPTIONAL_EXECUTIVE_SCENES)),
        "missing_scenes": missing,
        "optional_missing_scenes": optional_missing,
        "optional_unavailable_scenes": optional_unavailable,
    }


def _finance_readonly_check(token: str, action_id: int) -> dict:
    steps: list[dict] = []
    errors: list[str] = []
    if action_id <= 0:
        return {"step": "finance.operating_metrics.readonly", "ok": False, "errors": ["action_id_missing"], "steps": steps}

    status, contract_payload = _intent(
        "ui.contract",
        {
            "op": "action_open",
            "action_id": action_id,
            "source_mode": "backend_internal",
            "contract_surface": "native",
            "scene_key": "finance.operating_metrics",
        },
        token,
    )
    contract_ok = status < 400 and contract_payload.get("ok") is True
    model = _contract_model(contract_payload)
    steps.append({"step": "ui.contract.action_open", "ok": contract_ok, "status": status, "model": model})
    if not contract_ok:
        errors.append("action_contract_failed")
    if model and model != FINANCE_MODEL:
        errors.append(f"action_model_mismatch:{model}")

    status, list_payload = _intent(
        "api.data",
        {
            "op": "list",
            "model": FINANCE_MODEL,
            "fields": READ_FIELDS,
            "domain": [],
            "limit": 5,
            "order": "id desc",
        },
        token,
    )
    rows = _records(list_payload)
    record_id = int(rows[0].get("id") or 0) if rows else 0
    steps.append({"step": "api.data.list", "ok": status < 400 and list_payload.get("ok") is True and record_id > 0, "status": status, "record_id": record_id, "count": len(rows)})
    if record_id <= 0:
        errors.append("operating_metrics_list_empty")

    if record_id > 0:
        status, read_payload = _intent(
            "api.data",
            {"op": "read", "model": FINANCE_MODEL, "ids": [record_id], "fields": READ_FIELDS},
            token,
        )
        read_rows = _records(read_payload)
        steps.append({"step": "api.data.read", "ok": status < 400 and read_payload.get("ok") is True and bool(read_rows), "status": status, "record_id": record_id})
        if not read_rows:
            errors.append("operating_metrics_read_failed")

        status, write_payload = _intent(
            "api.data",
            {"op": "write", "model": FINANCE_MODEL, "ids": [record_id], "vals": {"display_name": WRITE_DENIAL_MARKER}},
            token,
        )
        denied, reason = _assert_denied(status, write_payload)
        steps.append({"step": "api.data.write_denied", "ok": denied, "status": status, "reason": reason, "record_id": record_id})
        if not denied:
            errors.append("write_unexpectedly_allowed")

    status, create_payload = _intent(
        "api.data",
        {"op": "create", "model": FINANCE_MODEL, "vals": {"display_name": WRITE_DENIAL_MARKER}},
        token,
    )
    denied, reason = _assert_denied(status, create_payload)
    steps.append({"step": "api.data.create_denied", "ok": denied, "status": status, "reason": reason})
    if not denied:
        errors.append("create_unexpectedly_allowed")

    return {
        "step": "finance.operating_metrics.readonly",
        "ok": not errors,
        "model": FINANCE_MODEL,
        "record_id": record_id,
        "steps": steps,
        "errors": errors,
    }


def main() -> int:
    token = _login()
    seed = _load_seed()
    checks = [
        _startup_scene_check(token, seed),
        _finance_readonly_check(token, _seed_action_id(seed, "finance.operating_metrics")),
    ]
    failures = [row for row in checks if not row.get("ok")]
    payload = {
        "generated_at_utc": _utc_now(),
        "ok": not failures,
        "db": DB_NAME,
        "base_url": get_base_url().rstrip("/"),
        "login": LOGIN,
        "seed_present": bool(seed),
        "seed_ok": bool(seed.get("ok")) if seed else False,
        "summary": {
            "check_count": len(checks),
            "pass_count": len(checks) - len(failures),
            "failed_count": len(failures),
        },
        "checks": checks,
    }
    REPORT_JSON.parent.mkdir(parents=True, exist_ok=True)
    REPORT_JSON.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(REPORT_JSON)
    if failures:
        print("[executive_readonly_smoke] FAIL")
        print(json.dumps(payload, ensure_ascii=False, indent=2))
        return 2
    print("[executive_readonly_smoke] PASS")
    print(json.dumps(payload["summary"], ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
