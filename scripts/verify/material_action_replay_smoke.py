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
REPORT_JSON = ROOT / "artifacts" / "backend" / "material_action_replay_smoke.json"
SEED_REPORT_PATH = ROOT / "artifacts" / "backend" / "material_action_replay_seed.json"

DB_NAME = os.getenv("DB_NAME") or os.getenv("E2E_DB") or "sc_demo"
LOGIN = os.getenv("ROLE_MATERIAL_LOGIN") or os.getenv("E2E_LOGIN") or "demo_business_full"
PASSWORD = os.getenv("ROLE_MATERIAL_PASSWORD") or os.getenv("E2E_PASSWORD") or "demo"

SCENES = [
    {
        "scene_key": "material.center",
        "label": "物资与分包中心",
        "menu_xmlid": "smart_construction_core.menu_sc_material_center",
        "model": "",
        "entry_only": True,
    },
    {
        "scene_key": "material.procurement",
        "label": "采购申请",
        "menu_xmlid": "smart_construction_core.menu_sc_material_purchase_request",
        "action_xmlid": "smart_construction_core.action_sc_material_purchase_request",
        "model": "sc.material.purchase.request",
    },
    {
        "scene_key": "material.inbound",
        "label": "入库单",
        "menu_xmlid": "smart_construction_core.menu_sc_material_inbound",
        "action_xmlid": "smart_construction_core.action_sc_material_inbound",
        "model": "sc.material.inbound",
    },
    {
        "scene_key": "labor.request",
        "label": "劳务申请",
        "menu_xmlid": "smart_construction_core.menu_sc_labor_request",
        "action_xmlid": "smart_construction_core.action_sc_labor_request",
        "model": "sc.labor.request",
    },
    {
        "scene_key": "equipment.request",
        "label": "设备申请",
        "menu_xmlid": "smart_construction_core.menu_sc_equipment_request",
        "action_xmlid": "smart_construction_core.action_sc_equipment_request",
        "model": "sc.equipment.request",
    },
    {
        "scene_key": "subcontract.request",
        "label": "分包申请",
        "menu_xmlid": "smart_construction_core.menu_sc_subcontract_request",
        "action_xmlid": "smart_construction_core.action_sc_subcontract_request",
        "model": "sc.subcontract.request",
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


def _xmlid_parts(xmlid: str) -> tuple[str, str]:
    module, _, name = str(xmlid or "").partition(".")
    return module, name


def _resolve_xmlid(token: str, xmlid: str, expected_model: str) -> int:
    module, name = _xmlid_parts(xmlid)
    if not module or not name:
        return 0
    status, payload = _intent(
        "api.data",
        {
            "op": "list",
            "model": "ir.model.data",
            "fields": ["id", "res_id", "module", "name", "model"],
            "domain": [["module", "=", module], ["name", "=", name], ["model", "=", expected_model]],
            "limit": 1,
        },
        token,
    )
    rows = (((payload.get("data") or {}).get("records")) or []) if status < 400 and payload.get("ok") is True else []
    if not rows or not isinstance(rows[0], dict):
        return 0
    try:
        return int(rows[0].get("res_id") or 0)
    except Exception:
        return 0


def _records(payload: dict) -> list[dict]:
    data = payload.get("data") if isinstance(payload.get("data"), dict) else {}
    rows = data.get("records") if isinstance(data.get("records"), list) else []
    return [row for row in rows if isinstance(row, dict)]


def _total(payload: dict) -> int:
    data = payload.get("data") if isinstance(payload.get("data"), dict) else {}
    try:
        return int(data.get("total") or 0)
    except Exception:
        return 0


def _name_of(row: dict[str, Any]) -> str:
    for key in ("display_name", "name", "code"):
        value = row.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
    return str(row.get("id") or "").strip()


def _contract_model(payload: dict) -> str:
    data = payload.get("data") if isinstance(payload.get("data"), dict) else {}
    action = data.get("action") if isinstance(data.get("action"), dict) else {}
    entry = data.get("entry") if isinstance(data.get("entry"), dict) else {}
    return str(action.get("res_model") or entry.get("model") or data.get("model") or "").strip()


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


def _replay_scene(token: str, spec: dict) -> dict:
    scene_key = str(spec.get("scene_key") or "")
    expected_model = str(spec.get("model") or "")
    steps: list[dict] = []
    errors: list[str] = []

    seed_row = spec.get("seed_row") if isinstance(spec.get("seed_row"), dict) else {}
    menu_id = int(seed_row.get("menu_id") or 0) if seed_row else 0
    if menu_id <= 0:
        menu_id = _resolve_xmlid(token, str(spec.get("menu_xmlid") or ""), "ir.ui.menu")
    steps.append({"step": "resolve_menu", "ok": menu_id > 0, "menu_id": menu_id})
    if menu_id <= 0:
        errors.append("menu_xmlid_unresolved")

    action_id = 0
    if spec.get("action_xmlid"):
        action_id = int(seed_row.get("action_id") or 0) if seed_row else 0
        if action_id <= 0:
            action_id = _resolve_xmlid(token, str(spec.get("action_xmlid") or ""), "ir.actions.act_window")
        steps.append({"step": "resolve_action", "ok": action_id > 0, "action_id": action_id})
        if action_id <= 0:
            errors.append("action_xmlid_unresolved")

    if menu_id > 0:
        status, payload = _intent(
            "ui.contract",
            {
                "op": "menu",
                "menu_id": menu_id,
                "source_mode": "backend_internal",
                "contract_surface": "native",
                "scene_key": scene_key,
            },
            token,
        )
        contract_ok = status < 400 and payload.get("ok") is True
        model = _contract_model(payload)
        step = {"step": "ui.contract.menu", "ok": contract_ok, "status": status, "model": model}
        steps.append(step)
        if not contract_ok:
            errors.append("menu_contract_failed")
        if expected_model and model and model != expected_model:
            errors.append(f"menu_model_mismatch:{model}")

    if action_id > 0:
        status, payload = _intent(
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
        contract_ok = status < 400 and payload.get("ok") is True
        model = _contract_model(payload)
        steps.append({"step": "ui.contract.action_open", "ok": contract_ok, "status": status, "model": model})
        if not contract_ok:
            errors.append("action_contract_failed")
        if expected_model and model and model != expected_model:
            errors.append(f"action_model_mismatch:{model}")

    if spec.get("entry_only"):
        return {
            "scene_key": scene_key,
            "label": spec.get("label"),
            "model": expected_model,
            "ok": not errors,
            "record_id": 0,
            "total": 0,
            "steps": steps,
            "errors": errors,
        }

    seed_record_id = int(seed_row.get("record_id") or 0) if seed_row else 0
    domain = [["id", "=", seed_record_id]] if seed_record_id > 0 else []
    status, list_payload = _intent(
        "api.data",
        {
            "op": "list",
            "model": expected_model,
            "fields": ["id", "display_name"],
            "domain": domain,
            "limit": 5,
            "order": "write_date desc,id desc",
        },
        token,
    )
    rows = _records(list_payload)
    total = _total(list_payload)
    record_id = int(rows[0].get("id") or 0) if rows else 0
    steps.append({"step": "api.data.list", "ok": status < 400 and list_payload.get("ok") is True and record_id > 0, "status": status, "total": total, "record_id": record_id})
    if record_id <= 0:
        errors.append("list_empty")

    search_term = _name_of(rows[0]) if rows else ""
    if search_term:
        status, search_payload = _intent(
            "api.data",
            {
                "op": "list",
                "model": expected_model,
                "fields": ["id", "display_name"],
                "search_term": search_term,
                "limit": 5,
                "order": "write_date desc,id desc",
            },
            token,
        )
        search_rows = _records(search_payload)
        search_ids = {int(row.get("id") or 0) for row in search_rows}
        steps.append({"step": "api.data.search", "ok": status < 400 and search_payload.get("ok") is True and record_id in search_ids, "status": status, "search_term": search_term, "matched_count": len(search_rows)})
        if record_id not in search_ids:
            errors.append("search_replay_missed_record")

    if record_id > 0:
        status, read_payload = _intent(
            "api.data",
            {"op": "read", "model": expected_model, "ids": [record_id], "fields": ["id", "display_name"]},
            token,
        )
        read_rows = _records(read_payload)
        steps.append({"step": "api.data.read", "ok": status < 400 and read_payload.get("ok") is True and bool(read_rows), "status": status, "record_id": record_id})
        if not read_rows:
            errors.append("read_failed")

    return {
        "scene_key": scene_key,
        "label": spec.get("label"),
        "model": expected_model,
        "ok": not errors,
        "record_id": record_id,
        "total": total,
        "steps": steps,
        "errors": errors,
    }


def main() -> int:
    token = _login()
    seed = _load_seed()
    seed_by_scene = _seed_rows(seed)
    scene_specs = []
    for spec in SCENES:
        item = dict(spec)
        item["seed_row"] = seed_by_scene.get(str(spec.get("scene_key") or ""), {})
        scene_specs.append(item)
    checks = [_replay_scene(token, spec) for spec in scene_specs]
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
            "scene_count": len(checks),
            "pass_count": len(checks) - len(failures),
            "failed_count": len(failures),
        },
        "checks": checks,
    }
    REPORT_JSON.parent.mkdir(parents=True, exist_ok=True)
    REPORT_JSON.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(REPORT_JSON)
    if failures:
        print("[material_action_replay_smoke] FAIL")
        print(json.dumps(payload, ensure_ascii=False, indent=2))
        return 2
    print("[material_action_replay_smoke] PASS")
    print(json.dumps(payload["summary"], ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
