#!/usr/bin/env python3
"""Replay legacy user context facts into neutral carrier models."""

from __future__ import annotations

import csv
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
        if (candidate / "artifacts/migration/fresh_db_legacy_user_context_replay_adapter_result_v1.json").exists():
            return candidate
    return Path.cwd()


def ensure_allowed_db() -> None:
    allowlist = {item.strip() for item in os.getenv("MIGRATION_REPLAY_DB_ALLOWLIST", "sc_migration_fresh").split(",") if item.strip()}
    if env.cr.dbname not in allowlist:  # noqa: F821
        raise RuntimeError({"db_name_not_allowed_for_replay": env.cr.dbname, "allowlist": sorted(allowlist)})  # noqa: F821


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return [dict(row) for row in csv.DictReader(handle)]


def write_json(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def clean(value: object) -> str:
    return "" if value is None else str(value).strip()


def bool_from_legacy_active(deleted_flag: str, state: str = "") -> bool:
    if clean(deleted_flag) in {"1", "true", "True"}:
        return False
    if clean(state) in {"0", "停用", "禁用"}:
        return False
    return True


REPO_ROOT = repo_root()
ARTIFACT_ROOT = Path(os.getenv("MIGRATION_ARTIFACT_ROOT", str(REPO_ROOT / "artifacts/migration")))
INPUT_MANIFEST = REPO_ROOT / "artifacts/migration/fresh_db_legacy_user_context_replay_adapter_result_v1.json"
DEPARTMENT_CSV = REPO_ROOT / "artifacts/migration/fresh_db_legacy_department_replay_payload_v1.csv"
PROFILE_CSV = REPO_ROOT / "artifacts/migration/fresh_db_legacy_user_profile_replay_payload_v1.csv"
ROLE_CSV = REPO_ROOT / "artifacts/migration/fresh_db_legacy_user_role_replay_payload_v1.csv"
OUTPUT_JSON = ARTIFACT_ROOT / "fresh_db_legacy_user_context_replay_write_result_v1.json"

ensure_allowed_db()
manifest = json.loads(INPUT_MANIFEST.read_text(encoding="utf-8"))
department_rows = read_csv(DEPARTMENT_CSV)
profile_rows = read_csv(PROFILE_CSV)
role_rows = read_csv(ROLE_CSV)

Department = env["sc.legacy.department"].sudo().with_context(active_test=False)  # noqa: F821
Profile = env["sc.legacy.user.profile"].sudo().with_context(active_test=False)  # noqa: F821
Role = env["sc.legacy.user.role"].sudo().with_context(active_test=False)  # noqa: F821
User = env["res.users"].sudo().with_context(active_test=False)  # noqa: F821

users_by_login = {
    rec["login"]: rec["id"]
    for rec in User.search_read(
        [("login", "in", sorted({row["generated_login"] for row in profile_rows if row.get("generated_login")}))],
        ["login"],
    )
}


def collapse_duplicates(model, key_field: str, keys: set[str]) -> int:
    removed = 0
    for key in sorted(key for key in keys if key):
        records = model.search([(key_field, "=", key)], order="id asc")
        if len(records) > 1:
            records[1:].unlink()
            removed += len(records) - 1
    return removed


deduped_departments = collapse_duplicates(
    Department,
    "legacy_department_id",
    {clean(row.get("legacy_department_id")) for row in department_rows},
)
deduped_profiles = collapse_duplicates(
    Profile,
    "legacy_user_id",
    {clean(row.get("legacy_user_id")) for row in profile_rows},
)
deduped_roles = collapse_duplicates(
    Role,
    "legacy_assignment_id",
    {clean(row.get("legacy_assignment_id")) for row in role_rows},
)

department_created = 0
department_updated = 0
department_by_legacy: dict[str, int] = {}
for row in department_rows:
    legacy_id = clean(row["legacy_department_id"])
    vals = {
        "legacy_department_id": legacy_id,
        "name": clean(row["name"]) or legacy_id,
        "parent_legacy_department_id": clean(row.get("parent_legacy_department_id")) or False,
        "depth": clean(row.get("depth")) or False,
        "state": clean(row.get("state")) or False,
        "identity_path": clean(row.get("identity_path")) or False,
        "legacy_project_id": clean(row.get("legacy_project_id")) or False,
        "is_company": clean(row.get("is_company")) or False,
        "is_child_company": clean(row.get("is_child_company")) or False,
        "charge_leader_legacy_user_id": clean(row.get("charge_leader_legacy_user_id")) or False,
        "charge_leader_name": clean(row.get("charge_leader_name")) or False,
        "note": clean(row.get("note")) or False,
        "active": clean(row.get("state")) not in {"0", "停用", "禁用"},
    }
    existing = Department.search([("legacy_department_id", "=", legacy_id)], limit=1)
    if existing:
        existing.write(vals)
        department_updated += 1
        department_by_legacy[legacy_id] = existing.id
    else:
        created = Department.create(vals)
        department_created += 1
        department_by_legacy[legacy_id] = created.id

for row in department_rows:
    legacy_id = clean(row["legacy_department_id"])
    parent_legacy_id = clean(row.get("parent_legacy_department_id"))
    parent_id = department_by_legacy.get(parent_legacy_id)
    if parent_id:
        Department.browse(department_by_legacy[legacy_id]).write({"parent_id": parent_id})

profile_created = 0
profile_updated = 0
profiles_by_legacy: dict[str, int] = {}
for row in profile_rows:
    legacy_id = clean(row["legacy_user_id"])
    user_id = users_by_login.get(clean(row.get("generated_login")))
    vals = {
        "legacy_user_id": legacy_id,
        "user_id": user_id or False,
        "generated_login": clean(row.get("generated_login")) or False,
        "source_login": clean(row.get("source_login")) or False,
        "display_name": clean(row.get("display_name")) or clean(row.get("source_login")) or legacy_id,
        "phone": clean(row.get("phone")) or False,
        "email": clean(row.get("email")) or False,
        "employee_no": clean(row.get("employee_no")) or False,
        "person_state": clean(row.get("person_state")) or False,
        "deleted_flag": clean(row.get("deleted_flag")) or False,
        "locked_flag": clean(row.get("locked_flag")) or False,
        "is_admin_flag": clean(row.get("is_admin_flag")) or False,
        "sex": clean(row.get("sex")) or False,
        "account_type": clean(row.get("account_type")) or False,
        "user_type": clean(row.get("user_type")) or False,
        "legacy_department_id": clean(row.get("legacy_department_id")) or False,
        "department_id": department_by_legacy.get(clean(row.get("legacy_department_id"))) or False,
        "department_name": clean(row.get("department_name")) or False,
        "tr_user_id": clean(row.get("tr_user_id")) or False,
        "tr_user_state": clean(row.get("tr_user_state")) or False,
        "tr_user_operator": clean(row.get("tr_user_operator")) or False,
        "tr_user_job_number": clean(row.get("tr_user_job_number")) or False,
        "source_evidence": clean(row.get("source_evidence")) or False,
        "active": bool_from_legacy_active(row.get("deleted_flag", ""), row.get("tr_user_state", "")),
    }
    existing = Profile.search([("legacy_user_id", "=", legacy_id)], limit=1)
    if existing:
        existing.write(vals)
        profile_updated += 1
        profiles_by_legacy[legacy_id] = existing.id
    else:
        created = Profile.create(vals)
        profile_created += 1
        profiles_by_legacy[legacy_id] = created.id

role_created = 0
role_updated = 0
role_blocked: list[dict[str, str]] = []
for row in role_rows:
    assignment_id = clean(row["legacy_assignment_id"])
    legacy_user_id = clean(row["legacy_user_id"])
    user_id = users_by_login.get(clean(row.get("generated_login")))
    if legacy_user_id and legacy_user_id not in profiles_by_legacy:
        role_blocked.append({"legacy_assignment_id": assignment_id, "legacy_user_id": legacy_user_id, "reason": "missing_user_profile"})
        continue
    vals = {
        "legacy_assignment_id": assignment_id,
        "legacy_user_id": legacy_user_id,
        "user_id": user_id or False,
        "legacy_role_id": clean(row.get("legacy_role_id")),
        "role_name": clean(row.get("role_name")) or False,
        "role_source": clean(row.get("role_source")) or "unknown",
        "company_legacy_id": clean(row.get("company_legacy_id")) or False,
        "source_table": clean(row.get("source_table")) or "unknown",
        "note": clean(row.get("note")) or False,
        "active": True,
    }
    existing = Role.search([("legacy_assignment_id", "=", assignment_id)], limit=1)
    if existing:
        existing.write(vals)
        role_updated += 1
    else:
        Role.create(vals)
        role_created += 1

env.cr.commit()  # noqa: F821
status = "PASS" if len(role_blocked) == 0 else "PASS_WITH_BLOCKED"
payload = {
    "status": status,
    "mode": "fresh_db_legacy_user_context_replay_write",
    "database": env.cr.dbname,  # noqa: F821
    "input_department_rows": len(department_rows),
    "input_profile_rows": len(profile_rows),
    "input_role_rows": len(role_rows),
    "created_departments": department_created,
    "updated_departments": department_updated,
    "created_profiles": profile_created,
    "updated_profiles": profile_updated,
    "created_roles": role_created,
    "updated_roles": role_updated,
    "deduped_departments": deduped_departments,
    "deduped_profiles": deduped_profiles,
    "deduped_roles": deduped_roles,
    "blocked_roles": len(role_blocked),
    "blocked_samples": role_blocked[:50],
    "db_writes": department_created + department_updated + profile_created + profile_updated + role_created + role_updated,
    "adapter_counts": {
        "department_rows": manifest.get("department_rows"),
        "profile_rows": manifest.get("profile_rows"),
        "role_rows": manifest.get("role_rows"),
    },
    "decision": "legacy_user_context_replay_complete" if not role_blocked else "legacy_user_context_replay_with_blocked_roles",
}
write_json(OUTPUT_JSON, payload)
print("FRESH_DB_LEGACY_USER_CONTEXT_REPLAY_WRITE=" + json.dumps(payload, ensure_ascii=False, sort_keys=True))
