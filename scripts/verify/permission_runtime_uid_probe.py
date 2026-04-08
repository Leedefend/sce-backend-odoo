#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations

import argparse
import json
import sys
import urllib.error
import urllib.request


def _post_json(url: str, payload: dict, headers: dict) -> tuple[int, dict]:
    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json", **headers},
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        body = json.loads(resp.read().decode("utf-8"))
        return int(resp.status), body if isinstance(body, dict) else {}


def _extract_contract_data(payload: dict) -> dict:
    data = payload.get("data") if isinstance(payload.get("data"), dict) else {}
    nested = data.get("data") if isinstance(data.get("data"), dict) else None
    return nested if isinstance(nested, dict) else data


def main() -> int:
    parser = argparse.ArgumentParser(description="Probe ui.contract permission effective rights for runtime uid alignment")
    parser.add_argument("--base-url", default="http://localhost:8069", help="Odoo base url")
    parser.add_argument("--db", required=True, help="Database name")
    parser.add_argument("--login", required=True, help="Login user")
    parser.add_argument("--password", required=True, help="Login password")
    parser.add_argument("--action-id", required=True, type=int, help="Target action id")
    parser.add_argument("--render-profile", default="create", help="ui.contract render_profile")
    parser.add_argument(
        "--fail-on-all-false",
        action="store_true",
        default=True,
        help="Fail when effective rights are all false",
    )
    args = parser.parse_args()

    intent_url = f"{args.base_url.rstrip('/')}/api/v1/intent"

    try:
        status_login, payload_login = _post_json(
            intent_url,
            {
                "intent": "login",
                "params": {"db": args.db, "login": args.login, "password": args.password},
            },
            headers={"X-Anonymous-Intent": "1"},
        )
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as exc:
        print(f"[permission_runtime_uid_probe] FAIL login request error: {exc}")
        return 2

    session = (payload_login.get("data") or {}).get("session") or {}
    token = str(session.get("token") or "").strip()
    if status_login != 200 or not token:
        print("[permission_runtime_uid_probe] FAIL login response invalid")
        print(json.dumps(payload_login, ensure_ascii=False))
        return 2

    try:
        status_contract, payload_contract = _post_json(
            intent_url,
            {
                "intent": "ui.contract",
                "params": {"action_id": args.action_id, "render_profile": args.render_profile},
            },
            headers={"Authorization": f"Bearer {token}"},
        )
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as exc:
        print(f"[permission_runtime_uid_probe] FAIL ui.contract request error: {exc}")
        return 2

    if status_contract != 200:
        print(f"[permission_runtime_uid_probe] FAIL ui.contract status={status_contract}")
        print(json.dumps(payload_contract, ensure_ascii=False))
        return 2

    data = _extract_contract_data(payload_contract)
    permissions = data.get("permissions") if isinstance(data.get("permissions"), dict) else {}
    effective = permissions.get("effective") if isinstance(permissions.get("effective"), dict) else {}
    rights = effective.get("rights") if isinstance(effective.get("rights"), dict) else {}
    head = data.get("head") if isinstance(data.get("head"), dict) else {}
    head_permissions = head.get("permissions") if isinstance(head.get("permissions"), dict) else {}

    normalized_rights = {
        "read": bool(rights.get("read")),
        "write": bool(rights.get("write")),
        "create": bool(rights.get("create")),
        "unlink": bool(rights.get("unlink")),
    }

    all_false = not any(normalized_rights.values())
    aligned_with_head = True
    for key, value in normalized_rights.items():
        if key in head_permissions and bool(head_permissions.get(key)) != value:
            aligned_with_head = False

    result = {
        "ok": True,
        "db": args.db,
        "action_id": args.action_id,
        "render_profile": args.render_profile,
        "effective_rights": normalized_rights,
        "head_permissions": head_permissions,
        "all_false": all_false,
        "aligned_with_head": aligned_with_head,
    }

    if args.fail_on_all_false and all_false:
        result["ok"] = False
        print("[permission_runtime_uid_probe] FAIL effective_rights all false")
        print(json.dumps(result, ensure_ascii=False))
        return 1

    print("[permission_runtime_uid_probe] PASS")
    print(json.dumps(result, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
