#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import urllib.request
from http.cookiejar import CookieJar


def _env(name: str, default: str = "") -> str:
    return str(os.getenv(name, default) or "").strip()


class SessionClient:
    def __init__(self, base_url: str):
        self.base_url = base_url.rstrip("/")
        self.opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(CookieJar()))

    def post(self, path: str, payload: dict, headers: dict | None = None) -> tuple[int, dict]:
        request = urllib.request.Request(
            f"{self.base_url}{path}",
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json", **(headers or {})},
            method="POST",
        )
        with self.opener.open(request, timeout=30) as response:
            body = json.loads(response.read().decode("utf-8"))
            return int(response.status), body

    def authenticate(self, db_name: str, login: str, password: str) -> int:
        status, body = self.post(
            "/web/session/authenticate",
            {
                "jsonrpc": "2.0",
                "method": "call",
                "params": {"db": db_name, "login": login, "password": password},
                "id": 1,
            },
        )
        if status != 200:
            return 0
        result = body.get("result") if isinstance(body, dict) else {}
        return int((result or {}).get("uid") or 0)


def _authenticate_with_fallback(
    base_url: str,
    db_name: str,
    logins: list[str],
    passwords: list[str],
) -> tuple[SessionClient | None, int, str, str]:
    for login in logins:
        normalized_login = str(login or "").strip()
        if not normalized_login:
            continue
        for password in passwords:
            normalized_password = str(password or "").strip()
            if not normalized_password:
                continue
            probe = SessionClient(base_url)
            uid = probe.authenticate(db_name, normalized_login, normalized_password)
            if uid > 0:
                return probe, uid, normalized_login, normalized_password
    return None, 0, "", ""


def _extract_home_blocks(data: dict) -> list[dict]:
    rows = data.get("home_blocks")
    if isinstance(rows, list):
        return rows
    ext_facts = data.get("ext_facts") if isinstance(data.get("ext_facts"), dict) else {}
    module_facts = ext_facts.get("smart_construction_core") if isinstance(ext_facts.get("smart_construction_core"), dict) else {}
    rows = module_facts.get("home_blocks")
    return rows if isinstance(rows, list) else []


def _resolve_effective_blocks(rows: list[dict], role_code: str) -> list[str]:
    normalized_role = str(role_code or "").strip().lower()
    blocks: list[str] = []
    for item in rows:
        if not isinstance(item, dict):
            continue
        code = str(item.get("role_code") or "").strip().lower()
        if code not in {"__global__", normalized_role}:
            continue
        values = item.get("blocks") if isinstance(item.get("blocks"), list) else []
        for value in values:
            block_key = str(value or "").strip()
            if block_key and block_key not in blocks:
                blocks.append(block_key)
    return blocks


def _resolve_available_scene_keys(data: dict) -> set[str]:
    available: set[str] = set()
    role_surface = data.get("role_surface") if isinstance(data.get("role_surface"), dict) else {}
    scene_candidates = role_surface.get("scene_candidates") if isinstance(role_surface.get("scene_candidates"), list) else []
    for value in scene_candidates:
        key = str(value or "").strip()
        if key:
            available.add(key)

    scene_ready = data.get("scene_ready_contract_v1") if isinstance(data.get("scene_ready_contract_v1"), dict) else {}
    scenes = scene_ready.get("scenes") if isinstance(scene_ready.get("scenes"), list) else []
    for row in scenes:
        if not isinstance(row, dict):
            continue
        scene_value = row.get("scene")
        if isinstance(scene_value, dict):
            scene_key = str(scene_value.get("key") or scene_value.get("scene_key") or "").strip()
        else:
            scene_key = str(scene_value or "").strip()

        page_value = row.get("page")
        if isinstance(page_value, dict):
            page_key = str(page_value.get("key") or page_value.get("scene_key") or "").strip()
        else:
            page_key = str(page_value or "").strip()
        if scene_key:
            available.add(scene_key)
        if page_key:
            available.add(page_key)
    return available


def main() -> None:
    base_url = _env("E2E_BASE_URL", "http://localhost:8069")
    db_name = _env("DB_NAME", "sc_test")
    outsider_login = _env("ROLE_OUTSIDER_LOGIN", "sc_fx_pure_outsider")

    roles = [
        ("admin", ["admin"], ["admin"]),
        ("pm", ["sc_fx_pm", "demo_role_pm"], ["demo", "prod_like", "admin"]),
        ("finance", ["sc_fx_finance", "demo_role_finance"], ["demo", "prod_like", "admin"]),
        ("outsider", [outsider_login], ["demo", "prod_like", "admin"]),
    ]

    failures: list[str] = []
    details: list[str] = []

    for role, logins, passwords in roles:
        client, uid, used_login, _ = _authenticate_with_fallback(base_url, db_name, logins, passwords)
        if not client:
            failures.append(f"{role}: auth failed")
            continue

        status, body = client.post(
            "/api/v1/intent",
            {"intent": "system.init", "params": {"contract_mode": "user", "with_preload": True}},
            headers={"X-Anonymous-Intent": "1"},
        )
        if status != 200 or not isinstance(body, dict) or body.get("ok") is not True:
            failures.append(f"{role}: system.init failed status={status}")
            continue
        data = body.get("data") if isinstance(body.get("data"), dict) else {}
        role_surface = data.get("role_surface") if isinstance(data.get("role_surface"), dict) else {}
        role_code = str(role_surface.get("role_code") or "").strip()
        home_blocks = _extract_home_blocks(data)
        effective_blocks = _resolve_effective_blocks(home_blocks, role_code)
        available_scenes = _resolve_available_scene_keys(data)
        matched = [item for item in effective_blocks if item in available_scenes]

        if role == "admin" and not effective_blocks:
            failures.append("admin: effective home blocks missing")
        if effective_blocks and not matched:
            failures.append(f"{role}: no block matched available scenes")

        details.append(
            f"{role}:uid={uid},login={used_login},role_code={role_code or '-'},blocks={len(effective_blocks)},matched={len(matched)}"
        )

    if failures:
        raise SystemExit("[native_business_admin_config_home_block_clickpath_verify] FAIL " + "; ".join(failures))

    print("[native_business_admin_config_home_block_clickpath_verify] PASS " + " | ".join(details))


if __name__ == "__main__":
    main()
