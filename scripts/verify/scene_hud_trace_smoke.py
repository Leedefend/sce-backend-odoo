#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

import os

from intent_smoke_utils import require_ok
from python_http_smoke_utils import get_base_url, http_post_json


REQUIRED_HUD_KEYS = (
    "scene_source",
    "scene_contract_ref",
    "scene_channel",
    "channel_selector",
    "channel_source_ref",
)


def _extract_meta(resp: dict) -> dict:
    meta = resp.get("meta") if isinstance(resp.get("meta"), dict) else {}
    data = resp.get("data") if isinstance(resp.get("data"), dict) else {}
    if not meta and isinstance(data.get("meta"), dict):
        meta = data.get("meta") or {}
    return meta


def _extract_data(resp: dict) -> dict:
    data = resp.get("data") if isinstance(resp.get("data"), dict) else {}
    if isinstance(data.get("data"), dict):
        data = data.get("data") or data
    return data


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

    status, init_resp = http_post_json(
        intent_url,
        {"intent": "system.init", "params": {"contract_mode": "hud"}},
        headers={"Authorization": f"Bearer {token}"},
    )
    require_ok(status, init_resp, "system.init hud")
    data = _extract_data(init_resp)
    meta = _extract_meta(init_resp)
    hud = data.get("hud") if isinstance(data.get("hud"), dict) else {}
    if not hud:
        raise RuntimeError("system.init hud payload missing")
    meta_trace = meta.get("scene_trace") if isinstance(meta.get("scene_trace"), dict) else {}
    if not meta_trace:
        raise RuntimeError("system.init hud meta.scene_trace missing")
    for key in REQUIRED_HUD_KEYS:
        if not str(hud.get(key) or "").strip():
            raise RuntimeError(f"system.init hud missing trace field: {key}")
        if not str(meta_trace.get(key) or "").strip():
            raise RuntimeError(f"system.init hud meta.scene_trace missing trace field: {key}")
        if str(hud.get(key) or "") != str(meta_trace.get(key) or ""):
            raise RuntimeError(f"system.init hud/meta trace mismatch field: {key}")
    governance = hud.get("governance")
    if not isinstance(governance, dict):
        raise RuntimeError("system.init hud governance summary missing")
    meta_governance = meta_trace.get("governance")
    if not isinstance(meta_governance, dict):
        raise RuntimeError("system.init hud meta.scene_trace governance summary missing")
    for key in ("before", "after", "filtered"):
        if not isinstance(governance.get(key), dict):
            raise RuntimeError(f"system.init hud governance missing section: {key}")
        if not isinstance(meta_governance.get(key), dict):
            raise RuntimeError(f"system.init hud meta.scene_trace governance missing section: {key}")
    print("[scene_hud_trace_smoke] PASS")


if __name__ == "__main__":
    main()
