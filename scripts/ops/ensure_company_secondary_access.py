#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

import json
import os
import sys
import xmlrpc.client
from typing import Any


def _text(value: Any) -> str:
    return str(value or "").strip()


def _safe_int(value: Any, default: int = 0) -> int:
    try:
        return int(value)
    except Exception:
        return default


def _bool_env(name: str, default: bool = False) -> bool:
    raw = _text(os.getenv(name))
    if not raw:
        return default
    return raw.lower() in {"1", "true", "yes", "on"}


def _get_base_url() -> str:
    base = _text(os.getenv("E2E_BASE_URL"))
    if base:
        return base.rstrip("/")
    port = _text(os.getenv("ODOO_PORT")) or "8070"
    return f"http://localhost:{port}"


def _execute(models, db: str, uid: int, password: str, model: str, method: str, args=None, kwargs=None):
    return models.execute_kw(db, uid, password, model, method, args or [], kwargs or {})


def main() -> int:
    base_url = _get_base_url()
    db = _text(os.getenv("DB_NAME") or os.getenv("E2E_DB"))
    admin_login = _text(os.getenv("ADMIN_LOGIN")) or "admin"
    admin_password = _text(os.getenv("ADMIN_PASSWD") or os.getenv("E2E_PASSWORD")) or "admin"
    target_login = _text(os.getenv("TARGET_LOGIN") or os.getenv("ROLE_PM_LOGIN")) or "demo_role_pm"
    target_company_id = _safe_int(os.getenv("TARGET_COMPANY_ID"), 2)
    apply_change = _bool_env("APPLY", False)

    if not db:
        print("[ensure_company_secondary_access] FAIL")
        print(" - missing DB_NAME/E2E_DB")
        return 1

    common = xmlrpc.client.ServerProxy(f"{base_url}/xmlrpc/2/common", allow_none=True)
    uid = _safe_int(common.authenticate(db, admin_login, admin_password, {}), 0)
    if uid <= 0:
        print("[ensure_company_secondary_access] FAIL")
        print(" - admin authentication failed")
        return 1

    models = xmlrpc.client.ServerProxy(f"{base_url}/xmlrpc/2/object", allow_none=True)

    company_ids = _execute(
        models,
        db,
        uid,
        admin_password,
        "res.company",
        "search",
        [[("id", "=", target_company_id)]],
        {"limit": 1},
    )
    if not company_ids:
        print("[ensure_company_secondary_access] FAIL")
        print(f" - target company id not found: {target_company_id}")
        return 1

    user_ids = _execute(
        models,
        db,
        uid,
        admin_password,
        "res.users",
        "search",
        [[("login", "=", target_login)]],
        {"limit": 1},
    )
    if not user_ids:
        print("[ensure_company_secondary_access] FAIL")
        print(f" - target user login not found: {target_login}")
        return 1

    user_id = _safe_int(user_ids[0], 0)
    payload = _execute(
        models,
        db,
        uid,
        admin_password,
        "res.users",
        "read",
        [[user_id]],
        {"fields": ["id", "login", "company_id", "company_ids"]},
    )
    row = payload[0] if isinstance(payload, list) and payload else {}
    before_company_id = _safe_int((row.get("company_id") or [0])[0], 0)
    before_company_ids = [
        _safe_int(item, 0) for item in (row.get("company_ids") or []) if _safe_int(item, 0) > 0
    ]

    needs_main_company_switch = before_company_id != target_company_id
    needs_allowed_company_append = target_company_id not in before_company_ids

    write_vals: dict[str, Any] = {}
    if needs_main_company_switch:
        write_vals["company_id"] = target_company_id
    if needs_allowed_company_append:
        write_vals["company_ids"] = [[4, target_company_id]]

    write_done = False
    if apply_change and write_vals:
        _execute(models, db, uid, admin_password, "res.users", "write", [[user_id], write_vals])
        write_done = True

    after_payload = _execute(
        models,
        db,
        uid,
        admin_password,
        "res.users",
        "read",
        [[user_id]],
        {"fields": ["id", "login", "company_id", "company_ids"]},
    )
    after_row = after_payload[0] if isinstance(after_payload, list) and after_payload else {}
    after_company_id = _safe_int((after_row.get("company_id") or [0])[0], 0)
    after_company_ids = [
        _safe_int(item, 0) for item in (after_row.get("company_ids") or []) if _safe_int(item, 0) > 0
    ]

    result = {
        "ok": True,
        "db": db,
        "base_url": base_url,
        "target_login": target_login,
        "target_company_id": target_company_id,
        "apply": apply_change,
        "write_done": write_done,
        "write_vals": write_vals,
        "before": {
            "company_id": before_company_id,
            "company_ids": before_company_ids,
        },
        "after": {
            "company_id": after_company_id,
            "company_ids": after_company_ids,
        },
    }

    print(json.dumps(result, ensure_ascii=False, indent=2))
    print("[ensure_company_secondary_access] PASS")
    if write_vals and not apply_change:
        print("[ensure_company_secondary_access] DRY-RUN (set APPLY=1 to apply)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

