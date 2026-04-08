#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

import json
import os
from pathlib import Path

from intent_smoke_utils import require_ok
from python_http_smoke_utils import get_base_url, http_post_json


ROOT = Path(__file__).resolve().parents[2]


def _artifacts_dir() -> Path:
    path = Path(str(os.getenv("ARTIFACTS_DIR") or "").strip() or (ROOT / "artifacts"))
    path.mkdir(parents=True, exist_ok=True)
    return path


def _login(intent_url: str, db_name: str, login: str, password: str) -> str:
    status, resp = http_post_json(
        intent_url,
        {"intent": "login", "params": {"db": db_name, "login": login, "password": password}},
        headers={"X-Anonymous-Intent": "1"},
    )
    require_ok(status, resp, "login")
    token = str(((resp.get("data") or {}) if isinstance(resp.get("data"), dict) else {}).get("token") or "").strip()
    if not token:
        raise RuntimeError("missing token")
    return token


def _fetch_surface(intent_url: str, token: str, surface: str) -> tuple[int, dict]:
    status, resp = http_post_json(
        intent_url,
        {
            "intent": "ui.contract",
            "params": {
                "op": "model",
                "model": "project.project",
                "view_type": "form",
                "contract_mode": "user",
                "contract_surface": surface,
            },
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    return status, resp if isinstance(resp, dict) else {}


def _validate_mapping(mapping: dict) -> list[str]:
    errors: list[str] = []
    native_to_governed = mapping.get("native_to_governed") if isinstance(mapping.get("native_to_governed"), dict) else {}
    if not native_to_governed:
        return ["surface_mapping.native_to_governed missing"]
    for key in (
        "fields",
        "layout_fields",
        "layout_nodes",
        "buttons",
        "header_buttons",
        "stat_buttons",
        "field_modifiers",
    ):
        row = native_to_governed.get(key) if isinstance(native_to_governed.get(key), dict) else {}
        if not row:
            errors.append(f"surface_mapping.native_to_governed.{key} missing")
            continue
        if not isinstance(row.get("native_count"), int):
            errors.append(f"{key}.native_count must be int")
        if not isinstance(row.get("governed_count"), int):
            errors.append(f"{key}.governed_count must be int")
        if not isinstance(row.get("removed"), list):
            errors.append(f"{key}.removed must be list")
        if not isinstance(row.get("added"), list):
            errors.append(f"{key}.added must be list")
    return errors


def main() -> int:
    base_url = get_base_url().rstrip("/")
    intent_url = f"{base_url}/api/v1/intent"
    db_name = str(os.getenv("E2E_DB") or os.getenv("DB_NAME") or "").strip()
    login = str(os.getenv("E2E_LOGIN") or "admin").strip()
    password = str(os.getenv("E2E_PASSWORD") or os.getenv("ADMIN_PASSWD") or "admin").strip()
    token = _login(intent_url, db_name, login, password)

    failures: list[str] = []
    report: dict[str, dict] = {}
    for surface in ("native", "user", "hud"):
        status, resp = _fetch_surface(intent_url, token, surface)
        if surface != "native":
            require_ok(status, resp, f"ui.contract.{surface}")

        data = resp.get("data") if isinstance(resp.get("data"), dict) else {}
        meta = resp.get("meta") if isinstance(resp.get("meta"), dict) else {}
        error = resp.get("error") if isinstance(resp.get("error"), dict) else {}

        if surface == "native" and resp.get("ok") is not True:
            error_code = str(error.get("code") or "").strip()
            error_msg = str(error.get("message") or "").strip().lower()
            native_disabled = (
                error_code == "INTERNAL_ERROR"
                and "native ui.contract op is disabled" in error_msg
                and "scene-ready contract" in error_msg
            )
            if native_disabled:
                report[surface] = {
                    "ok": True,
                    "errors": [],
                    "mode": "native_disabled_expected",
                    "status": status,
                    "error_code": error_code,
                }
                continue
            failures.append(f"native: ui.contract request failed status={status} code={error_code}")
            report[surface] = {"ok": False, "errors": ["native request failed"], "status": status}
            continue

        mapping = data.get("surface_mapping") if isinstance(data.get("surface_mapping"), dict) else {}
        errors = _validate_mapping(mapping)
        if surface == "native":
            if data.get("governed_from_native") is not False:
                errors.append("native governed_from_native must be false")
        else:
            if data.get("governed_from_native") is not True:
                errors.append(f"{surface} governed_from_native must be true")
        if str(data.get("contract_surface") or "").strip().lower() != surface:
            errors.append(f"data.contract_surface must be {surface}")
        if str(meta.get("contract_surface") or "").strip().lower() != surface:
            errors.append(f"meta.contract_surface must be {surface}")
        report[surface] = {"ok": not errors, "errors": errors}
        failures.extend([f"{surface}: {e}" for e in errors])

    artifacts = _artifacts_dir() / "backend"
    artifacts.mkdir(parents=True, exist_ok=True)
    out_json = artifacts / "surface_mapping_guard.json"
    out_md = artifacts / "surface_mapping_guard.md"
    payload = {"ok": not failures, "surfaces": report, "failures": failures}
    out_json.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    md = ["# Surface Mapping Guard", "", f"- ok: {payload['ok']}", ""]
    for surface, row in report.items():
        md.append(f"- {surface}: {'PASS' if row.get('ok') else 'FAIL'}")
    if failures:
        md.extend(["", "## Failures", ""])
        md.extend([f"- {item}" for item in failures])
    out_md.write_text("\n".join(md) + "\n", encoding="utf-8")
    print(str(out_json))
    print(str(out_md))
    if failures:
        print("[surface_mapping_guard] FAIL")
        return 1
    print("[surface_mapping_guard] PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
