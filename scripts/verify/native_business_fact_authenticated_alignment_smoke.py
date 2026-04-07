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


def _expect_ok_envelope(name: str, status: int, payload: dict) -> None:
    if status >= 400:
        _fail(f"{name} http status unexpected: {status}")
    if not isinstance(payload, dict):
        _fail(f"{name} payload not dict")
    if payload.get("ok") is not True:
        _fail(f"{name} envelope ok!=true: {json.dumps(payload, ensure_ascii=False)[:280]}")
    if "data" not in payload or "meta" not in payload:
        _fail(f"{name} missing envelope keys")


def main() -> None:
    base_url = get_base_url()
    intent_url = f"{base_url}/api/v1/intent"
    db_name = str(os.getenv("DB_NAME") or os.getenv("ODOO_DB") or "sc_dev").strip()
    login = str(os.getenv("E2E_LOGIN") or "admin").strip()
    password = str(os.getenv("E2E_PASSWORD") or os.getenv("ADMIN_PASSWD") or "admin").strip()

    login_status, login_payload = http_post_json(
        intent_url,
        {"intent": "login", "params": {"db": db_name, "login": login, "password": password}},
        headers={"X-Anonymous-Intent": "1"},
    )
    _expect_ok_envelope("login", login_status, login_payload)

    token = _extract_token(login_payload)
    if not token:
        _fail("login missing token")

    auth_headers = {"Authorization": f"Bearer {token}"}

    st_sys, payload_sys = http_post_json(
        intent_url,
        {"intent": "system.init", "params": {"contract_mode": "user"}},
        headers=auth_headers,
    )
    _expect_ok_envelope("system.init", st_sys, payload_sys)

    st_project, payload_project = http_post_json(
        intent_url,
        {"intent": "ui.contract", "params": {"op": "model", "model": "project.project", "view_type": "form"}},
        headers=auth_headers,
    )
    _expect_ok_envelope("ui.contract(project.project)", st_project, payload_project)

    st_dict, payload_dict = http_post_json(
        intent_url,
        {"intent": "ui.contract", "params": {"op": "model", "model": "project.dictionary", "view_type": "tree"}},
        headers=auth_headers,
    )
    _expect_ok_envelope("ui.contract(project.dictionary)", st_dict, payload_dict)

    project_data = payload_project.get("data") if isinstance(payload_project.get("data"), dict) else {}
    dict_data = payload_dict.get("data") if isinstance(payload_dict.get("data"), dict) else {}
    if not project_data:
        _fail("project.project contract data empty")
    if not dict_data:
        _fail("project.dictionary contract data empty")

    print(
        "[native_business_fact_authenticated_alignment_smoke] "
        f"PASS base_url={base_url} login={login} system_init={st_sys} project_contract={st_project} dictionary_contract={st_dict}"
    )


if __name__ == "__main__":
    main()
