#!/usr/bin/env python3
"""Verify wutao has business configuration capability without platform admin power."""

from __future__ import annotations

import json
import os
from pathlib import Path


def artifact_root() -> Path:
    candidates = []
    env_root = os.getenv("MIGRATION_ARTIFACT_ROOT")
    if env_root:
        candidates.append(Path(env_root))
    candidates.append(Path("/mnt/artifacts/migration"))
    candidates.append(Path(f"/tmp/history_real_user_business_config/{env.cr.dbname}"))  # noqa: F821
    for root in candidates:
        try:
            root.mkdir(parents=True, exist_ok=True)
            probe = root / ".write_probe"
            probe.write_text("ok\n", encoding="utf-8")
            probe.unlink()
            return root
        except Exception:
            continue
    raise RuntimeError({"artifact_root_unavailable": [str(path) for path in candidates]})


def menu_path(menu) -> str:
    names = []
    current = menu
    while current:
        names.append(current.name)
        current = current.parent_id
    return " / ".join(reversed(names))


Users = env["res.users"].sudo().with_context(active_test=False)  # noqa: F821
Menu = env["ir.ui.menu"].sudo()  # noqa: F821

user = Users.search([("login", "=", "wutao")], limit=1)
business_config_group = env.ref(  # noqa: F821
    "smart_construction_core.group_sc_cap_business_config_admin",
    raise_if_not_found=False,
)
platform_config_group = env.ref("smart_construction_core.group_sc_cap_config_admin", raise_if_not_found=False)  # noqa: F821

business_config_menus = []
system_config_menus = []
if user:
    visible_ids = Menu.with_user(user)._visible_menu_ids(debug=False)
    for menu in Menu.browse(visible_ids):
        path = menu_path(menu)
        if "业务配置" in path:
            business_config_menus.append(path)
        if "系统配置" in path:
            system_config_menus.append(path)

payload = {
    "status": "PASS",
    "database": env.cr.dbname,  # noqa: F821
    "mode": "history_wutao_business_config_probe",
    "db_writes": 0,
    "user": {
        "exists": bool(user),
        "id": user.id if user else False,
        "login": user.login if user else "",
        "name": user.name if user else "",
        "active": bool(user.active) if user else False,
        "company": user.company_id.name if user else "",
        "has_internal": bool(user and user.has_group("smart_construction_core.group_sc_internal_user")),
        "has_business_config": bool(user and business_config_group and business_config_group in user.groups_id),
        "has_platform_config": bool(user and platform_config_group and platform_config_group in user.groups_id),
        "is_system": bool(user and user.has_group("base.group_system")),
        "business_config_menu_count": len(business_config_menus),
        "business_config_menus": sorted(business_config_menus),
        "system_config_menu_count": len(system_config_menus),
        "system_config_menus": sorted(system_config_menus),
    },
}

errors = []
if not user:
    errors.append("wutao: missing user")
elif not user.active:
    errors.append("wutao: inactive user")
elif not payload["user"]["has_business_config"]:
    errors.append("wutao: missing business configuration capability")
elif payload["user"]["has_platform_config"] or payload["user"]["is_system"]:
    errors.append("wutao: must not have platform/system administrator capability")
elif not business_config_menus:
    errors.append("wutao: business configuration menus are not visible")

if errors:
    payload["status"] = "FAIL"
payload["errors"] = errors
payload["error_count"] = len(errors)

output = artifact_root() / "history_wutao_business_config_probe_result_v1.json"
output.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
print("HISTORY_WUTAO_BUSINESS_CONFIG_PROBE=" + json.dumps(payload, ensure_ascii=False, sort_keys=True))
if errors:
    raise RuntimeError({"history_wutao_business_config_errors": errors})
