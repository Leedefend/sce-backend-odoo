#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

import json
import os
from pathlib import Path

from python_http_smoke_utils import get_base_url, http_post_json


ROOT = Path(__file__).resolve().parents[2]
UI_GUIDE = ROOT / "docs" / "product" / "ui_guideline_v1.md"
REPORT_MD = ROOT / "docs" / "ops" / "audit" / "ui_surface_stability_report.md"
REPORT_JSON = ROOT / "artifacts" / "backend" / "ui_surface_stability_report.json"


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
    return http_post_json(payload=payload, url=intent_url, headers={"Authorization": f"Bearer {token}"})


def _shape(data: dict) -> list[str]:
    if isinstance(data.get("data"), dict):
        data = data.get("data")
    if not isinstance(data, dict):
        return []
    return sorted(data.keys())


def main() -> int:
    errors: list[str] = []
    warnings: list[str] = []
    if not UI_GUIDE.is_file():
        errors.append("missing docs/product/ui_guideline_v1.md")

    base_url = get_base_url()
    intent_url = f"{base_url}/api/v1/intent"
    db_name = str(os.getenv("DB_NAME") or os.getenv("ODOO_DB") or "sc_dev").strip()
    login = str(os.getenv("E2E_LOGIN") or "admin").strip()
    password = str(os.getenv("E2E_PASSWORD") or os.getenv("ADMIN_PASSWD") or "admin").strip()
    ok, token = _login(intent_url, db_name, login, password)
    if not ok:
        errors.append("login failed for ui surface stability")
        token = ""

    required_exact = ["user", "nav", "intents", "default_route"]
    required_any = {
        "scenes": ["scenes", "scene_ready_contract_v1"],
        "capabilities": ["capabilities", "released_scene_semantic_surface", "delivery_engine_v1"],
    }
    modes = {
        "default": {},
        "bundle_construction": {"sc.bundle": "construction"},
        "bundle_owner": {"sc.bundle": "owner", "sc.industry": "owner"},
    }
    shapes = {}

    if token:
        for mode, context in modes.items():
            status, payload = _intent(intent_url, token, "system.init", {"contract_mode": "user"}, context=context)
            if status >= 400 or not isinstance(payload, dict) or payload.get("ok") is not True:
                errors.append(f"system.init failed in mode={mode}")
                continue
            data = payload.get("data") if isinstance(payload.get("data"), dict) else {}
            keys = _shape(data)
            shapes[mode] = keys
            key_set = set(keys)
            for key in required_exact:
                if key not in key_set:
                    errors.append(f"mode={mode} missing required surface key: {key}")
            for semantic_key, alternatives in required_any.items():
                if not any(candidate in key_set for candidate in alternatives):
                    errors.append(
                        f"mode={mode} missing required surface semantic: {semantic_key} (any of {alternatives})"
                    )

    if shapes.get("default") and shapes.get("bundle_owner"):
        if shapes["default"] != shapes["bundle_owner"]:
            warnings.append("bundle_owner differs from default shape (allowed if additive)")

    payload = {
        "ok": len(errors) == 0,
        "summary": {
            "mode_count": len(shapes),
            "error_count": len(errors),
            "warning_count": len(warnings),
        },
        "shapes": shapes,
        "errors": errors,
        "warnings": warnings,
    }
    REPORT_JSON.parent.mkdir(parents=True, exist_ok=True)
    REPORT_JSON.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    lines = [
        "# UI Surface Stability Report",
        "",
        f"- mode_count: {len(shapes)}",
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
        print("[ui_surface_stability_ready] FAIL")
        return 2
    print("[ui_surface_stability_ready] PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
