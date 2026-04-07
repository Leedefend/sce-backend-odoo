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
        {
            "intent": "ui.contract",
            "params": {"op": "model", "model": "payment.request", "view_type": "form"},
        },
        headers={"Authorization": f"Bearer {token}"},
    )


def _button_shape(button: dict) -> tuple[str, str, tuple[str, ...]]:
    intent = str(button.get("intent") or "").strip()
    key = str(button.get("key") or "").strip()
    params = button.get("params") if isinstance(button.get("params"), dict) else {}
    return key, intent, tuple(sorted(params.keys()))


def main() -> None:
    base_url = get_base_url()
    intent_url = f"{base_url}/api/v1/intent"
    db_name = str(os.getenv("DB_NAME") or os.getenv("ODOO_DB") or "sc_demo").strip()

    roles = [
        (
            "finance",
            str(os.getenv("ROLE_FINANCE_LOGIN") or "demo_role_finance").strip(),
            str(os.getenv("ROLE_FINANCE_PASSWORD") or "demo").strip(),
        ),
        (
            "executive",
            str(os.getenv("ROLE_EXECUTIVE_LOGIN") or "demo_role_executive").strip(),
            str(os.getenv("ROLE_EXECUTIVE_PASSWORD") or "demo").strip(),
        ),
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

        st_1, payload_1 = _ui_contract(intent_url, token)
        _expect_ok(f"{role_key} payment.request form read1", st_1, payload_1)
        st_2, payload_2 = _ui_contract(intent_url, token)
        _expect_ok(f"{role_key} payment.request form read2", st_2, payload_2)

        data_1 = payload_1.get("data") if isinstance(payload_1.get("data"), dict) else {}
        data_2 = payload_2.get("data") if isinstance(payload_2.get("data"), dict) else {}
        btns_1 = [item for item in (data_1.get("buttons") or []) if isinstance(item, dict)]
        btns_2 = [item for item in (data_2.get("buttons") or []) if isinstance(item, dict)]

        ready_1 = [_button_shape(btn) for btn in btns_1 if isinstance(btn.get("params"), dict) and str(btn.get("intent") or "").strip()]
        ready_2 = [_button_shape(btn) for btn in btns_2 if isinstance(btn.get("params"), dict) and str(btn.get("intent") or "").strip()]

        if not ready_1:
            raise RuntimeError(f"{role_key} no intent-ready buttons in first read")
        if ready_1 != ready_2:
            raise RuntimeError(f"{role_key} action payload shape drift between reads")

        details.append(f"{role_key}:{login}:ready={len(ready_1)}")

    print(
        "[native_business_fact_role_action_payload_shape_smoke] "
        f"PASS roles={len(roles)} details={'|'.join(details)}"
    )


if __name__ == "__main__":
    main()
