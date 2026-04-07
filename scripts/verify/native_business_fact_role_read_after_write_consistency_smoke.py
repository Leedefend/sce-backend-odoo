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


def _read_shape(data: dict) -> tuple[int, int, str]:
    fields = data.get("fields") if isinstance(data.get("fields"), dict) else {}
    buttons = data.get("buttons") if isinstance(data.get("buttons"), list) else []
    policy = data.get("access_policy") if isinstance(data.get("access_policy"), dict) else {}
    mode = str(policy.get("mode") or "")
    return len(fields), len(buttons), mode


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

    role_matrix = [
        ("owner", str(os.getenv("ROLE_OWNER_LOGIN") or "demo_role_owner").strip(), str(os.getenv("ROLE_OWNER_PASSWORD") or "demo").strip()),
        ("pm", str(os.getenv("ROLE_PM_LOGIN") or "demo_role_pm").strip(), str(os.getenv("ROLE_PM_PASSWORD") or "demo").strip()),
    ]
    model_views = [("project.project", "form"), ("project.task", "form")]

    details: list[str] = []
    for role_key, login, password in role_matrix:
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

        for model, view_type in model_views:
            st_1, payload_1 = _ui_contract(intent_url, token, model, view_type)
            _expect_ok(f"{role_key} {model} first read", st_1, payload_1)
            data_1 = payload_1.get("data") if isinstance(payload_1.get("data"), dict) else {}

            st_2, payload_2 = _ui_contract(intent_url, token, model, view_type)
            _expect_ok(f"{role_key} {model} second read", st_2, payload_2)
            data_2 = payload_2.get("data") if isinstance(payload_2.get("data"), dict) else {}

            shape_1 = _read_shape(data_1)
            shape_2 = _read_shape(data_2)
            if shape_1 != shape_2:
                raise RuntimeError(
                    f"{role_key} {model} read-after-write shape drift: {shape_1} vs {shape_2}"
                )
            if shape_1[0] <= 0:
                raise RuntimeError(f"{role_key} {model} fields empty")
            if shape_1[2] != "allow":
                raise RuntimeError(f"{role_key} {model} access mode unexpected: {shape_1[2]}")

        details.append(f"{role_key}:{login}")

    print(
        "[native_business_fact_role_read_after_write_consistency_smoke] "
        f"PASS roles={len(role_matrix)} details={'|'.join(details)}"
    )


if __name__ == "__main__":
    main()
