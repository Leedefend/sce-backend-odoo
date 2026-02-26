#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

import json
import os
from pathlib import Path

from python_http_smoke_utils import get_base_url, http_post_json


ROOT = Path(__file__).resolve().parents[2]
MENU_SOURCE_JSON = ROOT / "docs" / "product" / "delivery" / "v1" / "delivery_menu_tree_source_v1.json"
ROLE_SOURCE_JSON = ROOT / "docs" / "product" / "delivery" / "v1" / "role_package_source_v1.json"
ROLE_FLOOR_JSON = ROOT / "artifacts" / "backend" / "role_capability_floor_prod_like.json"
REPORT_JSON = ROOT / "artifacts" / "product" / "visibility_filter_verification.json"
REPORT_MD = ROOT / "docs" / "ops" / "audit" / "visibility_filter_verification.md"


def _load(path: Path) -> dict:
    if not path.is_file():
        return {}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}
    return payload if isinstance(payload, dict) else {}


def _norm(v: object) -> str:
    return str(v or "").strip()


def _intent(intent_url: str, token: str | None, intent: str, params: dict, anonymous: bool = False):
    headers = {}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    if anonymous:
        headers["X-Anonymous-Intent"] = "1"
    st, payload = http_post_json(intent_url, {"intent": intent, "params": params}, headers=headers)
    return int(st), payload if isinstance(payload, dict) else {}


def _login(intent_url: str, db_name: str, login: str, password: str) -> str:
    st, body = _intent(
        intent_url,
        None,
        "login",
        {"db": db_name, "login": login, "password": password},
        anonymous=True,
    )
    if st >= 400 or body.get("ok") is not True:
        return ""
    return _norm(((body.get("data") or {}).get("token")))


def _system_init_scenes(intent_url: str, token: str) -> tuple[int, list[str]]:
    st, body = _intent(intent_url, token, "system.init", {"contract_mode": "user"})
    data = body.get("data") if isinstance(body.get("data"), dict) else {}
    raw = data.get("ui_contract_raw") if isinstance(data.get("ui_contract_raw"), dict) else {}
    scenes = raw.get("scenes") if isinstance(raw.get("scenes"), list) else []
    out = []
    for item in scenes:
        if not isinstance(item, dict):
            continue
        key = _norm(item.get("scene_key") or item.get("key"))
        if key:
            out.append(key)
    return st, sorted(set(out))


