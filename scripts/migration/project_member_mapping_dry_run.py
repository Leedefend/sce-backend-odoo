"""Readonly project_member mapping and permission-safety dry-run."""

from __future__ import annotations

import csv
import json
from collections import Counter
from pathlib import Path


SOURCE_CSV = Path("/mnt/artifacts/migration/project_member_source_shadow_v1.csv")
OUTPUT_JSON = Path("/mnt/artifacts/migration/project_member_dry_run_result_v1.json")
EXPECTED_COUNT = 21390
PLACEHOLDER_USER = "placeholder_user"


def clean(value):
    return ("" if value is None else str(value)).strip()


def read_csv(path):
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        return list(reader.fieldnames or []), [dict(row) for row in reader]


def write_json(path, payload):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def user_indexes(users):
    by_id_text = {}
    by_login = {}
    by_name = {}
    for user in users:
        by_id_text[str(user.id)] = user
        if user.login:
            by_login.setdefault(user.login.strip(), []).append(user)
        if user.name:
            by_name.setdefault(user.name.strip(), []).append(user)
    return by_id_text, by_login, by_name


def map_user(row, by_id_text, by_login, by_name):
    legacy_user_id = clean(row.get("USERID"))
    legacy_user_name = clean(row.get("LRR"))
    if legacy_user_id in by_id_text:
        user = by_id_text[legacy_user_id]
        return user, "odoo_id_text"
    login_matches = by_login.get(legacy_user_id, [])
    if len(login_matches) == 1:
        return login_matches[0], "login"
    name_matches = by_name.get(legacy_user_name, [])
    if len(name_matches) == 1:
        return name_matches[0], "name"
    return None, PLACEHOLDER_USER


def main():
    if env.cr.dbname != "sc_demo":  # noqa: F821
        raise RuntimeError({"db_name_not_sc_demo": env.cr.dbname})  # noqa: F821

    columns, rows = read_csv(SOURCE_CSV)
    required = {"ID", "USERID", "XMID", "XMMC", "LRR"}
    missing_columns = sorted(required - set(columns))
    if missing_columns:
        raise RuntimeError({"missing_project_member_columns": missing_columns})

    project_model = env["project.project"].sudo()  # noqa: F821
    user_model = env["res.users"].sudo()  # noqa: F821
    projects = project_model.search([("legacy_project_id", "!=", False)])
    project_by_legacy = {}
    for project in projects:
        project_by_legacy.setdefault(project.legacy_project_id or "", []).append(project)
    users = user_model.search([("active", "in", [True, False])])
    by_id_text, by_login, by_name = user_indexes(users)

    mapped_users = 0
    unmapped_users = 0
    placeholder_used = 0
    mapped_projects = 0
    unmapped_projects = 0
    duplicate_project_matches = 0
    user_match_modes = Counter()
    sample_rows = []
    unmapped_user_samples = []
    unmapped_project_samples = []
    duplicate_project_samples = []
    pair_counts = Counter()

    for row in rows:
        legacy_member_id = clean(row.get("ID"))
        legacy_project_id = clean(row.get("XMID"))
        project_matches = project_by_legacy.get(legacy_project_id, [])
        user, user_match_mode = map_user(row, by_id_text, by_login, by_name)
        if user:
            mapped_users += 1
        else:
            unmapped_users += 1
            placeholder_used += 1
            if len(unmapped_user_samples) < 50:
                unmapped_user_samples.append({"legacy_member_id": legacy_member_id, "legacy_user_id": clean(row.get("USERID")), "legacy_user_name": clean(row.get("LRR"))})
        user_match_modes[user_match_mode] += 1

        if len(project_matches) == 1:
            mapped_projects += 1
            project = project_matches[0]
        elif len(project_matches) > 1:
            duplicate_project_matches += 1
            project = None
            if len(duplicate_project_samples) < 50:
                duplicate_project_samples.append({"legacy_member_id": legacy_member_id, "legacy_project_id": legacy_project_id, "matches": [item.id for item in project_matches]})
        else:
            unmapped_projects += 1
            project = None
            if len(unmapped_project_samples) < 50:
                unmapped_project_samples.append({"legacy_member_id": legacy_member_id, "legacy_project_id": legacy_project_id, "project_name": clean(row.get("XMMC"))})

        key = (project.id if project else 0, user.id if user else 0, legacy_project_id, clean(row.get("USERID")))
        pair_counts[key] += 1
        if len(sample_rows) < 200:
            sample_rows.append(
                {
                    "legacy_member_id": legacy_member_id,
                    "legacy_project_id": legacy_project_id,
                    "project_id": project.id if project else None,
                    "legacy_user_id": clean(row.get("USERID")),
                    "legacy_user_name": clean(row.get("LRR")),
                    "mapped_user_id": user.id if user else None,
                    "mapped_user_name": user.name if user else PLACEHOLDER_USER,
                    "user_match_mode": user_match_mode,
                }
            )

    duplicate_pairs = sum(1 for count in pair_counts.values() if count > 1)
    authority_impacts = {
        "record_rule": "YES - project_member facts are candidate access truth and can alter project visibility if written",
        "project_visibility": "YES - member bindings may grant or deny project/task visibility",
        "responsibility_logic": "YES - member bindings may affect owner/PM/member responsibility workflows",
        "write_allowed_by_this_batch": False,
    }
    payload = {
        "status": "PASS",
        "mode": "project_member_mapping_permission_dry_run",
        "database": env.cr.dbname,  # noqa: F821
        "input": str(SOURCE_CSV),
        "total": len(rows),
        "mapped_users": mapped_users,
        "unmapped_users": unmapped_users,
        "placeholder_used": placeholder_used,
        "mapped_projects": mapped_projects,
        "unmapped_projects": unmapped_projects,
        "duplicate_project_matches": duplicate_project_matches,
        "duplicate_project_user_pairs": duplicate_pairs,
        "user_match_modes": dict(sorted(user_match_modes.items())),
        "authority_impacts": authority_impacts,
        "unmapped_user_samples": unmapped_user_samples,
        "unmapped_project_samples": unmapped_project_samples,
        "duplicate_project_samples": duplicate_project_samples,
        "sample_rows": sample_rows,
        "next_gate": "screen placeholder-user and record-rule impact before any project_member write",
    }
    if len(rows) != EXPECTED_COUNT:
        payload["status"] = "FAIL"
        payload["row_count_error"] = {"expected": EXPECTED_COUNT, "actual": len(rows)}
    write_json(OUTPUT_JSON, payload)
    env.cr.rollback()  # noqa: F821
    print("PROJECT_MEMBER_DRY_RUN=" + json.dumps({
        "status": payload["status"],
        "total": payload["total"],
        "mapped_users": mapped_users,
        "unmapped_users": unmapped_users,
        "placeholder_used": placeholder_used,
        "mapped_projects": mapped_projects,
        "unmapped_projects": unmapped_projects,
    }, ensure_ascii=False, sort_keys=True))
    if payload["status"] != "PASS":
        raise RuntimeError({"project_member_dry_run_failed": payload.get("row_count_error")})


main()
