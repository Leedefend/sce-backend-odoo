#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

import os

from intent_smoke_utils import require_ok
from python_http_smoke_utils import get_base_url, http_post_json


def _to_str_list(value):
    if isinstance(value, list):
        out = []
        for item in value:
            val = str(item or "").strip()
            if val:
                out.append(val)
        return out
    return []


def _collect_required_caps(scene: dict):
    required = set()
    required.update(_to_str_list(scene.get("required_capabilities")))
    access = scene.get("access")
    if isinstance(access, dict):
        required.update(_to_str_list(access.get("required_capabilities")))
    for tile in scene.get("tiles") if isinstance(scene.get("tiles"), list) else []:
        if not isinstance(tile, dict):
            continue
        required.update(_to_str_list(tile.get("required_capabilities")))
    return required


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
    auth = {"Authorization": f"Bearer {token}"}

    status, init_resp = http_post_json(
        intent_url,
        {"intent": "system.init", "params": {"contract_mode": "hud"}},
        headers=auth,
    )
    require_ok(status, init_resp, "system.init hud")

    data = init_resp.get("data") if isinstance(init_resp.get("data"), dict) else {}
    if isinstance(data.get("data"), dict):  # compat with nested envelope
        data = data.get("data") or data

    scenes = data.get("scenes") if isinstance(data.get("scenes"), list) else []
    capabilities = data.get("capabilities") if isinstance(data.get("capabilities"), list) else []
    if not scenes:
        raise RuntimeError("system.init scenes empty")
    if not capabilities:
        raise RuntimeError("system.init capabilities empty")

    cap_keys = {
        str(item.get("key") or "").strip()
        for item in capabilities
        if isinstance(item, dict) and str(item.get("key") or "").strip()
    }
    if not cap_keys:
        raise RuntimeError("capability keys empty")

    errors = []
    for scene in scenes:
        if not isinstance(scene, dict):
            errors.append("scene item must be object")
            continue
        scene_key = str(scene.get("code") or scene.get("key") or "").strip()
        if not scene_key:
            errors.append("scene missing code/key")
            continue
        refs = _collect_required_caps(scene)
        missing = sorted([key for key in refs if key not in cap_keys])
        if missing:
            errors.append(f"{scene_key}: missing required capabilities {','.join(missing)}")

    if errors:
        raise RuntimeError("scene-capability inconsistency: " + " | ".join(errors[:20]))

    print(f"[scene_capability_contract_guard] PASS scenes={len(scenes)} capabilities={len(cap_keys)}")


if __name__ == "__main__":
    main()
