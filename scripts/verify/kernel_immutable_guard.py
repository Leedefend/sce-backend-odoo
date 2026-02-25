#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path

from python_http_smoke_utils import get_base_url, http_post_json


ROOT = Path(__file__).resolve().parents[2]
SMART_CORE_ROOT = ROOT / "addons" / "smart_core"
REPORT_MD = ROOT / "docs" / "ops" / "audit" / "kernel_immutable_report.md"
REPORT_JSON = ROOT / "artifacts" / "backend" / "kernel_immutable_report.json"
ICP_KEY = "sc.core.extension_modules"
OWNER_MODULE = "smart_owner_core"


def _dir_hash(root: Path) -> str:
    h = hashlib.sha256()
    for path in sorted(root.rglob("*")):
        if not path.is_file():
            continue
        rel = str(path.relative_to(root)).replace("\\", "/")
        h.update(rel.encode("utf-8"))
        h.update(b"\0")
        h.update(path.read_bytes())
        h.update(b"\0")
    return h.hexdigest()


def _login(intent_url: str, db_name: str, login: str, password: str) -> tuple[bool, str]:
    status, payload = http_post_json(
        intent_url,
        {"intent": "login", "params": {"db": db_name, "login": login, "password": password}},
        headers={"X-Anonymous-Intent": "1"},
    )
    if status >= 400 or not isinstance(payload, dict) or payload.get("ok") is not True:
        return False, ""
    data = payload.get("data") if isinstance(payload.get("data"), dict) else {}
    token = str(data.get("token") or "").strip()
    return bool(token), token


def _intent(intent_url: str, token: str, intent: str, params: dict, context: dict | None = None) -> tuple[int, dict]:
    payload = {"intent": intent, "params": params}
    if isinstance(context, dict):
        payload["context"] = context
    return http_post_json(intent_url, payload, headers={"Authorization": f"Bearer {token}"})


def _get_icp(token: str, intent_url: str) -> tuple[int | None, str]:
    status, payload = _intent(
        intent_url,
        token,
        "api.data",
        {
            "op": "list",
            "model": "ir.config_parameter",
            "fields": ["id", "key", "value"],
            "domain": [["key", "=", ICP_KEY]],
            "limit": 1,
        },
    )
    if status >= 400 or not isinstance(payload, dict) or payload.get("ok") is not True:
        return None, ""
    data = payload.get("data") if isinstance(payload.get("data"), dict) else {}
    rows = data.get("records") if isinstance(data.get("records"), list) else []
    if not rows:
        return None, ""
    row = rows[0] if isinstance(rows[0], dict) else {}
    try:
        rid = int(row.get("id") or 0)
    except Exception:
        rid = 0
    return (rid if rid > 0 else None), str(row.get("value") or "")


def _set_icp(token: str, intent_url: str, value: str, existing_id: int | None) -> bool:
    if existing_id:
        status, payload = _intent(
            intent_url,
            token,
            "api.data",
            {
                "op": "write",
                "model": "ir.config_parameter",
                "ids": [existing_id],
                "vals": {"value": value},
            },
        )
    else:
        status, payload = _intent(
            intent_url,
            token,
            "api.data",
            {
                "op": "create",
                "model": "ir.config_parameter",
                "vals": {"key": ICP_KEY, "value": value},
            },
        )
    return status < 400 and isinstance(payload, dict) and payload.get("ok") is True


def _with_owner_module(raw: str) -> str:
    parts = [x.strip() for x in str(raw or "").split(",") if x and x.strip()]
    if OWNER_MODULE not in parts:
        parts.append(OWNER_MODULE)
    return ",".join(parts)


def main() -> int:
    errors: list[str] = []
    warnings: list[str] = []

    before_hash = _dir_hash(SMART_CORE_ROOT)
    base_url = get_base_url()
    intent_url = f"{base_url}/api/v1/intent"
    db_name = str(os.getenv("DB_NAME") or os.getenv("ODOO_DB") or "sc_dev").strip()
    login = str(os.getenv("E2E_LOGIN") or "admin").strip()
    password = str(os.getenv("E2E_PASSWORD") or os.getenv("ADMIN_PASSWD") or "admin").strip()

    ok, token = _login(intent_url, db_name, login, password)
    if not ok:
        errors.append("login failed")
        token = ""

    original_id = None
    original_value = ""
    if token:
        original_id, original_value = _get_icp(token, intent_url)
        enabled_value = _with_owner_module(original_value)
        if not _set_icp(token, intent_url, enabled_value, original_id):
            errors.append("enable owner extension modules failed")
        else:
            status_owner, payload_owner = _intent(
                intent_url,
                token,
                "system.init",
                {"contract_mode": "user"},
                context={"sc.industry": "owner"},
            )
            if status_owner >= 400 or not isinstance(payload_owner, dict):
                errors.append("system.init owner context failed during immutable guard")
            if not _set_icp(token, intent_url, original_value, original_id):
                errors.append("restore extension modules failed")

    after_hash = _dir_hash(SMART_CORE_ROOT)
    if before_hash != after_hash:
        errors.append("smart_core source hash changed after owner pack enable/disable flow")

    payload = {
        "ok": len(errors) == 0,
        "summary": {
            "before_hash": before_hash,
            "after_hash": after_hash,
            "hash_equal": before_hash == after_hash,
            "error_count": len(errors),
            "warning_count": len(warnings),
        },
        "errors": errors,
        "warnings": warnings,
    }
    REPORT_JSON.parent.mkdir(parents=True, exist_ok=True)
    REPORT_JSON.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    lines = [
        "# Kernel Immutable Guard Report",
        "",
        f"- hash_equal: {payload['summary']['hash_equal']}",
        f"- before_hash: {before_hash}",
        f"- after_hash: {after_hash}",
        f"- error_count: {len(errors)}",
        f"- warning_count: {len(warnings)}",
        "",
        "## Errors",
        "",
    ]
    if errors:
        for item in errors:
            lines.append(f"- {item}")
    else:
        lines.append("- none")
    lines.extend(["", "## Warnings", ""])
    if warnings:
        for item in warnings:
            lines.append(f"- {item}")
    else:
        lines.append("- none")
    REPORT_MD.parent.mkdir(parents=True, exist_ok=True)
    REPORT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")

    print(str(REPORT_MD))
    print(str(REPORT_JSON))
    if errors:
        print("[kernel_immutable_guard] FAIL")
        return 2
    print("[kernel_immutable_guard] PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
