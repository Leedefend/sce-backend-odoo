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
REPORT_JSON = ROOT / "artifacts" / "backend" / "ledger_snapshot_smoke.json"
SEED_REPORT_PATH = ROOT / "artifacts" / "backend" / "ledger_snapshot_seed.json"

DB_NAME = os.getenv("DB_NAME") or os.getenv("E2E_DB") or "sc_demo"
LOGIN = os.getenv("ROLE_LEDGER_READONLY_LOGIN") or "ledger_readonly_smoke"
PASSWORD = os.getenv("ROLE_LEDGER_READONLY_PASSWORD") or os.getenv("E2E_PASSWORD") or "demo"

SCENES = [
    {
        "scene_key": "finance.payment_ledger",
        "model": "payment.ledger",
        "fields": ["id", "display_name", "ref", "project_id", "partner_id", "amount", "write_date"],
        "search_fields": ["ref"],
    },
    {
        "scene_key": "finance.treasury_ledger",
        "model": "sc.treasury.ledger",
        "fields": ["id", "display_name", "name", "project_id", "partner_id", "amount", "state", "date", "write_date"],
        "search_fields": ["name"],
    },
    {
        "scene_key": "finance.settlement_orders",
        "model": "sc.settlement.order",
        "fields": ["id", "display_name", "name", "project_id", "partner_id", "amount_total", "settlement_amount", "state", "company_id", "write_date"],
        "search_fields": ["name"],
    },
]


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


def _login() -> tuple[str, int]:
    status, payload = _intent(
        "login",
        {"db": DB_NAME, "login": LOGIN, "password": PASSWORD},
        anonymous=True,
    )
    data = payload.get("data") if isinstance(payload.get("data"), dict) else {}
    token = str(data.get("token") or "").strip()
    user = data.get("user") if isinstance(data.get("user"), dict) else {}
    try:
        company_id = int(user.get("company_id") or 0)
    except Exception:
        company_id = 0
    if status >= 400 or payload.get("ok") is not True or not token:
        raise AssertionError(f"login failed status={status} error={payload.get('error')}")
    return token, company_id


def _load_seed() -> dict:
    if not SEED_REPORT_PATH.exists():
        return {}
    try:
        payload = json.loads(SEED_REPORT_PATH.read_text(encoding="utf-8"))
    except Exception:
        return {}
    return payload if isinstance(payload, dict) else {}


def _seed_rows(seed: dict) -> dict[str, dict]:
    rows = seed.get("checks") if isinstance(seed.get("checks"), list) else []
    return {str(row.get("scene_key") or ""): row for row in rows if isinstance(row, dict)}


def _records(payload: dict) -> list[dict]:
    data = payload.get("data") if isinstance(payload.get("data"), dict) else {}
    rows = data.get("records") if isinstance(data.get("records"), list) else []
    return [row for row in rows if isinstance(row, dict)]


def _total(payload: dict) -> int:
    data = payload.get("data") if isinstance(payload.get("data"), dict) else {}
    for key in ("total", "count"):
        try:
            return int(data.get(key) or 0)
        except Exception:
            pass
    return 0


def _count_params(spec: dict, *, context: dict | None = None) -> dict:
    params = {
        "op": "count",
        "model": spec["model"],
        "domain": [],
    }
    if context:
        params["context"] = context
    return params


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
    for item in _walk(payload):
        if not isinstance(item, dict):
            continue
        for key in ("scene_key", "sceneKey", "scene", "code", "key"):
            value = item.get(key)
            if isinstance(value, str) and "." in value:
                values.add(value.strip())
    return values


def _first_search_anchor(row: dict, search_fields: list[str]) -> tuple[str, str]:
    for field in search_fields:
        value = row.get(field)
        if isinstance(value, str) and value.strip():
            return field, value.strip()
        if isinstance(value, list) and len(value) >= 2 and isinstance(value[1], str) and value[1].strip():
            return field, value[1].strip()
    return "", ""


def _api_params(spec: dict, *, context: dict | None = None, search_term: str = "") -> dict:
    params = {
        "op": "list",
        "model": spec["model"],
        "fields": spec["fields"],
        "domain": [],
        "limit": 5,
        "order": "id desc",
    }
    if context:
        params["context"] = context
    if search_term:
        params["search_term"] = search_term
    return params


def _scene_startup_check(token: str) -> dict:
    required = [spec["scene_key"] for spec in SCENES]
    status, payload = _intent("system.init", {"scene_key": "finance.payment_ledger", "with_preload": False}, token)
    scenes = _scene_values(payload)
    missing = [scene for scene in required if scene not in scenes]
    return {
        "step": "system.init.ledger_scenes",
        "ok": status < 400 and payload.get("ok") is True and not missing,
        "status": status,
        "required_scenes": required,
        "found_scenes": sorted(scene for scene in scenes if scene in set(required)),
        "missing_scenes": missing,
    }


