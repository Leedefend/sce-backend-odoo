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


def _ui_contract(intent_url: str, token: str, model: str) -> tuple[int, dict]:
    return http_post_json(
        intent_url,
        {"intent": "ui.contract", "params": {"op": "model", "model": model, "view_type": "list"}},
        headers={"Authorization": f"Bearer {token}"},
    )


def main() -> None:
    base_url = get_base_url()
    intent_url = f"{base_url}/api/v1/intent"
    db_name = str(os.getenv("DB_NAME") or os.getenv("ODOO_DB") or "sc_demo").strip()

    role_model_matrix = [
        (
            "owner",
            str(os.getenv("ROLE_OWNER_LOGIN") or "demo_role_owner").strip(),
            str(os.getenv("ROLE_OWNER_PASSWORD") or "demo").strip(),
            ["project.project", "project.task", "project.budget", "project.cost.ledger"],
        ),
        (
            "pm",
            str(os.getenv("ROLE_PM_LOGIN") or "demo_role_pm").strip(),
            str(os.getenv("ROLE_PM_PASSWORD") or "demo").strip(),
            ["project.project", "project.task", "project.budget"],
        ),
        (
            "finance",
            str(os.getenv("ROLE_FINANCE_LOGIN") or "demo_role_finance").strip(),
            str(os.getenv("ROLE_FINANCE_PASSWORD") or "demo").strip(),
            ["payment.request", "project.settlement", "project.cost.ledger"],
        ),
        (
            "executive",
            str(os.getenv("ROLE_EXECUTIVE_LOGIN") or "demo_role_executive").strip(),
            str(os.getenv("ROLE_EXECUTIVE_PASSWORD") or "demo").strip(),
            ["project.project", "payment.request", "project.settlement"],
        ),
    ]

    details: list[str] = []
    for role_key, login, password, models in role_model_matrix:
        st_login, payload_login = http_post_json(
            intent_url,
            {"intent": "login", "params": {"db": db_name, "login": login, "password": password}},
            headers={"X-Anonymous-Intent": "1"},
        )
        _expect_ok(f"{role_key} login", st_login, payload_login)
        token = _extract_token(payload_login)
        if not token:
            raise RuntimeError(f"{role_key} missing token")

        st_sys, payload_sys = http_post_json(
            intent_url,
            {"intent": "system.init", "params": {"contract_mode": "user"}},
            headers={"Authorization": f"Bearer {token}"},
        )
        _expect_ok(f"{role_key} system.init", st_sys, payload_sys)

        for model in models:
            st_model, payload_model = _ui_contract(intent_url, token, model)
            _expect_ok(f"{role_key} contract {model}", st_model, payload_model)
            data = payload_model.get("data") if isinstance(payload_model.get("data"), dict) else {}
            if not data:
                raise RuntimeError(f"{role_key} contract {model} data empty")

        details.append(f"{role_key}:{login}:{len(models)}")

    print(
        "[native_business_fact_role_flow_usability_smoke] "
        f"PASS roles={len(role_model_matrix)} details={'|'.join(details)}"
    )


if __name__ == "__main__":
    main()
