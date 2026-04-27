#!/usr/bin/env python3
"""Verify admin and historical admin-like users are separated by semantics."""

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
    candidates.append(Path(f"/tmp/history_admin_semantics/{env.cr.dbname}"))  # noqa: F821
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


def xmlids_for(record) -> list[str]:
    if not record:
        return []
    rows = env["ir.model.data"].sudo().search([("model", "=", record._name), ("res_id", "=", record.id)])  # noqa: F821
    return sorted(rows.mapped("complete_name"))


def row_for(login: str) -> dict[str, object]:
    user = Users.search([("login", "=", login)], limit=1)
    if not user:
        return {"login": login, "exists": False}
    return {
        "id": user.id,
        "login": user.login,
        "name": user.name,
        "exists": True,
        "active": bool(user.active),
        "company": user.company_id.name,
        "xmlids": xmlids_for(user),
        "is_odoo_system": bool(user.has_group("base.group_system")),
        "has_platform_config": bool(user.has_group("smart_construction_core.group_sc_cap_config_admin")),
        "has_business_config": bool(user.has_group("smart_construction_core.group_sc_cap_business_config_admin")),
        "has_internal": bool(user.has_group("smart_construction_core.group_sc_internal_user")),
    }


Users = env["res.users"].sudo().with_context(active_test=False)  # noqa: F821

admin = row_for("admin")
history_admin = row_for("history_system_user_10000000")
old_history_admin = row_for("admin_10000000")

errors = []
if not admin.get("exists"):
    errors.append("admin: missing base technical account")
elif "base.user_admin" not in admin.get("xmlids", []):
    errors.append("admin: not bound to base.user_admin")
elif not admin.get("is_odoo_system") or not admin.get("has_platform_config"):
    errors.append("admin: must remain technical/platform administrator")

if not history_admin.get("exists"):
    errors.append("history_system_user_10000000: missing renamed historical placeholder")
elif history_admin.get("active"):
    errors.append("history_system_user_10000000: must be inactive")
elif history_admin.get("is_odoo_system") or history_admin.get("has_platform_config"):
    errors.append("history_system_user_10000000: must not be platform/system administrator")
elif "migration_assets.legacy_user_sc_10000000" not in history_admin.get("xmlids", []):
    errors.append("history_system_user_10000000: missing legacy XMLID binding")

if old_history_admin.get("exists"):
    errors.append("admin_10000000: old ambiguous login still exists")

payload = {
    "status": "PASS" if not errors else "FAIL",
    "database": env.cr.dbname,  # noqa: F821
    "mode": "history_admin_semantics_probe",
    "db_writes": 0,
    "errors": errors,
    "error_count": len(errors),
    "admin": admin,
    "history_system_user_10000000": history_admin,
    "admin_10000000": old_history_admin,
}

output = artifact_root() / "history_admin_semantics_probe_result_v1.json"
output.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
print("HISTORY_ADMIN_SEMANTICS_PROBE=" + json.dumps(payload, ensure_ascii=False, sort_keys=True))
if errors:
    raise RuntimeError({"history_admin_semantics_errors": errors})
