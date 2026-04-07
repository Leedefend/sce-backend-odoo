#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

import os

from python_http_smoke_utils import get_base_url, http_post_json


def _extract_token(payload: dict) -> str:
    data = payload.get("data") if isinstance(payload.get("data"), dict) else {}
    token = str(data.get("token") or "").strip()
    if token:
        return token
    session = data.get("session") if isinstance(data.get("session"), dict) else {}
    return str(session.get("token") or "").strip()


def _expect_ok(name: str, status: int, payload: dict) -> None:
    if status >= 400:
        raise RuntimeError(f"{name} status unexpected: {status}")
    if not isinstance(payload, dict) or payload.get("ok") is not True:
        raise RuntimeError(f"{name} envelope invalid")


def _ui_contract(intent_url: str, token: str) -> tuple[int, dict]:
    return http_post_json(
        intent_url,
        {"intent": "ui.contract", "params": {"op": "model", "model": "payment.request", "view_type": "form"}},
        headers={"Authorization": f"Bearer {token}"},
    )


def _visibility_signature(data: dict) -> tuple[tuple[str, str], ...]:
    buttons = data.get("buttons") if isinstance(data.get("buttons"), list) else []
    signature: list[tuple[str, str]] = []
    for button in buttons:
        if not isinstance(button, dict):
            continue
        key = str(button.get("key") or "")
        visible = str(button.get("visible") or "")
        signature.append((key, visible))
    return tuple(sorted(signature))


def main() -> None:
    base_url = get_base_url()
    intent_url = f"{base_url}/api/v1/intent"
    db_name = str(os.getenv("DB_NAME") or os.getenv("ODOO_DB") or "sc_demo").strip()

    roles = [
        ("finance", str(os.getenv("ROLE_FINANCE_LOGIN") or "demo_role_finance").strip(), str(os.getenv("ROLE_FINANCE_PASSWORD") or "demo").strip()),
        ("executive", str(os.getenv("ROLE_EXECUTIVE_LOGIN") or "demo_role_executive").strip(), str(os.getenv("ROLE_EXECUTIVE_PASSWORD") or "demo").strip()),
    ]

    details: list[str] = []
    for role_key, login, password in roles:
        st_login, payload_login = http_post_json(
            intent_url,
            {"intent": "login", "params": {"db": db_name, "login": login, "password": password}},
            headers={"X-Anonymous-Intent": "1"},
        )
        _expect_ok(f"{role_key} login", st_login, payload_login)
        token = _extract_token(payload_login)
        if not token:
            raise RuntimeError(f"{role_key} missing token")

        st1, p1 = _ui_contract(intent_url, token)
        _expect_ok(f"{role_key} read1", st1, p1)
        st2, p2 = _ui_contract(intent_url, token)
        _expect_ok(f"{role_key} read2", st2, p2)

        d1 = p1.get("data") if isinstance(p1.get("data"), dict) else {}
        d2 = p2.get("data") if isinstance(p2.get("data"), dict) else {}
        sig1 = _visibility_signature(d1)
        sig2 = _visibility_signature(d2)
        if not sig1:
            raise RuntimeError(f"{role_key} button visibility signature empty")
        if sig1 != sig2:
            raise RuntimeError(f"{role_key} button visibility surface drift")

        details.append(f"{role_key}:{login}:buttons={len(sig1)}")

    print(
        "[native_business_fact_role_button_visibility_surface_consistency_smoke] "
        f"PASS roles={len(roles)} details={'|'.join(details)}"
    )


if __name__ == "__main__":
    main()
