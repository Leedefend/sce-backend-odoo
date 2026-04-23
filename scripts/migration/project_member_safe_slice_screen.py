"""Readonly project_member placeholder screening and safe-slice selection."""

from __future__ import annotations

import csv
import json
from collections import Counter
from pathlib import Path


SOURCE_CSV = Path("/mnt/artifacts/migration/project_member_source_shadow_v1.csv")
DRY_RUN_JSON = Path("/mnt/artifacts/migration/project_member_dry_run_result_v1.json")
OUTPUT_JSON = Path("/mnt/artifacts/migration/project_member_placeholder_screen_result_v1.json")
SAFE_SLICE_CSV = Path("/mnt/artifacts/migration/project_member_no_placeholder_safe_slice_v1.csv")
EXPECTED_COUNT = 21390
SAFE_SLICE_LIMIT = 100


def clean(value):
    return ("" if value is None else str(value)).strip()


def read_csv(path):
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        return list(reader.fieldnames or []), [dict(row) for row in reader]


def write_json(path, payload):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def write_csv(path, fieldnames, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


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
    return None, "placeholder_user"


def main():
    if env.cr.dbname != "sc_demo":  # noqa: F821
        raise RuntimeError({"db_name_not_sc_demo": env.cr.dbname})  # noqa: F821

    dry_run = json.loads(DRY_RUN_JSON.read_text(encoding="utf-8"))
    if dry_run.get("status") != "PASS":
        raise RuntimeError({"dry_run_not_pass": dry_run.get("status")})

    _columns, rows = read_csv(SOURCE_CSV)
    project_model = env["project.project"].sudo()  # noqa: F821
    user_model = env["res.users"].sudo()  # noqa: F821
    projects = project_model.search([("legacy_project_id", "!=", False)])
    project_by_legacy = {}
    for project in projects:
        project_by_legacy.setdefault(project.legacy_project_id or "", []).append(project)
    users = user_model.search([("active", "in", [True, False])])
    by_id_text, by_login, by_name = user_indexes(users)

    counters = Counter()
    safe_candidates = []
    placeholder_samples = []
    duplicate_pair_counts = Counter()
    for row in rows:
        project_matches = project_by_legacy.get(clean(row.get("XMID")), [])
        user, user_match_mode = map_user(row, by_id_text, by_login, by_name)
        if len(project_matches) == 1:
            counters["mapped_project"] += 1
            project = project_matches[0]
        elif len(project_matches) > 1:
            counters["duplicate_project_match"] += 1
            project = None
        else:
            counters["unmapped_project"] += 1
            project = None

        if user:
            counters["mapped_user"] += 1
        else:
            counters["placeholder_user"] += 1
            if len(placeholder_samples) < 100:
                placeholder_samples.append(
                    {
                        "legacy_member_id": clean(row.get("ID")),
                        "legacy_project_id": clean(row.get("XMID")),
                        "legacy_user_id": clean(row.get("USERID")),
                        "legacy_user_name": clean(row.get("LRR")),
                    }
                )

        if project and user:
            pair_key = (project.id, user.id)
            duplicate_pair_counts[pair_key] += 1
            safe_candidates.append(
                {
                    "legacy_member_id": clean(row.get("ID")),
                    "legacy_project_id": clean(row.get("XMID")),
                    "project_id": project.id,
                    "project_name": project.name or "",
                    "legacy_user_id": clean(row.get("USERID")),
                    "legacy_user_name": clean(row.get("LRR")),
                    "mapped_user_id": user.id,
                    "mapped_user_name": user.name or "",
                    "user_match_mode": user_match_mode,
                    "source_project_name": clean(row.get("XMMC")),
                }
            )

    unique_safe_candidates = [
        item for item in safe_candidates
        if duplicate_pair_counts[(item["project_id"], item["mapped_user_id"])] == 1
    ]
    safe_slice = unique_safe_candidates[:SAFE_SLICE_LIMIT]
    if not safe_slice:
        raise RuntimeError({"no_safe_slice_candidates": True})

    fieldnames = [
        "legacy_member_id",
        "legacy_project_id",
        "project_id",
        "project_name",
        "legacy_user_id",
        "legacy_user_name",
        "mapped_user_id",
        "mapped_user_name",
        "user_match_mode",
        "source_project_name",
    ]
    write_csv(SAFE_SLICE_CSV, fieldnames, safe_slice)
    duplicate_project_user_pairs = sum(1 for count in duplicate_pair_counts.values() if count > 1)
    payload = {
        "status": "PASS",
        "mode": "project_member_placeholder_screen_no_placeholder_safe_slice",
        "database": env.cr.dbname,  # noqa: F821
        "input": str(SOURCE_CSV),
        "total": len(rows),
        "mapped_projects": counters["mapped_project"],
        "unmapped_projects": counters["unmapped_project"],
        "duplicate_project_matches": counters["duplicate_project_match"],
        "mapped_users": counters["mapped_user"],
        "placeholder_user": counters["placeholder_user"],
        "safe_candidates": len(safe_candidates),
        "unique_safe_candidates": len(unique_safe_candidates),
        "duplicate_project_user_pairs": duplicate_project_user_pairs,
        "safe_slice_rows": len(safe_slice),
        "safe_slice": str(SAFE_SLICE_CSV),
        "placeholder_policy": "block write; do not materialize placeholder_user rows",
        "placeholder_samples": placeholder_samples,
        "next_gate": "L3 bounded write may use only no-placeholder safe slice after explicit write task",
    }
    if len(rows) != EXPECTED_COUNT:
        payload["status"] = "FAIL"
        payload["row_count_error"] = {"expected": EXPECTED_COUNT, "actual": len(rows)}
    write_json(OUTPUT_JSON, payload)
    env.cr.rollback()  # noqa: F821
    print("PROJECT_MEMBER_SAFE_SLICE_SCREEN=" + json.dumps({
        "status": payload["status"],
        "total": payload["total"],
        "mapped_users": payload["mapped_users"],
        "placeholder_user": payload["placeholder_user"],
        "safe_candidates": payload["safe_candidates"],
        "unique_safe_candidates": payload["unique_safe_candidates"],
        "safe_slice_rows": payload["safe_slice_rows"],
    }, ensure_ascii=False, sort_keys=True))
    if payload["status"] != "PASS":
        raise RuntimeError({"project_member_safe_slice_screen_failed": payload.get("row_count_error")})


main()
