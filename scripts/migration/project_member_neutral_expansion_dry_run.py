"""Readonly expansion plan for project_member neutral carrier rows."""

from __future__ import annotations

import csv
import json
from collections import Counter, defaultdict
from pathlib import Path


SOURCE_CSV = Path("/mnt/artifacts/migration/project_member_source_shadow_v1.csv")
DRY_RUN_JSON = Path("/mnt/artifacts/migration/project_member_dry_run_result_v1.json")
POST_WRITE_REVIEW_JSON = Path("/mnt/artifacts/migration/project_member_neutral_34_post_write_review_result_v1.json")
OUTPUT_JSON = Path("/mnt/artifacts/migration/project_member_neutral_expansion_plan_v1.json")
RELATION_UNIQUE_SLICE_CSV = Path("/mnt/artifacts/migration/project_member_neutral_expansion_relation_unique_slice_v1.csv")
DUPLICATE_EVIDENCE_SLICE_CSV = Path("/mnt/artifacts/migration/project_member_neutral_expansion_duplicate_relation_evidence_slice_v1.csv")

RUN_ID = "ITER-2026-04-14-0030NX"
TARGET_MODEL = "sc.project.member.staging"
EXPECTED_TOTAL = 21390
RELATION_UNIQUE_LIMIT = 500
DUPLICATE_EVIDENCE_LIMIT = 500


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
        return by_id_text[legacy_user_id], "odoo_id_text"
    login_matches = by_login.get(legacy_user_id, [])
    if len(login_matches) == 1:
        return login_matches[0], "login"
    name_matches = by_name.get(legacy_user_name, [])
    if len(name_matches) == 1:
        return name_matches[0], "name"
    return None, "placeholder_user"


def output_row(row, project, user, user_match_mode, relation_count, already_neutral):
    return {
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
        "relation_key": f"{project.id}:{user.id}",
        "relation_count": relation_count,
        "already_neutral": "yes" if already_neutral else "no",
        "role_fact_status": "missing",
        "recommended_lane": "relation_unique" if relation_count == 1 else "duplicate_relation_evidence",
    }


