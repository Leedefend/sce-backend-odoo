#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

import json
import os
from typing import Any

from intent_smoke_utils import require_ok
from python_http_smoke_utils import get_base_url, http_post_json


def _post(
    intent_url: str,
    token: str | None,
    intent: str,
    params: dict[str, Any] | None = None,
    *,
    db_name: str = "",
) -> tuple[int, dict[str, Any]]:
    headers = {"X-Anonymous-Intent": "1"} if token is None else {"Authorization": f"Bearer {token}"}
    if db_name:
        headers["X-Odoo-DB"] = db_name
    status, payload = http_post_json(intent_url, {"intent": intent, "params": params or {}}, headers=headers)
    return status, payload if isinstance(payload, dict) else {}


def fetch_system_init_payload(
    *,
    with_preload: bool | None = None,
    contract_mode: str | None = None,
    extra_params: dict[str, Any] | None = None,
) -> dict[str, Any]:
    base_url = get_base_url()
    db_name = str(os.getenv("E2E_DB") or os.getenv("DB_NAME") or "").strip()
    login = str(os.getenv("E2E_LOGIN") or "admin").strip()
    password = str(os.getenv("E2E_PASSWORD") or os.getenv("ADMIN_PASSWD") or "admin").strip()
    intent_url = f"{base_url}/api/v1/intent"
    if db_name:
        intent_url = f"{intent_url}?db={db_name}"

    status, login_resp = _post(
        intent_url,
        None,
        "login",
        {"db": db_name, "login": login, "password": password},
        db_name=db_name,
    )
    require_ok(status, login_resp, "login")

    login_data = login_resp.get("data") if isinstance(login_resp.get("data"), dict) else {}
    token = ((login_data.get("session") or {}) if isinstance(login_data.get("session"), dict) else {}).get("token")
    token = str(token or "").strip()
    if not token:
        raise RuntimeError("login response missing data.session.token")

    resolved_with_preload = with_preload
    if resolved_with_preload is None:
        resolved_with_preload = str(os.getenv("SYSTEM_INIT_WITH_PRELOAD") or "0").strip() in {"1", "true", "yes"}
    resolved_contract_mode = str(contract_mode or os.getenv("SYSTEM_INIT_CONTRACT_MODE") or "default").strip() or "default"
    params = {
        "with_preload": bool(resolved_with_preload),
        "contract_mode": resolved_contract_mode,
    }
    if isinstance(extra_params, dict):
        params.update(extra_params)
    status, init_resp = _post(
        intent_url,
        token,
        "system.init",
        params,
        db_name=db_name,
    )
    require_ok(status, init_resp, "system.init")

    raw_bytes = len(json.dumps(init_resp, ensure_ascii=False, separators=(",", ":")).encode("utf-8"))
    data = init_resp.get("data") if isinstance(init_resp.get("data"), dict) else {}
    return {
        "intent_url": intent_url,
        "db_name": db_name,
        "login": login,
        "with_preload": bool(resolved_with_preload),
        "contract_mode": resolved_contract_mode,
        "response": init_resp,
        "data": data,
        "payload_bytes": raw_bytes,
    }
