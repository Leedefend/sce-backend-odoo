#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

import json
import os
import ast
from pathlib import Path

from python_http_smoke_utils import get_base_url, http_post_json


ROOT = Path(__file__).resolve().parents[2]
REPORT_MD = ROOT / "docs" / "ops" / "audit" / "platform_multi_domain_report.md"
REPORT_JSON = ROOT / "artifacts" / "backend" / "platform_multi_domain_report.json"
ICP_KEY = "sc.core.extension_modules"
OWNER_MODULE = "smart_owner_core"
OWNER_SCENE_FILE = ROOT / "addons" / "smart_owner_core" / "services" / "scene_registry_owner.py"


def _login(intent_url: str, db_name: str, login: str, password: str) -> tuple[bool, str, str]:
    status, payload = http_post_json(
        intent_url,
        {"intent": "login", "params": {"db": db_name, "login": login, "password": password}},
        headers={"X-Anonymous-Intent": "1"},
    )
    if status >= 400 or not isinstance(payload, dict) or payload.get("ok") is not True:
        return False, "", f"login failed: {login}"
    data = payload.get("data") if isinstance(payload.get("data"), dict) else {}
    session = data.get("session") if isinstance(data.get("session"), dict) else {}
    token = str(session.get("token") or data.get("token") or "").strip()
    if not token:
        return False, "", f"token missing: {login}"
    return True, token, ""


def _intent(intent_url: str, token: str, intent: str, params: dict, context: dict | None = None) -> tuple[int, dict]:
    payload = {"intent": intent, "params": params}
    if isinstance(context, dict):
        payload["context"] = context
    return http_post_json(intent_url, payload, headers={"Authorization": f"Bearer {token}"})


def _extract_keys(items: list, key: str) -> list[str]:
    out = []
    for item in items or []:
        if not isinstance(item, dict):
            continue
        raw = str(item.get(key) or "").strip()
        if raw:
            out.append(raw)
    return sorted(set(out))


def _extract_nav_scene_keys(nodes: list) -> list[str]:
    keys: set[str] = set()

    def walk(items):
        for node in items or []:
            if not isinstance(node, dict):
                continue
            scene_key = str(node.get("scene_key") or "").strip()
            if scene_key:
                keys.add(scene_key)
            meta = node.get("meta") if isinstance(node.get("meta"), dict) else {}
            meta_scene_key = str(meta.get("scene_key") or "").strip()
            if meta_scene_key:
                keys.add(meta_scene_key)
            walk(node.get("children") if isinstance(node.get("children"), list) else [])

    walk(nodes or [])
    return sorted(keys)


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


def _set_icp(token: str, intent_url: str, value: str, existing_id: int | None) -> tuple[bool, str]:
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
    if status >= 400 or not isinstance(payload, dict) or payload.get("ok") is not True:
        return False, "failed to write sc.core.extension_modules"
    return True, ""


def _with_owner_module(raw: str) -> str:
    parts = [x.strip() for x in str(raw or "").split(",") if x and x.strip()]
    if OWNER_MODULE not in parts:
        parts.append(OWNER_MODULE)
    return ",".join(parts)


def _has_owner_prefix(keys: list[str]) -> bool:
    return any(k.startswith("owner.") for k in keys)


def _only_owner_prefix(keys: list[str]) -> bool:
    return all(k.startswith("owner.") for k in keys) if keys else True


def _call_system_init(intent_url: str, token: str, context: dict | None = None) -> tuple[bool, dict]:
    status, payload = _intent(intent_url, token, "system.init", {"contract_mode": "user"}, context=context)
    if status >= 400 or not isinstance(payload, dict) or payload.get("ok") is not True:
        return False, {}
    data = payload.get("data") if isinstance(payload.get("data"), dict) else {}
    if isinstance(data.get("data"), dict):
        data = data.get("data")
    return True, (data if isinstance(data, dict) else {})


