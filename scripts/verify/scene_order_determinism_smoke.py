#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

import os

from intent_smoke_utils import require_ok
from python_http_smoke_utils import get_base_url, http_post_json


def _login(intent_url: str, *, db_name: str, login: str, password: str) -> str | None:
    status, payload = http_post_json(
        intent_url,
        {"intent": "login", "params": {"db": db_name, "login": login, "password": password}},
        headers={"X-Anonymous-Intent": "1"},
    )
    if status != 200 or not payload.get("ok"):
        return None
    data = payload.get("data") if isinstance(payload.get("data"), dict) else {}
    token = data.get("token")
    return str(token) if token else None


def _extract_sequences(payload: dict) -> tuple[list[str], list[str]]:
    data = payload.get("data") if isinstance(payload.get("data"), dict) else {}
    if isinstance(data.get("data"), dict):
        data = data.get("data") or data
    scenes = data.get("scenes") if isinstance(data.get("scenes"), list) else []
    capabilities = data.get("capabilities") if isinstance(data.get("capabilities"), list) else []
    scene_seq = [str(item.get("code") or item.get("key") or "").strip() for item in scenes if isinstance(item, dict)]
    cap_seq = [str(item.get("key") or "").strip() for item in capabilities if isinstance(item, dict)]
    return scene_seq, cap_seq


def main() -> None:
    base_url = get_base_url()
    db_name = os.getenv("E2E_DB") or os.getenv("DB_NAME") or ""
    login = os.getenv("E2E_LOGIN") or "admin"
    password = os.getenv("E2E_PASSWORD") or os.getenv("ADMIN_PASSWD") or "admin"
    intent_url = f"{base_url}/api/v1/intent"

    token = _login(intent_url, db_name=db_name, login=login, password=password)
    if not token:
        raise RuntimeError(f"login failed for determinism smoke: {login}")

    headers = {"Authorization": f"Bearer {token}"}
    req = {"intent": "system.init", "params": {"contract_mode": "hud"}}

    status1, resp1 = http_post_json(intent_url, req, headers=headers)
    require_ok(status1, resp1, "system.init hud #1")
    status2, resp2 = http_post_json(intent_url, req, headers=headers)
    require_ok(status2, resp2, "system.init hud #2")

    scenes1, caps1 = _extract_sequences(resp1)
    scenes2, caps2 = _extract_sequences(resp2)
    if scenes1 != scenes2:
        raise RuntimeError("scene order is not deterministic across repeated system.init calls")
    if caps1 != caps2:
        raise RuntimeError("capability order is not deterministic across repeated system.init calls")
    if len(scenes1) != len(set(scenes1)):
        raise RuntimeError("scene sequence contains duplicate keys")
    if len(caps1) != len(set(caps1)):
        raise RuntimeError("capability sequence contains duplicate keys")
    print(f"[scene_order_determinism_smoke] PASS scenes={len(scenes1)} capabilities={len(caps1)}")


if __name__ == "__main__":
    main()
