#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
VERIFY_DIR = ROOT / "scripts" / "verify"
if str(VERIFY_DIR) not in sys.path:
    sys.path.insert(0, str(VERIFY_DIR))

from intent_smoke_utils import require_ok  # type: ignore
from python_http_smoke_utils import get_base_url, http_post_json  # type: ignore


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Audit live project form ui.contract completeness")
    parser.add_argument("--db", required=True, help="Database name")
    parser.add_argument("--login", required=True, help="Fixture login")
    parser.add_argument("--password", required=True, help="Fixture password")
    parser.add_argument(
        "--expect-field-modifiers",
        choices=["present", "missing"],
        default="missing",
        help="Expected live result for views.form.field_modifiers",
    )
    return parser.parse_args()


def login(intent_url: str, db: str, login_name: str, password: str) -> str:
    status, resp = http_post_json(
        intent_url,
        {"intent": "login", "params": {"db": db, "login": login_name, "password": password}},
        headers={"X-Anonymous-Intent": "1"},
    )
    require_ok(status, resp, f"login({login_name})")
    data = resp.get("data") if isinstance(resp.get("data"), dict) else {}
    session = data.get("session") if isinstance(data.get("session"), dict) else {}
    token = str(session.get("token") or data.get("token") or "").strip()
    if not token:
        raise RuntimeError(f"login({login_name}) missing token")
    return token


def fetch_contract(intent_url: str, token: str) -> tuple[dict, dict]:
    status, resp = http_post_json(
        intent_url,
        {
            "intent": "ui.contract",
            "params": {"op": "model", "model": "project.project", "view_type": "form", "contract_mode": "user"},
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    require_ok(status, resp, "ui.contract(project.project.form)")
    data = resp.get("data") if isinstance(resp.get("data"), dict) else {}
    meta = resp.get("meta") if isinstance(resp.get("meta"), dict) else {}
    return data, meta


def main() -> int:
    args = parse_args()
    base_url = get_base_url()
    intent_url = f"{base_url}/api/v1/intent?db={args.db}"

    token = login(intent_url, args.db, args.login, args.password)
    data, meta = fetch_contract(intent_url, token)

    views = data.get("views") if isinstance(data.get("views"), dict) else {}
    form = views.get("form") if isinstance(views.get("form"), dict) else {}
    field_modifiers = form.get("field_modifiers")
    present = bool(field_modifiers)
    expected_present = args.expect_field_modifiers == "present"

    payload = {
        "status": "PASS" if present == expected_present else "FAIL",
        "base_url": base_url,
        "intent_url": intent_url,
        "trace_id": str(meta.get("trace_id") or ""),
        "field_modifiers_present": present,
        "field_modifiers_type": type(field_modifiers).__name__,
        "field_modifiers_keys": sorted(field_modifiers.keys())[:20] if isinstance(field_modifiers, dict) else [],
        "layout_present": bool(form.get("layout")),
        "statusbar_field": ((form.get("statusbar") or {}).get("field") if isinstance(form.get("statusbar"), dict) else None),
        "button_count": len(data.get("buttons") or []) if isinstance(data.get("buttons"), list) else 0,
        "rights_present": bool((((data.get("permissions") or {}).get("effective") or {}).get("rights"))),
    }
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0 if payload["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
