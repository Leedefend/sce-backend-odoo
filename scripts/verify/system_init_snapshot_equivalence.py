#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

import difflib
import json
import os
from pathlib import Path

from intent_smoke_utils import require_ok
from python_http_smoke_utils import get_base_url, http_post_json

ART_DIR = Path("artifacts/backend")
JSON_OUT = ART_DIR / "system_init_snapshot_equivalence.json"
MD_OUT = ART_DIR / "system_init_snapshot_equivalence.md"

VOLATILE_KEYS = {
    "elapsed_ms",
    "latency_ms",
    "trace_id",
    "etag",
    "timings",
    "timings_ms",
    "total_ms",
}


def _login(intent_url: str, db_name: str, login: str, password: str) -> str:
    status, resp = http_post_json(
        intent_url,
        {"intent": "login", "params": {"db": db_name, "login": login, "password": password}},
        headers={"X-Anonymous-Intent": "1"},
    )
    require_ok(status, resp, "login")
    data = (resp or {}).get("data") or {}
    token = data.get("token")
    if not token and isinstance(data.get("session"), dict):
        token = data.get("session", {}).get("token")
    if not token:
        raise RuntimeError("login missing token")
    return str(token)


def _request_system_init(intent_url: str, token: str, mode: str) -> dict:
    status, resp = http_post_json(
        intent_url,
        {"intent": "system.init", "params": {"contract_mode": mode}},
        headers={"Authorization": f"Bearer {token}"},
    )
    require_ok(status, resp, f"system.init[{mode}]")
    return resp


def _normalize(obj):
    if isinstance(obj, dict):
        out = {}
        for k in sorted(obj.keys()):
            if k in VOLATILE_KEYS:
                continue
            out[k] = _normalize(obj[k])
        return out
    if isinstance(obj, list):
        return [_normalize(x) for x in obj]
    return obj


def _as_text(obj: dict) -> str:
    return json.dumps(obj, ensure_ascii=False, sort_keys=True, indent=2)


def _compare(a: dict, b: dict, label: str) -> dict:
    na = _normalize(a)
    nb = _normalize(b)
    same = na == nb
    diff_preview = []
    if not same:
        al = _as_text(na).splitlines()
        bl = _as_text(nb).splitlines()
        diff_preview = list(difflib.unified_diff(al, bl, fromfile=f"{label}.first", tofile=f"{label}.second", lineterm=""))[:200]
    return {
        "label": label,
        "equal": same,
        "diff_preview": diff_preview,
    }


def main() -> None:
    ART_DIR.mkdir(parents=True, exist_ok=True)

    base_url = get_base_url()
    intent_url = f"{base_url}/api/v1/intent"
    db_name = os.getenv("E2E_DB") or os.getenv("DB_NAME") or ""
    login = os.getenv("E2E_LOGIN") or "admin"
    password = os.getenv("E2E_PASSWORD") or os.getenv("ADMIN_PASSWD") or "admin"

    token = _login(intent_url, db_name, login, password)

    user_1 = _request_system_init(intent_url, token, "user")
    user_2 = _request_system_init(intent_url, token, "user")
    hud_1 = _request_system_init(intent_url, token, "hud")
    hud_2 = _request_system_init(intent_url, token, "hud")

    checks = [
        _compare(user_1, user_2, "system.init.user"),
        _compare(hud_1, hud_2, "system.init.hud"),
    ]

    failed = [c for c in checks if not c.get("equal")]
    result = {
        "ok": not failed,
        "checks": checks,
        "db": db_name,
        "login": login,
    }
    JSON_OUT.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")

    lines = [
        "# System Init Snapshot Equivalence",
        "",
        f"- ok: `{str(result['ok']).lower()}`",
        f"- db: `{db_name}`",
        f"- login: `{login}`",
        "",
    ]
    for item in checks:
        lines.append(f"## {item['label']}")
        lines.append(f"- equal: `{str(item['equal']).lower()}`")
        if item.get("diff_preview"):
            lines.append("- diff_preview:")
            lines.append("```diff")
            lines.extend(item["diff_preview"])
            lines.append("```")
        lines.append("")
    MD_OUT.write_text("\n".join(lines), encoding="utf-8")

    print(str(JSON_OUT.resolve()))
    print(str(MD_OUT.resolve()))

    if failed:
        labels = ", ".join(x["label"] for x in failed)
        raise RuntimeError(f"system.init snapshot equivalence failed: {labels}")

    print("[system_init_snapshot_equivalence] PASS")


if __name__ == "__main__":
    main()
