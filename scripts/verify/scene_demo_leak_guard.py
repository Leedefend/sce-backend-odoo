#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

import json
import os
from pathlib import Path

from intent_smoke_utils import require_ok
from python_http_smoke_utils import get_base_url, http_post_json


DEMO_MARKERS = ("demo", "showcase", "smart_construction_demo")
ROOT = Path(__file__).resolve().parents[2]
PROD_LIKE_BASELINE_JSON = ROOT / "scripts" / "verify" / "baselines" / "role_capability_floor_prod_like.json"


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


def _contains_demo_marker(value) -> bool:
    text = str(value or "").strip().lower()
    if not text:
        return False
    return any(marker in text for marker in DEMO_MARKERS)


def _has_demo_semantics(item: dict) -> bool:
    if not isinstance(item, dict):
        return False
    tags = item.get("tags") if isinstance(item.get("tags"), list) else []
    for tag in tags:
        if _contains_demo_marker(tag):
            return True
    for key in ("key", "code", "name", "title", "label"):
        if _contains_demo_marker(item.get(key)):
            return True
    target = item.get("target")
    if isinstance(target, dict):
        for key in ("menu_xmlid", "action_xmlid", "route"):
            if _contains_demo_marker(target.get(key)):
                return True
    return False


def _load_prod_like_logins() -> list[str]:
    if not PROD_LIKE_BASELINE_JSON.is_file():
        return []
    try:
        payload = json.loads(PROD_LIKE_BASELINE_JSON.read_text(encoding="utf-8"))
    except Exception:
        return []
    fixtures = payload.get("fixtures") if isinstance(payload, dict) and isinstance(payload.get("fixtures"), list) else []
    logins: list[str] = []
    for fixture in fixtures:
        if not isinstance(fixture, dict):
            continue
        login = str(fixture.get("login") or "").strip()
        if login and login not in logins:
            logins.append(login)
    return logins


def main() -> None:
    base_url = get_base_url()
    db_name = os.getenv("E2E_DB") or os.getenv("DB_NAME") or ""
    env_candidates = str(os.getenv("E2E_ROLE_MATRIX_LOGINS") or "").strip()
    if env_candidates:
        login_candidates = [item.strip() for item in env_candidates.split(",") if item.strip()]
    else:
        login_candidates = _load_prod_like_logins()
        if "admin" not in login_candidates:
            login_candidates.append("admin")
        # Legacy fallback for older local DBs that still rely on demo users.
        if "demo_pm" not in login_candidates:
            login_candidates.append("demo_pm")
    explicit_login = str(os.getenv("E2E_LOGIN") or "").strip()
    if explicit_login:
        login_candidates = [explicit_login] + [item for item in login_candidates if item != explicit_login]
    default_pwd = os.getenv("E2E_ROLE_MATRIX_DEFAULT_PASSWORD") or "demo"
    prod_like_pwd = os.getenv("E2E_PROD_LIKE_PASSWORD") or "prod_like"
    admin_pwd = os.getenv("E2E_PASSWORD") or os.getenv("ADMIN_PASSWD") or "admin"

    intent_url = f"{base_url}/api/v1/intent"
    token = None
    selected_login = ""
    for login in login_candidates:
        if login == "admin":
            pwd = admin_pwd
        elif login.startswith("sc_fx_"):
            pwd = prod_like_pwd
        else:
            pwd = default_pwd
        token = _login(intent_url, db_name=db_name, login=login, password=pwd)
        if token:
            selected_login = login
            break
    if not token:
        raise RuntimeError(f"unable to login with candidates: {','.join(login_candidates)}")

    status, init_resp = http_post_json(
        intent_url,
        {"intent": "system.init", "params": {"contract_mode": "user"}},
        headers={"Authorization": f"Bearer {token}"},
    )
    require_ok(status, init_resp, "system.init user")
    data = init_resp.get("data") if isinstance(init_resp.get("data"), dict) else {}
    if isinstance(data.get("data"), dict):
        data = data.get("data") or data

    scenes = data.get("scenes") if isinstance(data.get("scenes"), list) else []
    capabilities = data.get("capabilities") if isinstance(data.get("capabilities"), list) else []

    errors: list[str] = []
    for scene in scenes:
        if _has_demo_semantics(scene):
            scene_key = str(scene.get("code") or scene.get("key") or "").strip()
            errors.append(f"user scene leaked demo semantics: {scene_key or '<unknown>'}")
    for cap in capabilities:
        if _has_demo_semantics(cap):
            cap_key = str(cap.get("key") or "").strip()
            errors.append(f"user capability leaked demo semantics: {cap_key or '<unknown>'}")

    if errors:
        raise RuntimeError(" | ".join(errors[:20]))
    print(f"[scene_demo_leak_guard] PASS login={selected_login} scenes={len(scenes)} capabilities={len(capabilities)}")


if __name__ == "__main__":
    main()
