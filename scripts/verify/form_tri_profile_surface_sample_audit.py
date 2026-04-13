#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any
from urllib.request import Request, urlopen


ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "artifacts" / "contract" / "form_tri_profile_surface_sample_v1.json"
FRONTEND_FORM_FILE = ROOT / "frontend" / "apps" / "web" / "src" / "pages" / "ContractFormPage.vue"


def _jsonrpc_call(base_url: str, path: str, payload: dict[str, Any], cookies: list[str]) -> dict[str, Any]:
    req = Request(
        f"{base_url.rstrip('/')}{path}",
        data=json.dumps({"jsonrpc": "2.0", "method": "call", "params": payload, "id": 1}).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    if cookies:
        req.add_header("Cookie", "; ".join(cookies))
    with urlopen(req, timeout=30) as resp:
        for row in resp.headers.get_all("Set-Cookie") or []:
            cookies.append(row.split(";", 1)[0])
        return json.loads(resp.read().decode("utf-8") or "{}")


def _http_call(base_url: str, path: str, payload: dict[str, Any], cookies: list[str]) -> dict[str, Any]:
    req = Request(
        f"{base_url.rstrip('/')}{path}",
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    if cookies:
        req.add_header("Cookie", "; ".join(cookies))
    with urlopen(req, timeout=30) as resp:
        for row in resp.headers.get_all("Set-Cookie") or []:
            cookies.append(row.split(";", 1)[0])
        return json.loads(resp.read().decode("utf-8") or "{}")


def _fetch_contract(base_url: str, db: str, login: str, password: str, profile: str, action_id: int, record_id: int) -> dict[str, Any]:
    cookies: list[str] = []
    auth = _jsonrpc_call(base_url, "/web/session/authenticate", {"db": db, "login": login, "password": password}, cookies)
    if auth.get("error"):
        raise RuntimeError(f"login failed: {auth['error']}")
    resp = _http_call(
        base_url,
        "/api/v1/intent",
        {
            "intent": "ui.contract",
            "params": {
                "op": "action_open",
                "action_id": int(action_id),
                "view_type": "form",
                "record_id": int(record_id),
                "contract_surface": "user",
                "contract_mode": "default",
                "render_profile": profile,
            },
        },
        cookies,
    )
    if resp.get("ok") is not True:
        raise RuntimeError(f"ui.contract failed for {profile}: {resp}")
    data = resp.get("data") if isinstance(resp.get("data"), dict) else {}
    return data


def _count_actions(surface: dict[str, Any], key: str) -> int:
    actions = (surface.get("actions") if isinstance(surface.get("actions"), dict) else {}).get(key)
    return len(actions) if isinstance(actions, list) else 0


def _frontend_consumer_presence() -> dict[str, bool]:
    text = FRONTEND_FORM_FILE.read_text(encoding="utf-8") if FRONTEND_FORM_FILE.exists() else ""
    return {
        "resolveSurfaceActionRows": "resolveSurfaceActionRows" in text,
        "activeRenderSurface": "activeRenderSurface" in text,
        "one2manyPolicies": "one2manyPolicies" in text,
    }


def run_audit(args: argparse.Namespace) -> dict[str, Any]:
    profiles = ("create", "edit", "readonly")
    payloads: dict[str, dict[str, Any]] = {}
    issues: list[str] = []
    for profile in profiles:
        payloads[profile] = _fetch_contract(
            args.base_url,
            args.db,
            args.login,
            args.password,
            profile,
            args.action_id,
            args.record_id,
        )

    surfaces = {
        profile: (payloads[profile].get("render_surfaces") or {}).get(profile, {})
        for profile in profiles
    }
    for profile in profiles:
        if not isinstance(surfaces[profile], dict) or not surfaces[profile]:
            issues.append(f"MISSING_SURFACE_{profile.upper()}")

    create_header = _count_actions(surfaces["create"], "header_buttons")
    edit_header = _count_actions(surfaces["edit"], "header_buttons")
    readonly_header = _count_actions(surfaces["readonly"], "header_buttons")
    create_stat = _count_actions(surfaces["create"], "stat_buttons")
    edit_stat = _count_actions(surfaces["edit"], "stat_buttons")
    readonly_stat = _count_actions(surfaces["readonly"], "stat_buttons")

    if not (edit_header >= create_header >= readonly_header):
        issues.append("HEADER_ACTION_ORDER_INVALID")
    if create_stat != 0:
        issues.append("CREATE_STAT_EXPECTED_EMPTY")
    if edit_stat < readonly_stat:
        issues.append("EDIT_STAT_EXPECTED_GTE_READONLY")

    consumer = _frontend_consumer_presence()
    if not all(consumer.values()):
        issues.append("FRONTEND_CONSUMER_SWITCH_INCOMPLETE")

    out = {
        "version": "v1",
        "audit": "form_tri_profile_surface_sample",
        "target": {
            "base_url": args.base_url,
            "db": args.db,
            "action_id": args.action_id,
            "record_id": args.record_id,
        },
        "summary": {
            "status": "PASS" if not issues else "BLOCKED",
            "issue_count": len(issues),
        },
        "metrics": {
            "create_header": create_header,
            "edit_header": edit_header,
            "readonly_header": readonly_header,
            "create_stat": create_stat,
            "edit_stat": edit_stat,
            "readonly_stat": readonly_stat,
        },
        "frontend_consumer": consumer,
        "issues": issues,
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(out, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return out


def main() -> int:
    parser = argparse.ArgumentParser(description="Sample verify tri-profile form surfaces and frontend consumer switch.")
    parser.add_argument("--base-url", default="http://127.0.0.1:18081")
    parser.add_argument("--db", default="sc_demo")
    parser.add_argument("--login", default="wutao")
    parser.add_argument("--password", default="demo")
    parser.add_argument("--action-id", type=int, default=531)
    parser.add_argument("--record-id", type=int, default=18)
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--strict", action="store_true")
    args = parser.parse_args()

    payload = run_audit(args)
    if args.json:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        print(f"status={payload['summary']['status']} issue_count={payload['summary']['issue_count']}")
    if args.strict and payload["summary"]["status"] != "PASS":
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
