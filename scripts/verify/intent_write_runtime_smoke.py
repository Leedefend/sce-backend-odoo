#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

from python_http_smoke_utils import get_base_url, http_post_json


ROOT = Path(__file__).resolve().parents[2]
OUT_JSON = ROOT / "artifacts" / "backend" / "intent_write_runtime_smoke.json"

FORBIDDEN_CODES = {"permission_denied", "forbidden", "access_denied"}
TARGETS = [
    {
        "intent": "api.data.create",
        "params": {
            "model": "project.project",
            "values": {"name": "intent_write_runtime_smoke"},
            "dry_run": True,
        },
    },
    {
        "intent": "execute_button",
        "params": {
            "model": "project.project",
            "button": {"name": "action_view_tasks", "type": "object"},
            "res_id": 0,
            "dry_run": True,
        },
    },
    {
        "intent": "payment.request.submit",
        "params": {
            "id": 0,
        },
    },
    {
        "intent": "scene.governance.rollback",
        "params": {"reason": "intent_write_runtime_smoke"},
    },
]


def _intent_post(intent_url: str, *, token: str | None, intent: str, params: dict | None = None) -> tuple[int, dict]:
    headers: dict[str, str] = {}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    else:
        headers["X-Anonymous-Intent"] = "1"
    return http_post_json(intent_url, {"intent": intent, "params": params or {}}, headers=headers)


def _try_login(intent_url: str, db_name: str, login: str, password: str) -> tuple[bool, str, dict]:
    status, payload = _intent_post(
        intent_url,
        token=None,
        intent="login",
        params={"db": db_name, "login": login, "password": password},
    )
    if status >= 400 or not isinstance(payload, dict) or payload.get("ok") is not True:
        return False, "", payload if isinstance(payload, dict) else {}
    data = payload.get("data") if isinstance(payload.get("data"), dict) else {}
    token = str(data.get("token") or "").strip()
    return bool(token), token, payload


def _as_int(value: Any, default: int = 0) -> int:
    try:
        return int(value)
    except Exception:
        return default


def _reason_code(payload: dict) -> str:
    if not isinstance(payload, dict):
        return ""
    err = payload.get("error")
    if isinstance(err, dict):
        code = str(err.get("reason_code") or err.get("code") or "").strip().lower()
        if code:
            return code
    return ""


def _is_forbidden(status: int, payload: dict) -> bool:
    code = _as_int(payload.get("code"), 0) if isinstance(payload, dict) else 0
    reason = _reason_code(payload)
    return status in {401, 403} or code in {401, 403} or reason in FORBIDDEN_CODES


def _is_server_error(status: int, payload: dict) -> bool:
    code = _as_int(payload.get("code"), 0) if isinstance(payload, dict) else 0
    return status >= 500 or code >= 500


def _resolve_probe_users(intent_url: str, db_name: str) -> list[dict[str, str]]:
    candidate_logins = [
        str(os.getenv("E2E_LOGIN") or "").strip(),
        str(os.getenv("E2E_DENY_LOGIN") or "").strip(),
        "admin",
        "sc_fx_pm",
        "sc_fx_finance",
        "sc_fx_executive",
        "sc_fx_contract_admin",
        "sc_fx_material_user",
        "sc_fx_cost_user",
        "demo",
    ]
    candidate_passwords = [
        str(os.getenv("E2E_PASSWORD") or "").strip(),
        str(os.getenv("E2E_DENY_PASSWORD") or "").strip(),
        str(os.getenv("E2E_PROD_LIKE_PASSWORD") or "").strip(),
        str(os.getenv("ADMIN_PASSWD") or "").strip(),
        "prod_like",
        "admin",
    ]
    users: list[dict[str, str]] = []
    seen_login: set[str] = set()
    tried: set[tuple[str, str]] = set()

    for login in candidate_logins:
        if not login or login in seen_login:
            continue
        for password in candidate_passwords:
            if not password:
                continue
            key = (login, password)
            if key in tried:
                continue
            tried.add(key)
            ok, token, _ = _try_login(intent_url, db_name, login, password)
            if not ok:
                continue
            users.append({"login": login, "token": token})
            seen_login.add(login)
            break
    return users


def main() -> int:
    base_url = get_base_url()
    db_name = str(os.getenv("DB_NAME") or os.getenv("ODOO_DB") or "sc_dev").strip()
    intent_url = f"{base_url}/api/v1/intent"
    failures: list[str] = []

    probe_users = _resolve_probe_users(intent_url, db_name)
    if len(probe_users) < 2:
        print("[intent_write_runtime_smoke] FAIL: need at least two probe users")
        print("hint: set E2E_LOGIN/E2E_PASSWORD and E2E_DENY_LOGIN/E2E_DENY_PASSWORD")
        return 2

    checks: list[dict[str, Any]] = []
    for target in TARGETS:
        intent = target["intent"]
        params = target["params"]
        runs: list[dict[str, Any]] = []
        auth_forbidden_logins: list[str] = []
        auth_allowed_logins: list[str] = []
        for user in probe_users:
            status, payload = _intent_post(intent_url, token=user["token"], intent=intent, params=params)
            forbidden = _is_forbidden(status, payload)
            server_error = _is_server_error(status, payload)
            if server_error:
                failures.append(
                    f"{intent}: server error for {user['login']} status={status} code={payload.get('code')}"
                )
            if forbidden:
                auth_forbidden_logins.append(user["login"])
            else:
                auth_allowed_logins.append(user["login"])
            runs.append(
                {
                    "login": user["login"],
                    "status": status,
                    "payload_code": _as_int(payload.get("code"), 0),
                    "reason_code": _reason_code(payload),
                    "forbidden": forbidden,
                }
            )

        anon_status, anon_payload = _intent_post(intent_url, token=None, intent=intent, params=params)
        anon_forbidden = _is_forbidden(anon_status, anon_payload)
        if _is_server_error(anon_status, anon_payload):
            failures.append(
                f"{intent}: anonymous probe must not be 500-level, got status={anon_status} code={anon_payload.get('code')}"
            )
        if not anon_forbidden:
            failures.append(
                f"{intent}: anonymous probe expected forbidden, got status={anon_status} code={anon_payload.get('code')}"
            )
        if not auth_allowed_logins:
            failures.append(f"{intent}: no allowed authenticated user found in runtime probes")

        checks.append(
            {
                "intent": intent,
                "auth_forbidden_logins": auth_forbidden_logins,
                "auth_allowed_logins": auth_allowed_logins,
                "anonymous_probe": {
                    "status": anon_status,
                    "payload_code": _as_int(anon_payload.get("code"), 0),
                    "reason_code": _reason_code(anon_payload),
                    "forbidden": anon_forbidden,
                },
                "runs": runs,
            }
        )

    report = {
        "ok": len(failures) == 0,
        "summary": {
            "target_count": len(TARGETS),
            "failure_count": len(failures),
            "probe_user_count": len(probe_users),
            "probe_logins": [item["login"] for item in probe_users],
            "intent_url": intent_url,
            "db_name": db_name,
        },
        "checks": checks,
        "errors": failures,
    }
    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(str(OUT_JSON))
    print(
        f"[intent_write_runtime_smoke] targets={len(TARGETS)} failures={len(failures)} "
        f"probe_users={len(probe_users)}"
    )
    if failures:
        for msg in failures:
            print(f"- {msg}")
        print("[intent_write_runtime_smoke] FAIL")
        return 2
    print("[intent_write_runtime_smoke] PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
