#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

import json
import os

from python_http_smoke_utils import get_base_url, http_post_json


def _fail(message: str) -> None:
    raise RuntimeError(message)


def _extract_token(payload: dict) -> str:
    data = payload.get("data") if isinstance(payload.get("data"), dict) else {}
    token = str(data.get("token") or "").strip()
    if token:
        return token
    session = data.get("session") if isinstance(data.get("session"), dict) else {}
    return str(session.get("token") or "").strip()


def _expect_ok(name: str, status: int, payload: dict) -> None:
    if status >= 400:
        _fail(f"{name} status unexpected: {status}")
    if not isinstance(payload, dict):
        _fail(f"{name} payload not dict")
    if payload.get("ok") is not True:
        _fail(f"{name} envelope not ok: {json.dumps(payload, ensure_ascii=False)[:320]}")


def _ui_contract(intent_url: str, token: str, model: str, view_type: str) -> tuple[int, dict]:
    return http_post_json(
        intent_url,
        {"intent": "ui.contract", "params": {"op": "model", "model": model, "view_type": view_type}},
        headers={"Authorization": f"Bearer {token}"},
    )


def main() -> None:
    base_url = get_base_url()
    intent_url = f"{base_url}/api/v1/intent"
    db_name = str(os.getenv("DB_NAME") or os.getenv("ODOO_DB") or "sc_demo").strip()

    candidates = [
        (str(os.getenv("ROLE_PM_LOGIN") or "demo_role_pm").strip(), str(os.getenv("ROLE_PM_PASSWORD") or "demo").strip()),
        (str(os.getenv("ROLE_OWNER_LOGIN") or "demo_role_owner").strip(), str(os.getenv("ROLE_OWNER_PASSWORD") or "demo").strip()),
        (str(os.getenv("ROLE_FINANCE_LOGIN") or "demo_role_finance").strip(), str(os.getenv("ROLE_FINANCE_PASSWORD") or "demo").strip()),
        (str(os.getenv("ROLE_EXECUTIVE_LOGIN") or "demo_role_executive").strip(), str(os.getenv("ROLE_EXECUTIVE_PASSWORD") or "demo").strip()),
    ]

    token = ""
    role_login = ""
    login_failures: list[str] = []
    for candidate_login, candidate_password in candidates:
        st_login, payload_login = http_post_json(
            intent_url,
            {"intent": "login", "params": {"db": db_name, "login": candidate_login, "password": candidate_password}},
            headers={"X-Anonymous-Intent": "1"},
        )
        if st_login >= 400 or not isinstance(payload_login, dict) or payload_login.get("ok") is not True:
            login_failures.append(f"{candidate_login}:{st_login}")
            continue
        candidate_token = _extract_token(payload_login)
        if not candidate_token:
            login_failures.append(f"{candidate_login}:token_missing")
            continue
        role_login = candidate_login
        token = candidate_token
        break

    if not token:
        _fail(f"all role login candidates failed: {', '.join(login_failures)}")

    st_sys, payload_sys = http_post_json(
        intent_url,
        {"intent": "system.init", "params": {"contract_mode": "user"}},
        headers={"Authorization": f"Bearer {token}"},
    )
    _expect_ok("role system.init", st_sys, payload_sys)

    st_project, payload_project = _ui_contract(intent_url, token, "project.project", "list")
    _expect_ok("role ui.contract project.project", st_project, payload_project)

    st_task, payload_task = _ui_contract(intent_url, token, "project.task", "list")
    _expect_ok("role ui.contract project.task", st_task, payload_task)

    project_data = payload_project.get("data") if isinstance(payload_project.get("data"), dict) else {}
    task_data = payload_task.get("data") if isinstance(payload_task.get("data"), dict) else {}
    if not project_data:
        _fail("role project.project contract data empty")
    if not task_data:
        _fail("role project.task contract data empty")

    print(
        "[native_business_fact_role_alignment_smoke] "
        f"PASS base_url={base_url} role_login={role_login} system_init={st_sys} project_contract={st_project} task_contract={st_task}"
    )


if __name__ == "__main__":
    main()