def _extract_owner_scenes_from_file() -> list[str]:
    if not OWNER_SCENE_FILE.is_file():
        return []
    try:
        tree = ast.parse(OWNER_SCENE_FILE.read_text(encoding="utf-8"), filename=str(OWNER_SCENE_FILE))
    except Exception:
        return []
    for node in tree.body:
        if not isinstance(node, ast.FunctionDef) or node.name != "list_owner_scenes":
            continue
        for stmt in node.body:
            if not isinstance(stmt, ast.Return):
                continue
            try:
                value = ast.literal_eval(stmt.value)
            except Exception:
                return []
            if not isinstance(value, list):
                return []
            return sorted(
                {
                    str(item.get("code") or item.get("key") or "").strip()
                    for item in value
                    if isinstance(item, dict) and str(item.get("code") or item.get("key") or "").strip()
                }
            )
    return []


def _surface_snapshot(data: dict) -> dict:
    scenes = data.get("scenes") if isinstance(data.get("scenes"), list) else []
    caps = data.get("capabilities") if isinstance(data.get("capabilities"), list) else []
    nav = data.get("nav") if isinstance(data.get("nav"), list) else []
    intents = data.get("intents") if isinstance(data.get("intents"), list) else []
    return {
        "scene_keys": _extract_keys(scenes, "code"),
        "capability_keys": _extract_keys(caps, "key"),
        "nav_scene_keys": _extract_nav_scene_keys(nav),
        "intent_keys": sorted(
            set(
                str(item.get("intent") or item.get("key") or "").strip()
                for item in intents
                if isinstance(item, dict) and str(item.get("intent") or item.get("key") or "").strip()
            )
        ),
    }


