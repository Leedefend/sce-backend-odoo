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


def _readiness_check(role: str, model: str, data: dict) -> None:
    if not isinstance(data.get("fields"), dict) or not data.get("fields"):
        raise RuntimeError(f"{role}:{model} fields missing")
    policy = data.get("access_policy") if isinstance(data.get("access_policy"), dict) else {}
    if str(policy.get("mode") or "").strip() != "allow":
        raise RuntimeError(f"{role}:{model} access_policy not allow")

    if model == "payment.request":
        buttons = data.get("buttons") if isinstance(data.get("buttons"), list) else []
        if not buttons:
            raise RuntimeError(f"{role}:{model} transition buttons missing")


def _ui_contract(intent_url: str, token: str, model: str) -> tuple[int, dict]:
    return http_post_json(
        intent_url,
        {"intent": "ui.contract", "params": {"op": "model", "model": model, "view_type": "form"}},
        headers={"Authorization": f"Bearer {token}"},
    )


def main() -> None:
    base_url = get_base_url()
    intent_url = f"{base_url}/api/v1/intent"
    db_name = str(os.getenv("DB_NAME") or os.getenv("ODOO_DB") or "sc_demo").strip()

    role_candidates = [
        ("finance", str(os.getenv("ROLE_FINANCE_LOGIN") or "demo_role_finance").strip(), str(os.getenv("ROLE_FINANCE_PASSWORD") or "demo").strip()),
        ("executive", str(os.getenv("ROLE_EXECUTIVE_LOGIN") or "demo_role_executive").strip(), str(os.getenv("ROLE_EXECUTIVE_PASSWORD") or "demo").strip()),
    ]
    models = ["payment.request", "project.settlement"]

    details: list[str] = []
    for role_key, login, password in role_candidates:
        st_login, payload_login = http_post_json(
            intent_url,
            {"intent": "login", "params": {"db": db_name, "login": login, "password": password}},
            headers={"X-Anonymous-Intent": "1"},
        )
        _expect_ok(f"{role_key} login", st_login, payload_login)
        token = _extract_token(payload_login)
        if not token:
            raise RuntimeError(f"{role_key} missing token")

        for model in models:
            st_model, payload_model = _ui_contract(intent_url, token, model)
            _expect_ok(f"{role_key} contract {model}", st_model, payload_model)
            data = payload_model.get("data") if isinstance(payload_model.get("data"), dict) else {}
            _readiness_check(role_key, model, data)

        details.append(f"{role_key}:{login}")

    print(
        "[native_business_fact_role_transition_readiness_smoke] "
        f"PASS roles={len(role_candidates)} models={len(models)} details={'|'.join(details)}"
    )


if __name__ == "__main__":
    main()
