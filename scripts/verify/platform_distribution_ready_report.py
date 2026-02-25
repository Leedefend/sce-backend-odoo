#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

import ast
import copy
import json
import os
from pathlib import Path

from python_http_smoke_utils import get_base_url, http_post_json


ROOT = Path(__file__).resolve().parents[2]
OWNER_SCENE_FILE = ROOT / "addons" / "smart_owner_core" / "services" / "scene_registry_owner.py"
OWNER_CAP_FILE = ROOT / "addons" / "smart_owner_core" / "services" / "capability_registry_owner.py"
REPORT_MD = ROOT / "docs" / "ops" / "audit" / "platform_distribution_report.md"
REPORT_JSON = ROOT / "artifacts" / "backend" / "platform_distribution_report.json"


def _extract_list_return(path: Path, fn_name: str) -> list[dict]:
    if not path.is_file():
        return []
    try:
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    except Exception:
        return []
    for node in tree.body:
        if not isinstance(node, ast.FunctionDef) or node.name != fn_name:
            continue
        for stmt in node.body:
            if isinstance(stmt, ast.Return):
                try:
                    value = ast.literal_eval(stmt.value)
                except Exception:
                    return []
                if isinstance(value, list):
                    return [item for item in value if isinstance(item, dict)]
    return []


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


def _system_init(intent_url: str, token: str) -> dict:
    status, payload = http_post_json(
        intent_url,
        {"intent": "system.init", "params": {"contract_mode": "user"}},
        headers={"Authorization": f"Bearer {token}"},
    )
    if status >= 400 or not isinstance(payload, dict) or payload.get("ok") is not True:
        return {}
    data = payload.get("data") if isinstance(payload.get("data"), dict) else {}
    if isinstance(data.get("data"), dict):
        data = data.get("data")
    return data if isinstance(data, dict) else {}


def _scene_codes(scenes: list[dict]) -> list[str]:
    return sorted(
        {
            str(item.get("code") or item.get("key") or "").strip()
            for item in scenes
            if isinstance(item, dict) and str(item.get("code") or item.get("key") or "").strip()
        }
    )


def _cap_keys(capabilities: list[dict]) -> list[str]:
    return sorted(
        {
            str(item.get("key") or "").strip()
            for item in capabilities
            if isinstance(item, dict) and str(item.get("key") or "").strip()
        }
    )


def main() -> int:
    errors: list[str] = []
    warnings: list[str] = []
    base_url = get_base_url()
    intent_url = f"{base_url}/api/v1/intent"
    db_name = str(os.getenv("DB_NAME") or os.getenv("ODOO_DB") or "sc_dev").strip()
    login = str(os.getenv("E2E_LOGIN") or "admin").strip()
    password = str(os.getenv("E2E_PASSWORD") or os.getenv("ADMIN_PASSWD") or "admin").strip()

    ok, token = _login(intent_url, db_name, login, password)
    if not ok:
        errors.append("login failed for distribution readiness probe")
        token = ""
    baseline = _system_init(intent_url, token) if token else {}
    if not baseline:
        errors.append("system.init baseline unavailable")

    owner_scenes = _extract_list_return(OWNER_SCENE_FILE, "list_owner_scenes")
    owner_caps = _extract_list_return(OWNER_CAP_FILE, "list_owner_capabilities")
    if not owner_scenes or not owner_caps:
        errors.append("owner distribution package payload missing")

    baseline_keys = sorted(baseline.keys()) if isinstance(baseline, dict) else []
    enabled_payload = copy.deepcopy(baseline) if isinstance(baseline, dict) else {}
    enabled_payload["scenes"] = owner_scenes
    enabled_payload["capabilities"] = owner_caps
    if "scene_count" in enabled_payload:
        enabled_payload["scene_count"] = len(owner_scenes)
    if "capability_count" in enabled_payload:
        enabled_payload["capability_count"] = len(owner_caps)
    enabled_keys = sorted(enabled_payload.keys())

    disabled_payload = copy.deepcopy(enabled_payload)
    disabled_payload["scenes"] = baseline.get("scenes", [])
    disabled_payload["capabilities"] = baseline.get("capabilities", [])
    if "scene_count" in disabled_payload:
        disabled_payload["scene_count"] = len(disabled_payload["scenes"])
    if "capability_count" in disabled_payload:
        disabled_payload["capability_count"] = len(disabled_payload["capabilities"])
    disabled_keys = sorted(disabled_payload.keys())

    if baseline_keys and (baseline_keys != enabled_keys or baseline_keys != disabled_keys):
        errors.append("payload shape changed during distribution enable/disable simulation")

    owner_scene_codes = _scene_codes(owner_scenes)
    owner_capability_keys = _cap_keys(owner_caps)
    if any(not code.startswith("owner.") for code in owner_scene_codes):
        errors.append("owner scene namespace must start with owner.")
    if any(not key.startswith("owner.") for key in owner_capability_keys):
        errors.append("owner capability namespace must start with owner.")

    residual_owner_after_disable = [
        code for code in _scene_codes(disabled_payload.get("scenes", [])) if code.startswith("owner.")
    ]
    if residual_owner_after_disable:
        errors.append("owner scene residue detected after disable simulation")

    payload = {
        "ok": len(errors) == 0,
        "summary": {
            "baseline_scene_count": len(_scene_codes(baseline.get("scenes", []) if isinstance(baseline, dict) else [])),
            "baseline_capability_count": len(_cap_keys(baseline.get("capabilities", []) if isinstance(baseline, dict) else [])),
            "owner_scene_count": len(owner_scene_codes),
            "owner_capability_count": len(owner_capability_keys),
            "error_count": len(errors),
            "warning_count": len(warnings),
        },
        "shape_keys": {
            "baseline": baseline_keys,
            "enabled": enabled_keys,
            "disabled": disabled_keys,
        },
        "errors": errors,
        "warnings": warnings,
    }
    REPORT_JSON.parent.mkdir(parents=True, exist_ok=True)
    REPORT_JSON.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    lines = [
        "# Platform Distribution Report",
        "",
        f"- baseline_scene_count: {payload['summary']['baseline_scene_count']}",
        f"- baseline_capability_count: {payload['summary']['baseline_capability_count']}",
        f"- owner_scene_count: {payload['summary']['owner_scene_count']}",
        f"- owner_capability_count: {payload['summary']['owner_capability_count']}",
        f"- error_count: {payload['summary']['error_count']}",
        f"- warning_count: {payload['summary']['warning_count']}",
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
        print("[platform_distribution_ready_report] FAIL")
        return 2
    print("[platform_distribution_ready_report] PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
