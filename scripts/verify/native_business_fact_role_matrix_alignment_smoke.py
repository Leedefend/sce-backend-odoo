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


def _role_candidates() -> list[tuple[str, str, str]]:
    return [
        ("owner", str(os.getenv("ROLE_OWNER_LOGIN") or "demo_role_owner").strip(), str(os.getenv("ROLE_OWNER_PASSWORD") or "demo").strip()),
        ("pm", str(os.getenv("ROLE_PM_LOGIN") or "demo_role_pm").strip(), str(os.getenv("ROLE_PM_PASSWORD") or "demo").strip()),
        ("finance", str(os.getenv("ROLE_FINANCE_LOGIN") or "demo_role_finance").strip(), str(os.getenv("ROLE_FINANCE_PASSWORD") or "demo").strip()),
        ("executive", str(os.getenv("ROLE_EXECUTIVE_LOGIN") or "demo_role_executive").strip(), str(os.getenv("ROLE_EXECUTIVE_PASSWORD") or "demo").strip()),
    ]


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

    passed = 0
    details: list[str] = []
    for role_key, login, password in _role_candidates():
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

        st_project, payload_project = _ui_contract(intent_url, token, "project.project")
        _expect_ok(f"{role_key} project.contract", st_project, payload_project)

        st_task, payload_task = _ui_contract(intent_url, token, "project.task")
        _expect_ok(f"{role_key} task.contract", st_task, payload_task)

        passed += 1
        details.append(f"{role_key}:{login}:ok")

    print(
        "[native_business_fact_role_matrix_alignment_smoke] "
        f"PASS roles_checked={passed} details={'|'.join(details)}"
    )


if __name__ == "__main__":
    main()
