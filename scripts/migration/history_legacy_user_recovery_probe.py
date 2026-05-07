#!/usr/bin/env python3
"""Probe whether legacy user business facts are recoverable in runtime."""

from __future__ import annotations

import json
import os
from pathlib import Path


def repo_root() -> Path:
    env_root = os.getenv("MIGRATION_REPO_ROOT")
    candidates = []
    if env_root:
        candidates.append(Path(env_root))
    candidates.extend([Path("/mnt"), Path.cwd()])
    for candidate in candidates:
        if (candidate / "addons/smart_construction_core/__manifest__.py").exists():
            return candidate
    return Path.cwd()


def artifact_root() -> Path:
    root = Path(os.getenv("MIGRATION_ARTIFACT_ROOT", str(repo_root() / "artifacts/migration")))
    root.mkdir(parents=True, exist_ok=True)
    return root


def count(model_name: str, domain: list[tuple[str, str, object]] | None = None) -> int:
    return env[model_name].sudo().with_context(active_test=False).search_count(domain or [])  # noqa: F821


def sample_login(login: str) -> dict[str, object]:
    Users = env["res.users"].sudo().with_context(active_test=False)  # noqa: F821
    Profile = env["sc.legacy.user.profile"].sudo().with_context(active_test=False)  # noqa: F821
    user = Users.search([("login", "=", login)], limit=1)
    profile = Profile.search([("source_login", "=", login), ("active", "=", True)], limit=1)
    return {
        "login": login,
        "user_id": user.id if user else 0,
        "user_name": user.name if user else "",
        "profile_user_login": profile.user_id.login if profile and profile.user_id else "",
        "role_summary": profile.role_summary if profile else "",
        "department_scope_length": len(profile.department_scope_summary or "") if profile else 0,
        "group_count": len(user.groups_id) if user else 0,
    }


Imd = env["ir.model.data"].sudo()  # noqa: F821
counts = {
    "profiles_total": count("sc.legacy.user.profile"),
    "profiles_active": count("sc.legacy.user.profile", [("active", "=", True)]),
    "profiles_linked_to_user": count("sc.legacy.user.profile", [("user_id", "!=", False)]),
    "roles_total": count("sc.legacy.user.role"),
    "roles_linked_to_user": count("sc.legacy.user.role", [("user_id", "!=", False)]),
    "roles_projected": count("sc.legacy.user.role", [("projection_state", "=", "projected")]),
    "roles_unmapped": count("sc.legacy.user.role", [("projection_state", "=", "unmapped")]),
    "scopes_total": count("sc.legacy.user.project.scope"),
    "scopes_current": count("sc.legacy.user.project.scope", [("scope_state", "=", "current")]),
    "scopes_linked_to_user": count("sc.legacy.user.project.scope", [("user_id", "!=", False)]),
    "scopes_linked_to_project": count("sc.legacy.user.project.scope", [("project_id", "!=", False)]),
    "scopes_current_linked_to_project": count(
        "sc.legacy.user.project.scope",
        [("scope_state", "=", "current"), ("project_id", "!=", False)],
    ),
    "scopes_access_applied": count("sc.legacy.user.project.scope", [("project_access_applied", "=", True)]),
    "legacy_user_xmlids": Imd.search_count(
        [("module", "=", "migration_assets"), ("model", "=", "res.users"), ("name", "like", "legacy_user_sc_%")]
    ),
    "active_internal_users": count("res.users", [("active", "=", True), ("share", "=", False)]),
}

samples = [sample_login(login) for login in ("wutao", "chenshuai", "hujun", "shuiwujingbanren")]
checks = {
    "profiles_imported": counts["profiles_total"] >= 101,
    "profiles_linked": counts["profiles_linked_to_user"] >= 101,
    "legacy_user_assets_imported": counts["legacy_user_xmlids"] >= 101,
    "roles_imported": counts["roles_total"] >= 330,
    "roles_linked": counts["roles_linked_to_user"] >= 330,
    "roles_projected": counts["roles_projected"] >= 250,
    "project_scopes_imported": counts["scopes_total"] >= 90871,
    "project_scopes_user_linked": counts["scopes_linked_to_user"] >= 90871,
    "project_scopes_project_linked": counts["scopes_linked_to_project"] >= 60000,
    "current_project_scope_access_applied": counts["scopes_access_applied"] >= 17000,
    "sample_users_recoverable": all(item["user_id"] and item["profile_user_login"] == item["login"] for item in samples),
}

payload = {
    "status": "PASS" if all(checks.values()) else "FAIL",
    "mode": "history_legacy_user_recovery_probe",
    "database": env.cr.dbname,  # noqa: F821
    "counts": counts,
    "checks": checks,
    "samples": samples,
    "decision": "legacy_user_business_recovery_ready" if all(checks.values()) else "legacy_user_business_recovery_incomplete",
}
output = artifact_root() / "history_legacy_user_recovery_probe_result_v1.json"
output.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print("HISTORY_LEGACY_USER_RECOVERY_PROBE=" + json.dumps(payload, ensure_ascii=False, sort_keys=True))
if payload["status"] != "PASS":
    raise SystemExit(1)
