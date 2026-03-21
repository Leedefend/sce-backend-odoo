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
REPORT_MD = ROOT / "docs" / "ops" / "audit" / "owner_scene_independent_deploy_report.md"
REPORT_JSON = ROOT / "artifacts" / "backend" / "owner_scene_independent_deploy_report.json"


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
    session = data.get("session") if isinstance(data.get("session"), dict) else {}
    token = str(session.get("token") or data.get("token") or "").strip()
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
        errors.append("login failed for owner scene independent deployment probe")
        token = ""
    base_data = _system_init(intent_url, token) if token else {}
    if not base_data:
        errors.append("system.init baseline payload not available")

    owner_scenes = _extract_list_return(OWNER_SCENE_FILE, "list_owner_scenes")
    owner_caps = _extract_list_return(OWNER_CAP_FILE, "list_owner_capabilities")
    if not owner_scenes:
        errors.append("owner scenes missing")
    if not owner_caps:
        errors.append("owner capabilities missing")

    owner_scene_codes = sorted(
        {
            str(item.get("code") or item.get("key") or "").strip()
            for item in owner_scenes
            if str(item.get("code") or item.get("key") or "").strip()
        }
    )
    owner_cap_keys = sorted(
        {
            str(item.get("key") or "").strip()
            for item in owner_caps
            if str(item.get("key") or "").strip()
        }
    )
    if any(not key.startswith("owner.") for key in owner_scene_codes):
        errors.append("owner scene namespace must start with owner.")
    if any(not key.startswith("owner.") for key in owner_cap_keys):
        errors.append("owner capability namespace must start with owner.")

    simulated = copy.deepcopy(base_data) if isinstance(base_data, dict) else {}
    if isinstance(simulated, dict):
        baseline_keys = sorted(simulated.keys())
        simulated["scenes"] = owner_scenes
        simulated["capabilities"] = owner_caps
        simulated["scene_count"] = len(owner_scenes)
        simulated["capability_count"] = len(owner_caps)
        simulated_keys = sorted(simulated.keys())
        if not baseline_keys:
            warnings.append("baseline keys empty; simulated structure check downgraded")
        elif not set(baseline_keys).issubset(set(simulated_keys)):
            errors.append("simulated payload dropped baseline keys unexpectedly")
    else:
        errors.append("simulated payload invalid")
        baseline_keys = []
        simulated_keys = []

    payload = {
        "ok": len(errors) == 0,
        "summary": {
            "owner_scene_count": len(owner_scenes),
            "owner_capability_count": len(owner_caps),
            "baseline_key_count": len(baseline_keys),
            "simulated_key_count": len(simulated_keys),
            "error_count": len(errors),
            "warning_count": len(warnings),
        },
        "owner_scene_codes": owner_scene_codes,
        "owner_capability_keys": owner_cap_keys,
        "errors": errors,
        "warnings": warnings,
    }
    REPORT_JSON.parent.mkdir(parents=True, exist_ok=True)
    REPORT_JSON.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    lines = [
        "# Owner Scene Independent Deploy Report",
        "",
        f"- owner_scene_count: {payload['summary']['owner_scene_count']}",
        f"- owner_capability_count: {payload['summary']['owner_capability_count']}",
        f"- baseline_key_count: {payload['summary']['baseline_key_count']}",
        f"- simulated_key_count: {payload['summary']['simulated_key_count']}",
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
        print("[owner_scene_independent_deploy_report] FAIL")
        return 2
    print("[owner_scene_independent_deploy_report] PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
