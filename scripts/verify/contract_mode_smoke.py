#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

import os

from intent_smoke_utils import require_ok
from python_http_smoke_utils import get_base_url, http_post_json

FORBIDDEN_USER_KEYS = {
    "action_xmlid",
    "menu_xmlid",
    "scene_key",
    "required_groups",
    "required_flag",
    "role_scope",
    "capability_scope",
}


def _has_internal_or_smoke(item: dict) -> bool:
    if not isinstance(item, dict):
        return False
    tags = item.get("tags")
    if isinstance(tags, str):
        tag_set = {x.strip().lower() for x in tags.split(",") if x.strip()}
    elif isinstance(tags, list):
        tag_set = {str(x).strip().lower() for x in tags if str(x).strip()}
    else:
        tag_set = set()
    name = str(item.get("name") or "").strip().lower()
    key = str(item.get("key") or item.get("code") or "").strip().lower()
    if {"internal", "smoke"} & tag_set:
        return True
    if item.get("is_test") or item.get("smoke_test"):
        return True
    text = f"{name} {key}"
    return ("smoke" in text) or ("internal" in text)


def _find_forbidden_keys(value, *, path="", found=None):
    found = found if isinstance(found, list) else []
    if isinstance(value, list):
        for idx, item in enumerate(value):
            _find_forbidden_keys(item, path=f"{path}[{idx}]", found=found)
        return found
    if not isinstance(value, dict):
        return found
    for key, item in value.items():
        key_text = str(key or "").strip().lower()
        next_path = f"{path}.{key}" if path else str(key)
        if key_text in FORBIDDEN_USER_KEYS:
            found.append(next_path)
        _find_forbidden_keys(item, path=next_path, found=found)
    return found


def _post_intent(intent_url: str, token: str, intent: str, params: dict) -> tuple[int, dict]:
    return http_post_json(
        intent_url,
        {"intent": intent, "params": params},
        headers={"Authorization": f"Bearer {token}"},
    )


def _extract_meta_data(resp: dict) -> tuple[dict, dict]:
    if not isinstance(resp, dict):
        return {}, {}
    meta = resp.get("meta") if isinstance(resp.get("meta"), dict) else {}
    data = resp.get("data") if isinstance(resp.get("data"), dict) else {}
    # Compat: some envelopes wrap handler payload in data.{status,data,meta}
    if not meta and isinstance(data.get("meta"), dict):
        meta = data.get("meta") or {}
    if isinstance(data.get("data"), dict):
        data = data.get("data") or data
    return meta, data


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

    status, user_init = _post_intent(
        intent_url,
        token,
        "system.init",
        {"contract_mode": "user"},
    )
    require_ok(status, user_init, "system.init user")
    user_meta, user_data = _extract_meta_data(user_init)
    if (user_meta.get("contract_mode") or "") != "user":
        raise RuntimeError(f"system.init user mode mismatch: meta={user_meta.get('contract_mode')}")
    if (user_data.get("contract_mode") or "") != "user":
        raise RuntimeError(f"system.init user mode mismatch: data={user_data.get('contract_mode')}")

    user_scenes = user_data.get("scenes") if isinstance(user_data.get("scenes"), list) else []
    user_caps = user_data.get("capabilities") if isinstance(user_data.get("capabilities"), list) else []
    if any(_has_internal_or_smoke(item) for item in user_scenes):
        raise RuntimeError("system.init user mode contains internal/smoke scene")
    if any(_has_internal_or_smoke(item) for item in user_caps):
        raise RuntimeError("system.init user mode contains internal/smoke capability")
    forbidden_hits = _find_forbidden_keys({"scenes": user_scenes, "capabilities": user_caps})
    if forbidden_hits:
        detail = ";".join(forbidden_hits[:10])
        raise RuntimeError(f"system.init user mode exposes technical keys: {detail}")

    status, hud_init = _post_intent(
        intent_url,
        token,
        "system.init",
        {"contract_mode": "hud"},
    )
    require_ok(status, hud_init, "system.init hud")
    hud_meta, hud_data = _extract_meta_data(hud_init)
    if (hud_meta.get("contract_mode") or "") != "hud":
        raise RuntimeError(f"system.init hud mode mismatch: meta={hud_meta.get('contract_mode')}")
    if (hud_data.get("contract_mode") or "") != "hud":
        raise RuntimeError(f"system.init hud mode mismatch: data={hud_data.get('contract_mode')}")
    hud_trace = hud_data.get("hud") if isinstance(hud_data.get("hud"), dict) else {}
    for key in ("scene_source", "scene_contract_ref", "channel_selector", "channel_source_ref"):
        if not str(hud_trace.get(key) or "").strip():
            raise RuntimeError(f"system.init hud tracing missing key: {key}")
    governance = hud_trace.get("governance") if isinstance(hud_trace.get("governance"), dict) else {}
    if not governance:
        raise RuntimeError("system.init hud tracing missing governance summary")

    status, user_contract = _post_intent(
        intent_url,
        token,
        "ui.contract",
        {"op": "model", "model": "project.project", "view_type": "tree", "contract_mode": "user"},
    )
    require_ok(status, user_contract, "ui.contract user")
    user_contract_meta, _ = _extract_meta_data(user_contract)
    if user_contract_meta.get("contract_mode") != "user":
        raise RuntimeError("ui.contract user mode mismatch")

    status, hud_contract = _post_intent(
        intent_url,
        token,
        "ui.contract",
        {"op": "model", "model": "project.project", "view_type": "tree", "hud": 1},
    )
    require_ok(status, hud_contract, "ui.contract hud")
    hud_contract_meta, _ = _extract_meta_data(hud_contract)
    if hud_contract_meta.get("contract_mode") != "hud":
        raise RuntimeError("ui.contract hud mode mismatch")

    print("[contract_mode_smoke] PASS")


if __name__ == "__main__":
    main()
