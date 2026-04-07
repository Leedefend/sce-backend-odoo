#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

import os

from python_http_smoke_utils import get_base_url, http_post_json


def _intent(intent_url: str, token: str | None, intent: str, params: dict, anonymous: bool = False):
    headers: dict[str, str] = {}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    if anonymous:
        headers["X-Anonymous-Intent"] = "1"
    return http_post_json(intent_url, {"intent": intent, "params": params}, headers=headers)


def _expect_ok(label: str, status: int, payload: dict) -> None:
    if status >= 400 or not isinstance(payload, dict) or payload.get("ok") is not True:
        raise RuntimeError(f"{label} failed: status={status} payload={payload}")


def _login(intent_url: str, db_name: str, login: str, password: str) -> str:
    st, body = _intent(intent_url, None, "login", {"db": db_name, "login": login, "password": password}, anonymous=True)
    _expect_ok("login", st, body)
    data = body.get("data") if isinstance(body.get("data"), dict) else {}
    token = str(data.get("token") or "").strip()
    if token:
        return token
    session = data.get("session") if isinstance(data.get("session"), dict) else {}
    token = str(session.get("token") or "").strip()
    if not token:
        raise RuntimeError("login token missing")
    return token


def _field_exists(intent_url: str, token: str, model_name: str, field_name: str) -> bool:
    st, body = _intent(
        intent_url,
        token,
        "api.data",
        {
            "op": "list",
            "model": "ir.model.fields",
            "fields": ["id", "name", "model"],
            "domain": [["model", "=", model_name], ["name", "=", field_name]],
            "limit": 1,
        },
    )
    _expect_ok(f"ir.model.fields lookup {model_name}.{field_name}", st, body)
    records = (((body.get("data") or {}).get("records")) or [])
    return bool(records)


def main() -> None:
    base_url = get_base_url()
    intent_url = f"{base_url}/api/v1/intent"
    db_name = str(os.getenv("DB_NAME") or os.getenv("ODOO_DB") or "sc_demo").strip()
    admin_login = str(os.getenv("E2E_LOGIN") or "admin").strip()
    admin_password = str(os.getenv("E2E_PASSWORD") or os.getenv("ADMIN_PASSWD") or "admin").strip()

    token = _login(intent_url, db_name, admin_login, admin_password)

    required = {
        "project.project": ["company_id"],
        "project.task": ["company_id", "project_id"],
        "project.budget": ["company_id", "project_id"],
        "project.cost.ledger": ["company_id", "project_id"],
        "payment.request": ["company_id", "project_id"],
        "payment.ledger": ["company_id", "project_id"],
        "sc.settlement.order": ["company_id", "project_id"],
    }

    missing: list[str] = []
    detail: list[str] = []
    for model_name, fields in required.items():
        present = []
        for field_name in fields:
            if _field_exists(intent_url, token, model_name, field_name):
                present.append(field_name)
            else:
                missing.append(f"{model_name}.{field_name}")
        detail.append(f"{model_name}:{','.join(present)}")

    if missing:
        raise RuntimeError("isolation anchor missing: " + ", ".join(missing))

    print("[native_business_fact_isolation_anchor_verify] PASS " + "|".join(detail))


if __name__ == "__main__":
    main()
