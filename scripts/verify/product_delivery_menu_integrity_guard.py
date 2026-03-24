#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

from python_http_smoke_utils import get_base_url, http_post_json


ROOT = Path(__file__).resolve().parents[2]
OUT_JSON = ROOT / "artifacts" / "backend" / "product_delivery_menu_integrity_guard.json"
OUT_MD = ROOT / "artifacts" / "backend" / "product_delivery_menu_integrity_guard.md"
EXPECTED_MENU_KEYS = [
    "release.fr1.project_intake",
    "release.fr2.project_flow",
    "release.fr3.cost_tracking",
    "release.fr4.payment_tracking",
    "release.fr5.settlement_summary",
    "release.my_work",
]


def _write(path: Path, payload: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(payload, encoding="utf-8")


def _write_json(path: Path, payload: dict) -> None:
    _write(path, json.dumps(payload, ensure_ascii=False, indent=2) + "\n")


def _post(intent_url: str, token: str | None, intent: str, params: dict | None = None, *, db_name: str = ""):
    headers = {"X-Anonymous-Intent": "1"} if token is None else {"Authorization": f"Bearer {token}"}
    if db_name:
        headers["X-Odoo-DB"] = db_name
    status, payload = http_post_json(intent_url, {"intent": intent, "params": params or {}}, headers=headers)
    return status, payload if isinstance(payload, dict) else {}


def _assert_ok(status: int, payload: dict, label: str) -> None:
    if status >= 400 or payload.get("ok") is not True:
        raise RuntimeError(f"{label} failed: status={status} payload={payload}")


def _extract_token(login_payload: dict) -> str:
    data = login_payload.get("data") if isinstance(login_payload.get("data"), dict) else {}
    token = str(data.get("token") or "").strip()
    if token:
        return token
    session = data.get("session") if isinstance(data.get("session"), dict) else {}
    return str(session.get("token") or "").strip()


def _flatten_leaf_rows(contract: dict) -> list[dict]:
    out: list[dict] = []
    for root in contract.get("nav") or []:
        if not isinstance(root, dict):
            continue
        for group in root.get("children") or []:
            if not isinstance(group, dict):
                continue
            for leaf in group.get("children") or []:
                if isinstance(leaf, dict):
                    out.append(leaf)
    return out


def main() -> int:
    base_url = get_base_url()
    db_name = str(os.getenv("E2E_DB") or os.getenv("DB_NAME") or "").strip()
    login = str(os.getenv("E2E_LOGIN") or "demo_pm").strip()
    password = str(os.getenv("E2E_PASSWORD") or "demo").strip()
    intent_url = f"{base_url}/api/v1/intent"
    if db_name:
        intent_url = f"{intent_url}?db={db_name}"

    report: dict = {"status": "PASS", "db_name": db_name, "login": login}
    try:
        status, login_resp = _post(intent_url, None, "login", {"db": db_name, "login": login, "password": password}, db_name=db_name)
        _assert_ok(status, login_resp, "login")
        token = _extract_token(login_resp)
        if not token:
            raise RuntimeError("login token missing")

        status, init_resp = _post(intent_url, token, "system.init", {"scene": "web", "with_preload": False, "root_xmlid": "smart_construction_core.menu_sc_root"}, db_name=db_name)
        _assert_ok(status, init_resp, "system.init")
        data = init_resp.get("data") if isinstance(init_resp.get("data"), dict) else {}
        contract = data.get("delivery_engine_v1") if isinstance(data.get("delivery_engine_v1"), dict) else {}
        if not contract:
            raise RuntimeError("delivery_engine_v1 missing")

        rows = _flatten_leaf_rows(contract)
        menu_keys = [str((row.get("meta") or {}).get("menu_key") or row.get("key") or "").strip() for row in rows]
        routes = [str((row.get("meta") or {}).get("route") or "").strip() for row in rows]
        if menu_keys != EXPECTED_MENU_KEYS:
            raise RuntimeError(f"menu keys drift: {menu_keys}")
        if any(not route for route in routes):
            raise RuntimeError(f"empty route found: {routes}")
        report["menu_keys"] = menu_keys
        report["routes"] = routes
    except Exception as exc:
        report["status"] = "FAIL"
        report["error"] = str(exc)
        _write_json(OUT_JSON, report)
        _write(OUT_MD, f"# Delivery Menu Integrity Guard\n\n- status: `FAIL`\n- error: `{exc}`\n")
        print("[product_delivery_menu_integrity_guard] FAIL")
        print(f" - {exc}")
        return 1

    _write_json(OUT_JSON, report)
    _write(OUT_MD, "# Delivery Menu Integrity Guard\n\n- status: `PASS`\n")
    print("[product_delivery_menu_integrity_guard] PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())

