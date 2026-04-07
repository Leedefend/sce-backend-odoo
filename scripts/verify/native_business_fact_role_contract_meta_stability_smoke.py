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
        {"intent": "ui.contract", "params": {"op": "model", "model": model, "view_type": "form"}},
        headers={"Authorization": f"Bearer {token}"},
    )


def _meta_signature(payload: dict) -> tuple[tuple[str, ...], tuple[str, ...]]:
    meta = payload.get("meta") if isinstance(payload.get("meta"), dict) else {}
    meta_keys = tuple(sorted(str(key) for key in meta.keys()))
    core_values = tuple(str(meta.get(name) or "") for name in ("version", "contract_version"))
    return meta_keys, core_values


def main() -> None:
    base_url = get_base_url()
    intent_url = f"{base_url}/api/v1/intent"
    db_name = str(os.getenv("DB_NAME") or os.getenv("ODOO_DB") or "sc_demo").strip()

    roles = [
        ("finance", str(os.getenv("ROLE_FINANCE_LOGIN") or "demo_role_finance").strip(), str(os.getenv("ROLE_FINANCE_PASSWORD") or "demo").strip()),
        ("executive", str(os.getenv("ROLE_EXECUTIVE_LOGIN") or "demo_role_executive").strip(), str(os.getenv("ROLE_EXECUTIVE_PASSWORD") or "demo").strip()),
    ]
    models = ["payment.request", "project.settlement"]

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

        for model in models:
            st1, p1 = _ui_contract(intent_url, token, model)
            _expect_ok(f"{role_key} {model} read1", st1, p1)
            st2, p2 = _ui_contract(intent_url, token, model)
            _expect_ok(f"{role_key} {model} read2", st2, p2)

            sig1 = _meta_signature(p1)
            sig2 = _meta_signature(p2)
            if sig1 != sig2:
                raise RuntimeError(f"{role_key} {model} meta drift")

        details.append(f"{role_key}:{login}")

    print(
        "[native_business_fact_role_contract_meta_stability_smoke] "
        f"PASS roles={len(roles)} models={len(models)} details={'|'.join(details)}"
    )


if __name__ == "__main__":
    main()
