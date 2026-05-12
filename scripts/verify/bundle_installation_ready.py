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
REPORT_MD = ROOT / "docs" / "ops" / "audit" / "bundle_installation_report.md"
REPORT_JSON = ROOT / "artifacts" / "backend" / "bundle_installation_report.json"


def _list_return(path: Path, fn_name: str) -> list[dict]:
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
    return data.get("data") if isinstance(data.get("data"), dict) else data


def _keys(d: dict) -> list[str]:
    return sorted(d.keys()) if isinstance(d, dict) else []


def _bundle_fact(bundle_name: str, scenes: list, caps: list) -> dict:
    return {"name": f"smart_{bundle_name}_bundle", "scenes": scenes, "capabilities": caps}


def _set_bundle_fact(payload: dict, bundle_name: str, scenes: list, caps: list) -> dict:
    out = copy.deepcopy(payload)
    ext_facts = out.get("ext_facts") if isinstance(out.get("ext_facts"), dict) else {}
    product = ext_facts.get("product") if isinstance(ext_facts.get("product"), dict) else {}
    product["bundle"] = _bundle_fact(bundle_name, scenes, caps)
    ext_facts["product"] = product
    out["ext_facts"] = ext_facts
    return out


def _remove_bundle_fact(payload: dict) -> dict:
    out = copy.deepcopy(payload)
    ext_facts = out.get("ext_facts") if isinstance(out.get("ext_facts"), dict) else {}
    product = ext_facts.get("product") if isinstance(ext_facts.get("product"), dict) else {}
    product.pop("bundle", None)
    if product:
        ext_facts["product"] = product
    else:
        ext_facts.pop("product", None)
    if ext_facts:
        out["ext_facts"] = ext_facts
    else:
        out.pop("ext_facts", None)
    return out


def _extract_bundle(bundle_name: str) -> dict:
    if bundle_name == "construction":
        base = ROOT / "addons" / "smart_construction_bundle" / "services" / "bundle_registry.py"
    else:
        base = ROOT / "addons" / "smart_owner_bundle" / "services" / "bundle_registry.py"
    scenes = _list_return(base, "list_bundle_scenes")
    caps = _list_return(base, "list_bundle_capabilities")
    return {"scenes": scenes, "capabilities": caps}


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
        errors.append("login failed for bundle installation check")
        token = ""
    baseline = _system_init(intent_url, token) if token else {}
    if not baseline:
        errors.append("system.init baseline unavailable")

    bundle_result = {}
    baseline_keys = _keys(baseline)
    for bundle in ("construction", "owner"):
        ext = _extract_bundle(bundle)
        scenes = ext.get("scenes") if isinstance(ext.get("scenes"), list) else []
        caps = ext.get("capabilities") if isinstance(ext.get("capabilities"), list) else []
        if not scenes or not caps:
            errors.append(f"{bundle} bundle registry incomplete")
            continue
        enabled = _set_bundle_fact(baseline, bundle, scenes, caps)
        disabled = _remove_bundle_fact(enabled)
        enabled_extra_keys = [key for key in _keys(enabled) if key not in baseline_keys]
        disabled_extra_keys = [key for key in _keys(disabled) if key not in baseline_keys]
        missing_after_disabled = [key for key in baseline_keys if key not in _keys(disabled)]
        allowed_extra_keys = {"ext_facts"}
        if baseline_keys and (set(enabled_extra_keys) - allowed_extra_keys):
            errors.append(f"{bundle} bundle added unsupported top-level keys: {','.join(enabled_extra_keys)}")
        if baseline_keys and (disabled_extra_keys or missing_after_disabled):
            errors.append(f"{bundle} bundle disabled payload does not return to baseline shape")
        bundle_result[bundle] = {
            "scene_count": len(scenes),
            "capability_count": len(caps),
            "enabled_shape_keys": _keys(enabled),
            "disabled_shape_keys": _keys(disabled),
            "enabled_extra_keys": enabled_extra_keys,
            "disabled_extra_keys": disabled_extra_keys,
            "missing_after_disabled": missing_after_disabled,
        }

    payload = {
        "ok": len(errors) == 0,
        "summary": {
            "baseline_shape_count": len(baseline_keys),
            "error_count": len(errors),
            "warning_count": len(warnings),
        },
        "bundles": bundle_result,
        "errors": errors,
        "warnings": warnings,
    }
    REPORT_JSON.parent.mkdir(parents=True, exist_ok=True)
    REPORT_JSON.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    lines = [
        "# Bundle Installation Report",
        "",
        f"- baseline_shape_count: {len(baseline_keys)}",
        f"- error_count: {len(errors)}",
        f"- warning_count: {len(warnings)}",
        "",
        "## Bundles",
        "",
    ]
    for name, row in bundle_result.items():
        lines.append(f"- {name}: scenes={row['scene_count']}, capabilities={row['capability_count']}")
    if not bundle_result:
        lines.append("- none")
    lines.extend(["", "## Errors", ""])
    if errors:
        for item in errors:
            lines.append(f"- {item}")
    else:
        lines.append("- none")
    REPORT_MD.parent.mkdir(parents=True, exist_ok=True)
    REPORT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")

    print(str(REPORT_MD))
    print(str(REPORT_JSON))
    if errors:
        print("[bundle_installation_ready] FAIL")
        return 2
    print("[bundle_installation_ready] PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