def main() -> int:
    errors: list[str] = []
    warnings: list[str] = []

    menu_src = _load(MENU_SOURCE_JSON)
    role_src = _load(ROLE_SOURCE_JSON)
    role_floor = _load(ROLE_FLOOR_JSON)

    hidden = sorted({_norm(x) for x in (menu_src.get("hidden_for_delivery_roles") if isinstance(menu_src.get("hidden_for_delivery_roles"), list) else []) if _norm(x)})
    delivery_entries = sorted(
        {
            _norm(x)
            for row in (menu_src.get("menu_tree") if isinstance(menu_src.get("menu_tree"), list) else [])
            if isinstance(row, dict)
            for x in (row.get("entries") if isinstance(row.get("entries"), list) else [])
            if _norm(x)
        }
    )

    role_rows = role_src.get("roles") if isinstance(role_src.get("roles"), list) else []
    role_by_key = {_norm(r.get("role_key")): r for r in role_rows if isinstance(r, dict) and _norm(r.get("role_key"))}
    pm_login = _norm((role_by_key.get("pm") or {}).get("probe_login"))
    admin_login = _norm((role_by_key.get("admin") or {}).get("probe_login"))

    db_name = _norm(os.getenv("DB_NAME") or os.getenv("ODOO_DB") or "sc_dev")
    probe_password = _norm(os.getenv("ROLE_PROBE_PASSWORD") or os.getenv("E2E_PASSWORD") or "")
    live_probe = _norm(os.getenv("VISIBILITY_LIVE_PROBE") or "0") == "1"

    pm_visible = []
    admin_visible = []
    evidence_mode = "policy_projection"
    login_ok = {"pm": False, "admin": False}

    if live_probe and probe_password and pm_login and admin_login:
        try:
            intent_url = f"{get_base_url()}/api/v1/intent"
            pm_token = _login(intent_url, db_name, pm_login, probe_password)
            admin_token = _login(intent_url, db_name, admin_login, probe_password)
            login_ok["pm"] = bool(pm_token)
            login_ok["admin"] = bool(admin_token)
            if pm_token and admin_token:
                _, pm_visible = _system_init_scenes(intent_url, pm_token)
                _, admin_visible = _system_init_scenes(intent_url, admin_token)
                evidence_mode = "live_probe"
            else:
                warnings.append("live_probe_login_failed_fallback_to_policy_projection")
        except Exception:
            warnings.append("live_probe_unavailable_fallback_to_policy_projection")

    if evidence_mode != "live_probe":
        # Policy projection: delivery roles only see delivery entries; admin sees delivery + hidden.
        pm_visible = list(delivery_entries)
        admin_visible = sorted(set(delivery_entries) | set(hidden))

    pm_hidden_leak = sorted([s for s in hidden if s in set(pm_visible)])
    admin_hidden_missing = sorted([s for s in hidden if s not in set(admin_visible)])

    if pm_hidden_leak:
        errors.append(f"pm_hidden_leak_count={len(pm_hidden_leak)}")
    if admin_hidden_missing:
        errors.append(f"admin_hidden_missing_count={len(admin_hidden_missing)}")

    # sanity checks
    if not delivery_entries:
        errors.append("delivery_entries_empty")
    if not hidden:
        warnings.append("hidden_list_empty")

    # role floor presence evidence for projection mode
    floor_rows = role_floor.get("roles") if isinstance(role_floor.get("roles"), list) else []
    floor_logins = {_norm(r.get("login")) for r in floor_rows if isinstance(r, dict)}
    if evidence_mode != "live_probe":
        if pm_login and pm_login not in floor_logins:
            warnings.append(f"pm_login_not_in_role_floor={pm_login}")
        if admin_login and admin_login not in floor_logins:
            warnings.append(f"admin_login_not_in_role_floor={admin_login}")

    payload = {
        "ok": len(errors) == 0,
        "summary": {
            "evidence_mode": evidence_mode,
            "delivery_entry_count": len(delivery_entries),
            "hidden_entry_count": len(hidden),
            "pm_hidden_leak_count": len(pm_hidden_leak),
            "admin_hidden_missing_count": len(admin_hidden_missing),
            "error_count": len(errors),
            "warning_count": len(warnings),
        },
        "roles": {
            "pm": {
                "role_key": "pm",
                "probe_login": pm_login,
                "login_ok": login_ok["pm"],
                "visible_entries": pm_visible,
            },
            "admin": {
                "role_key": "admin",
                "probe_login": admin_login,
                "login_ok": login_ok["admin"],
                "visible_entries": admin_visible,
            },
        },
        "hidden_entries": hidden,
        "delivery_entries": delivery_entries,
        "pm_hidden_leak": pm_hidden_leak,
        "admin_hidden_missing": admin_hidden_missing,
        "errors": errors,
        "warnings": warnings,
    }

    REPORT_JSON.parent.mkdir(parents=True, exist_ok=True)
    REPORT_JSON.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    lines = [
        "# Visibility Filter Verification",
        "",
        f"- evidence_mode: {payload['summary']['evidence_mode']}",
        f"- delivery_entry_count: {payload['summary']['delivery_entry_count']}",
        f"- hidden_entry_count: {payload['summary']['hidden_entry_count']}",
        f"- pm_hidden_leak_count: {payload['summary']['pm_hidden_leak_count']}",
        f"- admin_hidden_missing_count: {payload['summary']['admin_hidden_missing_count']}",
        f"- error_count: {payload['summary']['error_count']}",
        f"- warning_count: {payload['summary']['warning_count']}",
    ]
    REPORT_MD.parent.mkdir(parents=True, exist_ok=True)
    REPORT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")

    print(str(REPORT_MD))
    print(str(REPORT_JSON))
    if errors:
        print("[visibility_filter_verification] FAIL")
        return 2
    print("[visibility_filter_verification] PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
