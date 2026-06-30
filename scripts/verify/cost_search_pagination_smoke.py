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
REPORT_JSON = ROOT / "artifacts" / "backend" / "cost_search_pagination_smoke.json"
SEED_REPORT_PATH = ROOT / "artifacts" / "backend" / "cost_search_pagination_seed.json"

DB_NAME = os.getenv("DB_NAME") or os.getenv("E2E_DB") or "sc_demo"
LOGIN = os.getenv("ROLE_COST_READONLY_LOGIN") or "cost_readonly_smoke"
PASSWORD = os.getenv("ROLE_COST_READONLY_PASSWORD") or os.getenv("E2E_PASSWORD") or "demo"

SCENES = [
    {
        "scene_key": "cost.project_budget",
        "model": "project.budget",
        "fields": ["id", "display_name", "name", "project_id", "company_id", "write_date"],
        "search_anchor": "name",
    },
    {
        "scene_key": "cost.project_cost_ledger",
        "model": "project.cost.ledger",
        "fields": ["id", "display_name", "project_id", "cost_code_id", "amount", "date", "company_id", "write_date"],
        "search_anchor": "cost_code_id",
    },
    {
        "scene_key": "cost.profit_compare",
        "model": "project.profit.compare",
        "fields": ["id", "display_name", "project_id"],
        "search_anchor": "project_id",
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


def _login() -> str:
    status, payload = _intent("login", {"db": DB_NAME, "login": LOGIN, "password": PASSWORD}, anonymous=True)
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


def _seed_rows(seed: dict) -> dict[str, dict]:
    rows = seed.get("checks") if isinstance(seed.get("checks"), list) else []
    return {str(row.get("scene_key") or ""): row for row in rows if isinstance(row, dict)}


def _records(payload: dict) -> list[dict]:
    data = payload.get("data") if isinstance(payload.get("data"), dict) else {}
    rows = data.get("records") if isinstance(data.get("records"), list) else []
    return [row for row in rows if isinstance(row, dict)]


def _count(payload: dict) -> int:
    data = payload.get("data") if isinstance(payload.get("data"), dict) else {}
    for key in ("total", "count"):
        try:
            return int(data.get(key) or 0)
        except Exception:
            pass
    return 0


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
        if isinstance(item, dict):
            for key in ("scene_key", "sceneKey", "scene", "code", "key"):
                value = item.get(key)
                if isinstance(value, str) and "." in value:
                    values.add(value.strip())
    return values


def _list_params(spec: dict, *, offset: int = 0, domain: list | None = None) -> dict:
    return {
        "op": "list",
        "model": spec["model"],
        "fields": spec["fields"],
        "domain": domain or [],
        "limit": 2,
        "offset": offset,
        "order": "id desc",
    }


def _anchor_domain(row: dict, anchor: str) -> list:
    value = row.get(anchor)
    if isinstance(value, list) and value:
        return [[anchor, "=", int(value[0] or 0)]]
    if isinstance(value, str) and value.strip():
        return [[anchor, "ilike", value.strip()]]
    return []


def _startup_check(token: str) -> dict:
    required = [spec["scene_key"] for spec in SCENES]
    status, payload = _intent("system.init", {"scene_key": "cost.project_budget", "with_preload": False}, token)
    scenes = _scene_values(payload)
    missing = [scene for scene in required if scene not in scenes]
    return {
        "step": "system.init.cost_scenes",
        "ok": status < 400 and payload.get("ok") is True and not missing,
        "status": status,
        "required_scenes": required,
        "found_scenes": sorted(scene for scene in scenes if scene in set(required)),
        "missing_scenes": missing,
    }


def _scene_check(token: str, spec: dict, seed_row: dict) -> dict:
    errors: list[str] = []
    steps: list[dict] = []
    action_id = int(seed_row.get("action_id") or 0)
    if action_id <= 0:
        errors.append("action_id_missing")
    else:
        status, contract_payload = _intent(
            "ui.contract",
            {
                "op": "action_open",
                "action_id": action_id,
                "source_mode": "backend_internal",
                "contract_surface": "native",
                "scene_key": spec["scene_key"],
            },
            token,
        )
        model = _contract_model(contract_payload)
        ok = status < 400 and contract_payload.get("ok") is True and model == spec["model"]
        steps.append({"step": "ui.contract.action_open", "ok": ok, "status": status, "model": model, "action_id": action_id})
        if not ok:
            errors.append("action_contract_failed")

    status, count_payload = _intent("api.data", {"op": "count", "model": spec["model"], "domain": []}, token)
    total = _count(count_payload)
    count_ok = status < 400 and count_payload.get("ok") is True and total > 0
    steps.append({"step": "api.data.count", "ok": count_ok, "status": status, "count": total})
    if not count_ok:
        errors.append("count_failed")

    status, page1_payload = _intent("api.data", _list_params(spec, offset=0), token)
    page1 = _records(page1_payload)
    page1_ids = [int(row.get("id") or 0) for row in page1]
    page1_ok = status < 400 and page1_payload.get("ok") is True and bool(page1_ids)
    steps.append({"step": "api.data.page_1", "ok": page1_ok, "status": status, "ids": page1_ids})
    if not page1_ok:
        errors.append("page_1_empty")

    status, page2_payload = _intent("api.data", _list_params(spec, offset=2), token)
    page2 = _records(page2_payload)
    page2_ids = [int(row.get("id") or 0) for row in page2]
    page2_ok = status < 400 and page2_payload.get("ok") is True and (total <= 2 or bool(page2_ids)) and not set(page1_ids).intersection(page2_ids)
    steps.append({"step": "api.data.page_2", "ok": page2_ok, "status": status, "ids": page2_ids, "offset": 2})
    if not page2_ok:
        errors.append("page_2_invalid")

    domain = _anchor_domain(page1[0], str(spec.get("search_anchor") or "")) if page1 else []
    if domain:
        status, search_payload = _intent("api.data", _list_params(spec, offset=0, domain=domain), token)
        search_ids = [int(row.get("id") or 0) for row in _records(search_payload)]
        search_ok = status < 400 and search_payload.get("ok") is True and bool(set(page1_ids).intersection(search_ids))
        steps.append({"step": "api.data.search_domain", "ok": search_ok, "status": status, "domain": domain, "ids": search_ids})
        if not search_ok:
            errors.append("search_domain_missed_record")
    else:
        steps.append({"step": "api.data.search_domain", "ok": True, "skipped": "missing_anchor"})

    return {
        "scene_key": spec["scene_key"],
        "model": spec["model"],
        "ok": not errors,
        "record_count": total,
        "page_1_ids": page1_ids,
        "page_2_ids": page2_ids,
        "steps": steps,
        "errors": errors,
    }


def main() -> int:
    token = _login()
    seed = _load_seed()
    seed_by_scene = _seed_rows(seed)
    checks = [_startup_check(token)]
    checks.extend(_scene_check(token, spec, seed_by_scene.get(spec["scene_key"], {})) for spec in SCENES)
    failures = [row for row in checks if not row.get("ok")]
    payload = {
        "generated_at_utc": _utc_now(),
        "ok": not failures,
        "db": DB_NAME,
        "base_url": get_base_url().rstrip("/"),
        "login": LOGIN,
        "seed_present": bool(seed),
        "seed_ok": bool(seed.get("ok")) if seed else False,
        "summary": {"check_count": len(checks), "pass_count": len(checks) - len(failures), "failed_count": len(failures)},
        "checks": checks,
    }
    REPORT_JSON.parent.mkdir(parents=True, exist_ok=True)
    REPORT_JSON.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(REPORT_JSON)
    if failures:
        print("[cost_search_pagination_smoke] FAIL")
        print(json.dumps(payload, ensure_ascii=False, indent=2))
        return 2
    print("[cost_search_pagination_smoke] PASS")
    print(json.dumps(payload["summary"], ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
