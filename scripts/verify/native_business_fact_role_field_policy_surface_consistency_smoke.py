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


def _field_policy_signature(data: dict) -> tuple[tuple[str, str], ...]:
    field_policies = data.get("field_policies") if isinstance(data.get("field_policies"), dict) else {}
    normalized: list[tuple[str, str]] = []
    for field_name, policy in sorted(field_policies.items()):
        if isinstance(policy, dict):
            mode = str(policy.get("mode") or policy.get("policy") or "")
        else:
            mode = str(policy or "")
        normalized.append((str(field_name), mode))
    return tuple(normalized)


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
            d1 = p1.get("data") if isinstance(p1.get("data"), dict) else {}
            d2 = p2.get("data") if isinstance(p2.get("data"), dict) else {}
            sig1 = _field_policy_signature(d1)
            sig2 = _field_policy_signature(d2)
            if sig1 != sig2:
                raise RuntimeError(f"{role_key} {model} field-policy surface drift")
            if not sig1:
                raise RuntimeError(f"{role_key} {model} field_policies empty")

        details.append(f"{role_key}:{login}")

    print(
        "[native_business_fact_role_field_policy_surface_consistency_smoke] "
        f"PASS roles={len(roles)} models={len(models)} details={'|'.join(details)}"
    )


if __name__ == "__main__":
    main()
