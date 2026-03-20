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


def _find_company(models, db: str, uid: int, password: str, company_id: int, company_name: str) -> int:
    if company_id > 0:
        found = _execute(
            models,
            db,
            uid,
            password,
            "res.company",
            "search",
            [[("id", "=", company_id)]],
            {"limit": 1},
        )
        if found:
            return _safe_int(found[0], 0)
    if company_name:
        found = _execute(
            models,
            db,
            uid,
            password,
            "res.company",
            "search",
            [[("name", "=", company_name)]],
            {"limit": 1},
        )
        if found:
            return _safe_int(found[0], 0)
    return 0


def _create_company(models, db: str, uid: int, password: str, company_name: str) -> int:
    if not company_name:
        return 0
    return _safe_int(
        _execute(
            models,
            db,
            uid,
            password,
            "res.company",
            "create",
            [{"name": company_name}],
        ),
        0,
    )


def _find_user(models, db: str, uid: int, password: str, login: str) -> int:
    found = _execute(
        models,
        db,
        uid,
        password,
        "res.users",
        "search",
        [[("login", "=", login)]],
        {"limit": 1},
    )
    if not found:
        return 0
    return _safe_int(found[0], 0)


def _create_user(
    models,
    db: str,
    uid: int,
    password: str,
    login: str,
    name: str,
    plain_password: str,
    company_id: int,
) -> int:
    vals = {
        "name": name,
        "login": login,
        "password": plain_password,
        "share": False,
        "company_id": company_id,
        "company_ids": [[6, 0, [company_id]]],
    }
    return _safe_int(_execute(models, db, uid, password, "res.users", "create", [vals]), 0)


def main() -> int:
    base_url = _get_base_url()
    db = _text(os.getenv("DB_NAME") or os.getenv("E2E_DB"))
    admin_login = _text(os.getenv("ADMIN_LOGIN")) or "admin"
    admin_password = _text(os.getenv("ADMIN_PASSWD") or os.getenv("E2E_PASSWORD")) or "admin"

    target_login = _text(os.getenv("TARGET_LOGIN") or os.getenv("ROLE_PM_LOGIN")) or "demo_role_pm"
    target_user_name = _text(os.getenv("TARGET_USER_NAME")) or "Demo PM Company2"
    target_user_password = _text(os.getenv("TARGET_USER_PASSWORD")) or "demo"

    target_company_id = _safe_int(os.getenv("TARGET_COMPANY_ID"), 2)
    target_company_name = _text(os.getenv("TARGET_COMPANY_NAME")) or "Demo Secondary Company"

    create_company_if_missing = _bool_env("CREATE_COMPANY_IF_MISSING", True)
    create_user_if_missing = _bool_env("CREATE_USER_IF_MISSING", False)
    set_primary_company = _bool_env("SET_PRIMARY_COMPANY", False)
    apply_change = _bool_env("APPLY", False)

    if not db:
        print("[seed_company_secondary_access] FAIL")
        print(" - missing DB_NAME/E2E_DB")
        return 1

    common = xmlrpc.client.ServerProxy(f"{base_url}/xmlrpc/2/common", allow_none=True)
    uid = _safe_int(common.authenticate(db, admin_login, admin_password, {}), 0)
    if uid <= 0:
        print("[seed_company_secondary_access] FAIL")
        print(" - admin authentication failed")
        return 1

    models = xmlrpc.client.ServerProxy(f"{base_url}/xmlrpc/2/object", allow_none=True)

    company_before = _find_company(models, db, uid, admin_password, target_company_id, target_company_name)
    company_created = 0
    company_after = company_before
    if company_before <= 0 and create_company_if_missing and apply_change:
        company_created = _create_company(models, db, uid, admin_password, target_company_name)
        company_after = company_created
    elif company_before <= 0 and create_company_if_missing and not apply_change:
        company_after = -1

    effective_company_id = company_before if company_before > 0 else company_created
    if effective_company_id <= 0 and company_after == -1:
        effective_company_id = target_company_id

    user_before = _find_user(models, db, uid, admin_password, target_login)
    user_created = 0
    write_vals: dict[str, Any] = {}
    before_company_id = 0
    before_company_ids: list[int] = []
    after_company_id = 0
    after_company_ids: list[int] = []

    if user_before > 0:
        rows = _execute(
            models,
            db,
            uid,
            admin_password,
            "res.users",
            "read",
            [[user_before]],
            {"fields": ["company_id", "company_ids"]},
        )
        row = rows[0] if isinstance(rows, list) and rows else {}
        before_company_id = _safe_int((row.get("company_id") or [0])[0], 0)
        before_company_ids = [_safe_int(item, 0) for item in (row.get("company_ids") or []) if _safe_int(item, 0) > 0]

        if effective_company_id > 0 and effective_company_id not in before_company_ids:
            write_vals["company_ids"] = [[4, effective_company_id]]
        if set_primary_company and effective_company_id > 0 and before_company_id != effective_company_id:
            write_vals["company_id"] = effective_company_id

        if apply_change and write_vals:
            _execute(models, db, uid, admin_password, "res.users", "write", [[user_before], write_vals])

        rows_after = _execute(
            models,
            db,
            uid,
            admin_password,
            "res.users",
            "read",
            [[user_before]],
            {"fields": ["company_id", "company_ids"]},
        )
        row_after = rows_after[0] if isinstance(rows_after, list) and rows_after else {}
        after_company_id = _safe_int((row_after.get("company_id") or [0])[0], 0)
        after_company_ids = [_safe_int(item, 0) for item in (row_after.get("company_ids") or []) if _safe_int(item, 0) > 0]
    else:
        if create_user_if_missing and apply_change and effective_company_id > 0:
            user_created = _create_user(
                models,
                db,
                uid,
                admin_password,
                target_login,
                target_user_name,
                target_user_password,
                effective_company_id,
            )
            after_company_id = effective_company_id
            after_company_ids = [effective_company_id]

    result = {
        "ok": True,
        "db": db,
        "base_url": base_url,
        "apply": apply_change,
        "target": {
            "login": target_login,
            "company_id": target_company_id,
            "company_name": target_company_name,
        },
        "policy": {
            "create_company_if_missing": create_company_if_missing,
            "create_user_if_missing": create_user_if_missing,
            "set_primary_company": set_primary_company,
        },
        "company": {
            "before_id": company_before,
            "after_id": company_after,
            "created_id": company_created,
        },
        "user": {
            "before_id": user_before,
            "created_id": user_created,
            "before_company_id": before_company_id,
            "before_company_ids": before_company_ids,
            "after_company_id": after_company_id,
            "after_company_ids": after_company_ids,
            "write_vals": write_vals,
        },
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))
    print("[seed_company_secondary_access] PASS")
    if not apply_change:
        print("[seed_company_secondary_access] DRY-RUN (set APPLY=1 to apply)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