def _ledger_scene_check(token: str, spec: dict, seed_row: dict, company_id: int) -> dict:
    scene_key = spec["scene_key"]
    model = spec["model"]
    action_id = int(seed_row.get("action_id") or 0)
    menu_id = int(seed_row.get("menu_id") or 0)
    context = {"allowed_company_ids": [company_id], "company_id": company_id} if company_id > 0 else {}
    steps: list[dict] = []
    errors: list[str] = []

    if action_id <= 0:
        errors.append("action_id_missing")
    if menu_id <= 0:
        errors.append("menu_id_missing")

    if action_id > 0:
        status, contract_payload = _intent(
            "ui.contract",
            {
                "op": "action_open",
                "action_id": action_id,
                "source_mode": "backend_internal",
                "contract_surface": "native",
                "scene_key": scene_key,
            },
            token,
        )
        contract_ok = status < 400 and contract_payload.get("ok") is True
        contract_model = _contract_model(contract_payload)
        steps.append({"step": "ui.contract.action_open", "ok": contract_ok, "status": status, "model": contract_model, "action_id": action_id})
        if not contract_ok:
            errors.append("action_contract_failed")
        if contract_model and contract_model != model:
            errors.append(f"action_model_mismatch:{contract_model}")

    status, first_payload = _intent("api.data", _api_params(spec), token)
    first_rows = _records(first_payload)
    first_ids = [int(row.get("id") or 0) for row in first_rows]
    first_total = _total(first_payload)
    steps.append({"step": "api.data.list", "ok": status < 400 and first_payload.get("ok") is True and bool(first_ids), "status": status, "total": first_total, "ids": first_ids})
    if not first_ids:
        errors.append("list_empty")

    status, count_payload = _intent("api.data", _count_params(spec), token)
    count_total = _total(count_payload)
    count_ok = status < 400 and count_payload.get("ok") is True and count_total >= len(first_ids)
    steps.append({"step": "api.data.count", "ok": count_ok, "status": status, "count": count_total})
    if not count_ok:
        errors.append("count_failed")

    status, repeat_payload = _intent("api.data", _api_params(spec), token)
    repeat_rows = _records(repeat_payload)
    repeat_ids = [int(row.get("id") or 0) for row in repeat_rows]
    repeat_total = _total(repeat_payload)
    repeat_ok = status < 400 and repeat_payload.get("ok") is True and repeat_ids == first_ids and repeat_total == first_total
    steps.append({"step": "api.data.list_repeat", "ok": repeat_ok, "status": status, "total": repeat_total, "ids": repeat_ids})
    if not repeat_ok:
        errors.append("list_repeat_mismatch")

    if context:
        status, scoped_payload = _intent("api.data", _api_params(spec, context=context), token)
        scoped_rows = _records(scoped_payload)
        scoped_ids = [int(row.get("id") or 0) for row in scoped_rows]
        scoped_total = _total(scoped_payload)
        scoped_ok = status < 400 and scoped_payload.get("ok") is True and bool(scoped_ids)
        steps.append({"step": "api.data.company_scope_list", "ok": scoped_ok, "status": status, "total": scoped_total, "ids": scoped_ids, "context": context})
        if not scoped_ok:
            errors.append("company_scope_list_empty")

        status, scoped_count_payload = _intent("api.data", _count_params(spec, context=context), token)
        scoped_count = _total(scoped_count_payload)
        scoped_count_ok = status < 400 and scoped_count_payload.get("ok") is True and scoped_count >= len(scoped_ids)
        steps.append({"step": "api.data.company_scope_count", "ok": scoped_count_ok, "status": status, "count": scoped_count, "context": context})
        if not scoped_count_ok:
            errors.append("company_scope_count_failed")

    search_field, search_term = _first_search_anchor(first_rows[0], spec["search_fields"]) if first_rows else ("", "")
    if search_term:
        search_params = _api_params(spec)
        search_params["domain"] = [[search_field, "ilike", search_term]]
        status, search_payload = _intent("api.data", search_params, token)
        search_rows = _records(search_payload)
        search_ids = {int(row.get("id") or 0) for row in search_rows}
        search_ok = status < 400 and search_payload.get("ok") is True and bool(search_ids.intersection(first_ids))
        steps.append(
            {
                "step": "api.data.search_domain",
                "ok": search_ok,
                "status": status,
                "search_field": search_field,
                "search_term": search_term,
                "domain": search_params["domain"],
                "matched_ids": sorted(search_ids),
            }
        )
        if not search_ok:
            errors.append("search_missed_snapshot_record")
    else:
        steps.append({"step": "api.data.search_domain", "ok": True, "skipped": "empty_search_term"})

    return {
        "scene_key": scene_key,
        "model": model,
        "ok": not errors,
        "record_count": count_total,
        "snapshot_ids": first_ids,
        "domain_trace": {
            "domain": [],
            "order": "id desc",
            "limit": 5,
            "company_context": context,
        },
        "steps": steps,
        "errors": errors,
    }


def main() -> int:
    token, company_id = _login()
    seed = _load_seed()
    seed_by_scene = _seed_rows(seed)
    checks = [_scene_startup_check(token)]
    for spec in SCENES:
        checks.append(_ledger_scene_check(token, spec, seed_by_scene.get(spec["scene_key"], {}), company_id))
    failures = [row for row in checks if not row.get("ok")]
    payload = {
        "generated_at_utc": _utc_now(),
        "ok": not failures,
        "db": DB_NAME,
        "base_url": get_base_url().rstrip("/"),
        "login": LOGIN,
        "company_id": company_id,
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
        print("[ledger_snapshot_smoke] FAIL")
        print(json.dumps(payload, ensure_ascii=False, indent=2))
        return 2
    print("[ledger_snapshot_smoke] PASS")
    print(json.dumps(payload["summary"], ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
