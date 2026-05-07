#!/usr/bin/env python3
"""Project legacy user visible profile fields onto runtime user accounts."""

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


def ensure_allowed_db() -> None:
    allowlist = {
        item.strip()
        for item in os.getenv("MIGRATION_REPLAY_DB_ALLOWLIST", "sc_migration_fresh").split(",")
        if item.strip()
    }
    if env.cr.dbname not in allowlist:  # noqa: F821
        raise RuntimeError({"db_name_not_allowed_for_user_profile_runtime_projection": env.cr.dbname, "allowlist": sorted(allowlist)})  # noqa: F821


def clean(value: object) -> str:
    if value is None or value is False:
        return ""
    text = str(value).strip()
    return "" if text.lower() == "false" else text


def should_skip_profile(profile, user) -> bool:
    return clean(user.login) == "history_system_user_10000000"


ensure_allowed_db()

Profile = env["sc.legacy.user.profile"].sudo().with_context(active_test=False)  # noqa: F821
Users = env["res.users"].sudo().with_context(active_test=False)  # noqa: F821

profiles = Profile.search([("user_id", "!=", False)])
updated = []
unchanged = 0
blocked = []
for profile in profiles:
    user = profile.user_id.with_context(active_test=False)
    if not user.exists():
        blocked.append({"profile_id": profile.id, "legacy_user_id": profile.legacy_user_id, "reason": "missing_runtime_user"})
        continue
    if should_skip_profile(profile, user):
        unchanged += 1
        continue
    vals = {}
    if clean(profile.display_name) and clean(profile.display_name) != clean(user.name):
        vals["name"] = clean(profile.display_name)
    if "phone" in Users._fields and clean(profile.phone) and clean(profile.phone) != clean(user.phone):
        vals["phone"] = clean(profile.phone)
    elif "phone" in Users._fields and not clean(profile.phone) and clean(user.phone).lower() == "false":
        vals["phone"] = False
    if "mobile" in Users._fields and clean(profile.phone) and clean(profile.phone) != clean(user.mobile):
        vals["mobile"] = clean(profile.phone)
    elif "mobile" in Users._fields and not clean(profile.phone) and clean(user.mobile).lower() == "false":
        vals["mobile"] = False
    if clean(profile.email) and clean(profile.email).lower() != clean(user.email).lower():
        vals["email"] = clean(profile.email).lower()
    elif not clean(profile.email) and clean(user.email).lower() == "false":
        vals["email"] = False
    if not vals:
        unchanged += 1
        continue
    before = {
        "name": clean(user.name),
        "phone": clean(getattr(user, "phone", "")),
        "mobile": clean(getattr(user, "mobile", "")),
        "email": clean(user.email),
    }
    user.write(vals)
    updated.append(
        {
            "user_id": user.id,
            "login": user.login,
            "legacy_user_id": profile.legacy_user_id,
            "profile_id": profile.id,
            "before": before,
            "after": {
                "name": vals.get("name", before["name"]),
                "phone": vals.get("phone", before["phone"]),
                "mobile": vals.get("mobile", before["mobile"]),
                "email": vals.get("email", before["email"]),
            },
        }
    )

env.cr.commit()  # noqa: F821
payload = {
    "status": "PASS" if not blocked else "PASS_WITH_BLOCKED",
    "mode": "history_user_profile_runtime_projection_write",
    "database": env.cr.dbname,  # noqa: F821
    "input_profiles": len(profiles),
    "updated_users": len(updated),
    "unchanged_users": unchanged,
    "blocked": len(blocked),
    "blocked_samples": blocked[:20],
    "updated_samples": updated[:20],
    "decision": "legacy_user_visible_profile_projected_to_runtime_user",
}
output = artifact_root() / "history_user_profile_runtime_projection_write_result_v1.json"
output.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print("HISTORY_USER_PROFILE_RUNTIME_PROJECTION_WRITE=" + json.dumps(payload, ensure_ascii=False, sort_keys=True))