def main():
    if env.cr.dbname != "sc_demo":  # noqa: F821
        raise RuntimeError({"db_name_not_sc_demo": env.cr.dbname})  # noqa: F821

    dry_run = json.loads(DRY_RUN_JSON.read_text(encoding="utf-8"))
    post_write_review = json.loads(POST_WRITE_REVIEW_JSON.read_text(encoding="utf-8"))
    if dry_run.get("status") != "PASS":
        raise RuntimeError({"project_member_dry_run_not_pass": dry_run.get("status")})
    if post_write_review.get("status") != "ROLLBACK_READY":
        raise RuntimeError({"neutral_34_not_rollback_ready": post_write_review.get("status")})

    columns, rows = read_csv(SOURCE_CSV)
    required_columns = {"ID", "USERID", "XMID", "XMMC", "LRR"}
    missing_columns = sorted(required_columns - set(columns))
    if missing_columns:
        raise RuntimeError({"missing_project_member_columns": missing_columns})

    project_model = env["project.project"].sudo()  # noqa: F821
    user_model = env["res.users"].sudo()  # noqa: F821
    neutral_model = env[TARGET_MODEL].sudo()  # noqa: F821

    project_by_legacy = defaultdict(list)
    for project in project_model.search([("legacy_project_id", "!=", False)]):
        project_by_legacy[project.legacy_project_id or ""].append(project)

    users = user_model.search([("active", "in", [True, False])])
    by_id_text, by_login, by_name = user_indexes(users)
    existing_neutral_legacy_ids = set(neutral_model.search([]).mapped("legacy_member_id"))

    counters = Counter()
    relation_counts = Counter()
    mapped_rows = []
    for row in rows:
        project_matches = project_by_legacy.get(clean(row.get("XMID")), [])
        user, user_match_mode = map_user(row, by_id_text, by_login, by_name)
        if len(project_matches) != 1 or not user:
            if not user:
                counters["placeholder_or_unmapped_user"] += 1
            if len(project_matches) == 0:
                counters["unmapped_project"] += 1
            if len(project_matches) > 1:
                counters["duplicate_project_match"] += 1
            continue
        project = project_matches[0]
        relation_key = (project.id, user.id)
        relation_counts[relation_key] += 1
        mapped_rows.append((row, project, user, user_match_mode, relation_key))

    relation_unique_rows = []
    duplicate_evidence_rows = []
    already_neutral_rows = []
    for row, project, user, user_match_mode, relation_key in mapped_rows:
        legacy_member_id = clean(row.get("ID"))
        already_neutral = legacy_member_id in existing_neutral_legacy_ids
        out = output_row(row, project, user, user_match_mode, relation_counts[relation_key], already_neutral)
        if already_neutral:
            already_neutral_rows.append(out)
            continue
        if relation_counts[relation_key] == 1:
            relation_unique_rows.append(out)
        else:
            duplicate_evidence_rows.append(out)

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
        "relation_key",
        "relation_count",
        "already_neutral",
        "role_fact_status",
        "recommended_lane",
    ]
    relation_unique_slice = relation_unique_rows[:RELATION_UNIQUE_LIMIT]
    duplicate_evidence_slice = duplicate_evidence_rows[:DUPLICATE_EVIDENCE_LIMIT]
    write_csv(RELATION_UNIQUE_SLICE_CSV, fieldnames, relation_unique_slice)
    write_csv(DUPLICATE_EVIDENCE_SLICE_CSV, fieldnames, duplicate_evidence_slice)

    blocking_reasons = []
    if len(rows) != EXPECTED_TOTAL:
        blocking_reasons.append("unexpected_source_row_count")
    if not duplicate_evidence_slice and (relation_unique_rows or duplicate_evidence_rows):
        blocking_reasons.append("no_duplicate_evidence_slice")
    remaining_evidence_rows = len(relation_unique_rows) + len(duplicate_evidence_rows)
    if remaining_evidence_rows == 0:
        recommended_next_gate = "Neutral carrier coverage is complete for all mapped project/user rows; no expansion write remains."
    else:
        recommended_next_gate = (
            "If relation_unique rows exist, write them first. Otherwise open a duplicate-relation evidence carrier write task "
            "that explicitly allows multiple legacy rows per same project/user relation while still avoiding project.responsibility."
        )

    payload = {
        "status": "PASS" if not blocking_reasons else "PASS_WITH_RISK",
        "mode": "project_member_neutral_expansion_dry_run",
        "database": env.cr.dbname,  # noqa: F821
        "run_id": RUN_ID,
        "db_writes": 0,
        "target_model": TARGET_MODEL,
        "source_rows": len(rows),
        "mapped_project_user_rows": len(mapped_rows),
        "already_neutral_rows": len(already_neutral_rows),
        "remaining_relation_unique_rows": len(relation_unique_rows),
        "remaining_duplicate_relation_evidence_rows": len(duplicate_evidence_rows),
        "relation_unique_slice_rows": len(relation_unique_slice),
        "duplicate_relation_evidence_slice_rows": len(duplicate_evidence_slice),
        "distinct_relation_keys": len(relation_counts),
        "duplicate_relation_keys": sum(1 for count in relation_counts.values() if count > 1),
        "blocked_or_unmapped": dict(sorted(counters.items())),
        "role_fact_status": "missing",
        "remaining_evidence_rows": remaining_evidence_rows,
        "recommended_next_gate": recommended_next_gate,
        "artifacts": {
            "relation_unique_slice": str(RELATION_UNIQUE_SLICE_CSV),
            "duplicate_relation_evidence_slice": str(DUPLICATE_EVIDENCE_SLICE_CSV),
        },
        "blocking_reasons": blocking_reasons,
    }
    write_json(OUTPUT_JSON, payload)
    env.cr.rollback()  # noqa: F821
    print("PROJECT_MEMBER_NEUTRAL_EXPANSION_DRY_RUN=" + json.dumps({
        "status": payload["status"],
        "mapped_project_user_rows": payload["mapped_project_user_rows"],
        "already_neutral_rows": payload["already_neutral_rows"],
        "remaining_relation_unique_rows": payload["remaining_relation_unique_rows"],
        "remaining_duplicate_relation_evidence_rows": payload["remaining_duplicate_relation_evidence_rows"],
        "relation_unique_slice_rows": payload["relation_unique_slice_rows"],
        "duplicate_relation_evidence_slice_rows": payload["duplicate_relation_evidence_slice_rows"],
    }, ensure_ascii=False, sort_keys=True))
    if payload["status"] != "PASS":
        raise RuntimeError({"project_member_neutral_expansion_dry_run_risk": blocking_reasons})


main()