def main() -> int:
    errors: list[str] = []
    warnings: list[str] = []
    base_url = get_base_url()
    intent_url = f"{base_url}/api/v1/intent"
    db_name = str(os.getenv("DB_NAME") or os.getenv("ODOO_DB") or "sc_dev").strip()

    pm_login = str(os.getenv("ROLE_PM_LOGIN") or "demo_role_pm").strip()
    pm_password = str(os.getenv("ROLE_PM_PASSWORD") or "demo").strip()
    owner_login = str(os.getenv("ROLE_OWNER_LOGIN") or "demo_role_owner").strip()
    owner_password = str(os.getenv("ROLE_OWNER_PASSWORD") or "demo").strip()
    admin_login = str(os.getenv("E2E_LOGIN") or "admin").strip()
    admin_password = str(os.getenv("E2E_PASSWORD") or os.getenv("ADMIN_PASSWD") or "admin").strip()

    ok_admin, admin_token, admin_msg = _login(intent_url, db_name, admin_login, admin_password)
    if not ok_admin:
        errors.append(admin_msg or "admin login failed")
    original_icp_id = None
    original_icp_value = ""
    if ok_admin:
        original_icp_id, original_icp_value = _get_icp(admin_token, intent_url)
        target_value = _with_owner_module(original_icp_value)
        ok_set, msg_set = _set_icp(admin_token, intent_url, target_value, original_icp_id)
        if not ok_set:
            errors.append(msg_set)

    snapshots: dict[str, dict] = {}
    try:
        if not errors:
            ok_pm, pm_token, pm_msg = _login(intent_url, db_name, pm_login, pm_password)
            if not ok_pm:
                errors.append(pm_msg or "construction user login failed")
            else:
                ok_data, data = _call_system_init(intent_url, pm_token, context={})
                if not ok_data:
                    errors.append("construction user system.init failed")
                else:
                    snapshots["construction_only"] = _surface_snapshot(data)

            ok_owner, owner_token, owner_msg = _login(intent_url, db_name, owner_login, owner_password)
            if not ok_owner:
                errors.append(owner_msg or "owner user login failed")
            else:
                ok_data, data = _call_system_init(intent_url, owner_token, context={"sc.industry": "owner"})
                if not ok_data:
                    errors.append("owner user system.init failed")
                else:
                    snapshots["owner_only"] = _surface_snapshot(data)

            ok_super, super_token, super_msg = _login(intent_url, db_name, admin_login, admin_password)
            if not ok_super:
                errors.append(super_msg or "super user login failed")
            else:
                ok_default, data_default = _call_system_init(intent_url, super_token, context={})
                ok_owner_ctx, data_owner_ctx = _call_system_init(
                    intent_url, super_token, context={"sc.industry": "owner"}
                )
                if not ok_default or not ok_owner_ctx:
                    errors.append("super user system.init failed")
                else:
                    snapshots["super_default"] = _surface_snapshot(data_default)
                    snapshots["super_owner_ctx"] = _surface_snapshot(data_owner_ctx)

        # Isolation assertions
        construction = snapshots.get("construction_only", {})
        if construction:
            if _has_owner_prefix(construction.get("scene_keys", [])):
                errors.append("construction-only user leaked owner scenes")
            if _has_owner_prefix(construction.get("capability_keys", [])):
                errors.append("construction-only user leaked owner capabilities")
            if _has_owner_prefix(construction.get("nav_scene_keys", [])):
                errors.append("construction-only user leaked owner nav")

        owner_only = snapshots.get("owner_only", {})
        owner_scene_catalog = _extract_owner_scenes_from_file()
        if owner_only:
            if not owner_only.get("scene_keys"):
                warnings.append("owner-only user returned empty scenes")
            if not _only_owner_prefix(owner_only.get("scene_keys", [])):
                warnings.append("owner-only runtime scenes are mixed; validate owner-overlay scene package")
                if not owner_scene_catalog:
                    errors.append("owner overlay scene catalog missing")
                elif not _only_owner_prefix(owner_scene_catalog):
                    errors.append("owner overlay scene catalog contains non-owner scene keys")
            if not owner_only.get("capability_keys"):
                errors.append("owner-only user returned empty capabilities")
            if not _only_owner_prefix(owner_only.get("capability_keys", [])):
                errors.append("owner-only user capabilities are mixed with non-owner domain")
            if not _only_owner_prefix(owner_only.get("nav_scene_keys", [])):
                warnings.append("owner-only nav carries non-owner scene keys (runtime compatibility mode)")

        super_default = snapshots.get("super_default", {})
        super_owner_ctx = snapshots.get("super_owner_ctx", {})
        if super_default and _has_owner_prefix(super_default.get("scene_keys", [])):
            warnings.append("super default payload includes owner scenes")
        if super_owner_ctx:
            if not _only_owner_prefix(super_owner_ctx.get("scene_keys", [])):
                warnings.append("super owner-context scenes are mixed (runtime compatibility mode)")
            if not _only_owner_prefix(super_owner_ctx.get("capability_keys", [])):
                errors.append("super owner-context capabilities are mixed with non-owner domain")
            owner_intents = [k for k in super_owner_ctx.get("intent_keys", []) if k.startswith("owner.")]
            if len(owner_intents) < 2:
                warnings.append("super owner-context intent surface omits owner write intents")
    finally:
        if ok_admin:
            # restore config
            _set_icp(admin_token, intent_url, original_icp_value, original_icp_id)

    payload = {
        "ok": len(errors) == 0,
        "summary": {
            "error_count": len(errors),
            "warning_count": len(warnings),
            "profiles_checked": sorted(list(snapshots.keys())),
            "owner_scene_count": len((snapshots.get("owner_only") or {}).get("scene_keys", [])),
            "owner_capability_count": len((snapshots.get("owner_only") or {}).get("capability_keys", [])),
        },
        "snapshots": snapshots,
        "errors": errors,
        "warnings": warnings,
    }
    REPORT_JSON.parent.mkdir(parents=True, exist_ok=True)
    REPORT_JSON.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    lines = [
        "# Platform Multi-Domain Report",
        "",
        f"- profiles_checked: {', '.join(payload['summary']['profiles_checked']) if payload['summary']['profiles_checked'] else 'none'}",
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
        print("[platform_multi_domain_ready_report] FAIL")
        return 2
    print("[platform_multi_domain_ready_report] PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
