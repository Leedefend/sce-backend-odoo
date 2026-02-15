#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

import os

from intent_smoke_utils import require_ok
from python_http_smoke_utils import get_base_url, http_post_json


REQUIRED_TRACE_KEYS = (
    "scene_source",
    "scene_contract_ref",
    "scene_channel",
    "channel_selector",
    "channel_source_ref",
)


def _extract_meta_data(resp: dict) -> tuple[dict, dict]:
    meta = resp.get("meta") if isinstance(resp.get("meta"), dict) else {}
    data = resp.get("data") if isinstance(resp.get("data"), dict) else {}
    if not meta and isinstance(data.get("meta"), dict):
        meta = data.get("meta") or {}
    if isinstance(data.get("data"), dict):
        data = data.get("data") or data
    return meta, data


def _assert_trace(meta: dict, *, label: str) -> dict:
    trace = meta.get("scene_trace") if isinstance(meta.get("scene_trace"), dict) else {}
    if not trace:
        raise RuntimeError(f"{label} missing meta.scene_trace")
    for key in REQUIRED_TRACE_KEYS:
        if not str(trace.get(key) or "").strip():
            raise RuntimeError(f"{label} missing meta.scene_trace.{key}")
    governance = trace.get("governance")
    if not isinstance(governance, dict):
        raise RuntimeError(f"{label} missing meta.scene_trace.governance")
    for key in ("before", "after", "filtered"):
        if not isinstance(governance.get(key), dict):
            raise RuntimeError(f"{label} governance missing section: {key}")
    return trace


def main() -> None:
    base_url = get_base_url()
    db_name = os.getenv("E2E_DB") or os.getenv("DB_NAME") or ""
    login = os.getenv("E2E_LOGIN") or "admin"
    password = os.getenv("E2E_PASSWORD") or os.getenv("ADMIN_PASSWD") or "admin"
    intent_url = f"{base_url}/api/v1/intent"

    status, login_resp = http_post_json(
        intent_url,
        {"intent": "login", "params": {"db": db_name, "login": login, "password": password}},
        headers={"X-Anonymous-Intent": "1"},
    )
    require_ok(status, login_resp, "login")
    token = (login_resp.get("data") or {}).get("token")
    if not token:
        raise RuntimeError("login response missing token")

    status, user_resp = http_post_json(
        intent_url,
        {"intent": "system.init", "params": {"contract_mode": "user"}},
        headers={"Authorization": f"Bearer {token}"},
    )
    require_ok(status, user_resp, "system.init user")
    user_meta, user_data = _extract_meta_data(user_resp)
    if (user_meta.get("contract_mode") or "") != "user":
        raise RuntimeError(f"system.init user mode mismatch: meta={user_meta.get('contract_mode')}")
    if user_data.get("hud") is not None:
        raise RuntimeError("system.init user should not include data.hud")
    for key in ("scene_diagnostics", "diagnostic", "scene_channel_selector", "scene_channel_source_ref"):
        if key in user_data:
            raise RuntimeError(f"system.init user should not include {key}")
    user_trace = _assert_trace(user_meta, label="system.init user")

    status, hud_resp = http_post_json(
        intent_url,
        {"intent": "system.init", "params": {"contract_mode": "hud"}},
        headers={"Authorization": f"Bearer {token}"},
    )
    require_ok(status, hud_resp, "system.init hud")
    hud_meta, hud_data = _extract_meta_data(hud_resp)
    if (hud_meta.get("contract_mode") or "") != "hud":
        raise RuntimeError(f"system.init hud mode mismatch: meta={hud_meta.get('contract_mode')}")
    hud_trace = _assert_trace(hud_meta, label="system.init hud")
    hud_payload = hud_data.get("hud") if isinstance(hud_data.get("hud"), dict) else {}
    if not hud_payload:
        raise RuntimeError("system.init hud missing data.hud")
    if not isinstance(hud_data.get("scene_diagnostics"), dict):
        raise RuntimeError("system.init hud missing data.scene_diagnostics")
    for key in REQUIRED_TRACE_KEYS:
        if str(hud_trace.get(key) or "") != str(hud_payload.get(key) or ""):
            raise RuntimeError(f"system.init hud/meta trace mismatch: {key}")
    if str(user_trace.get("scene_channel") or "").strip() != str(hud_trace.get("scene_channel") or "").strip():
        raise RuntimeError("system.init scene_channel mismatch between user/hud mode")

    print("[scene_meta_trace_smoke] PASS")


if __name__ == "__main__":
    main()
