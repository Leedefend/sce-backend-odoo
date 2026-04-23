"""Readonly gate for duplicate-relation project_member neutral carrier write."""

from __future__ import annotations

import csv
import json
from collections import Counter
from pathlib import Path


EXPANSION_PLAN_JSON = Path("/mnt/artifacts/migration/project_member_neutral_expansion_plan_v1.json")
DUPLICATE_SLICE_CSV = Path("/mnt/artifacts/migration/project_member_neutral_expansion_duplicate_relation_evidence_slice_v1.csv")
OUTPUT_JSON = Path("/mnt/artifacts/migration/project_member_duplicate_relation_write_gate_v1.json")
ROLLBACK_PLAN_CSV = Path("/mnt/artifacts/migration/project_member_duplicate_relation_rollback_plan_v1.csv")

RUN_ID = "ITER-2026-04-14-0030NY"
TARGET_MODEL = "sc.project.member.staging"
EXPECTED_SLICE_ROWS = 500


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
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def main():
    if env.cr.dbname != "sc_demo":  # noqa: F821
        raise RuntimeError({"db_name_not_sc_demo": env.cr.dbname})  # noqa: F821

    expansion_plan = json.loads(EXPANSION_PLAN_JSON.read_text(encoding="utf-8"))
    if expansion_plan.get("status") != "PASS":
        raise RuntimeError({"expansion_plan_not_pass": expansion_plan.get("status")})
    if expansion_plan.get("remaining_relation_unique_rows") != 0:
        raise RuntimeError({"relation_unique_rows_should_be_written_first": expansion_plan.get("remaining_relation_unique_rows")})

    columns, rows = read_csv(DUPLICATE_SLICE_CSV)
    required_columns = {
        "legacy_member_id",
        "legacy_project_id",
        "project_id",
        "legacy_user_id",
        "mapped_user_id",
        "relation_key",
        "relation_count",
        "already_neutral",
        "role_fact_status",
        "recommended_lane",
    }
    blocking_reasons = []
    missing_columns = sorted(required_columns - set(columns))
    if missing_columns:
        blocking_reasons.append({"error": "missing_columns", "columns": missing_columns})
    if len(rows) != EXPECTED_SLICE_ROWS:
        blocking_reasons.append({"error": "slice_row_count_not_500", "rows": len(rows)})

    legacy_ids = [clean(row.get("legacy_member_id")) for row in rows]
    duplicate_legacy_ids = [key for key, count in Counter(legacy_ids).items() if key and count > 1]
    if duplicate_legacy_ids:
        blocking_reasons.append({"error": "duplicate_legacy_member_id", "sample": duplicate_legacy_ids[:20]})

    invalid_rows = []
    relation_counts = Counter()
    for line_no, row in enumerate(rows, start=2):
        line_errors = []
        if clean(row.get("already_neutral")) != "no":
            line_errors.append("already_neutral_not_no")
        if clean(row.get("role_fact_status")) != "missing":
            line_errors.append("role_fact_status_not_missing")
        if clean(row.get("recommended_lane")) != "duplicate_relation_evidence":
            line_errors.append("recommended_lane_not_duplicate_relation_evidence")
        try:
            if int(clean(row.get("relation_count"))) <= 1:
                line_errors.append("relation_count_not_duplicate")
        except ValueError:
            line_errors.append("relation_count_not_integer")
        for field in ["legacy_member_id", "legacy_project_id", "project_id", "legacy_user_id", "mapped_user_id", "relation_key"]:
            if not clean(row.get(field)):
                line_errors.append(f"missing_{field}")
        if line_errors:
            invalid_rows.append({"line": line_no, "legacy_member_id": clean(row.get("legacy_member_id")), "errors": line_errors})
        relation_counts[clean(row.get("relation_key"))] += 1

    if invalid_rows:
        blocking_reasons.append({"error": "invalid_rows", "rows": invalid_rows[:50], "count": len(invalid_rows)})

    model = env[TARGET_MODEL].sudo()  # noqa: F821
    existing_same_legacy = model.search([("legacy_member_id", "in", legacy_ids)])
    if existing_same_legacy:
        blocking_reasons.append({"error": "existing_neutral_legacy_conflict", "ids": existing_same_legacy.ids[:100]})

    project_ids = sorted({int(clean(row.get("project_id"))) for row in rows if clean(row.get("project_id"))})
    user_ids = sorted({int(clean(row.get("mapped_user_id"))) for row in rows if clean(row.get("mapped_user_id"))})
    projects = env["project.project"].sudo().browse(project_ids).exists()  # noqa: F821
    users = env["res.users"].sudo().browse(user_ids).exists()  # noqa: F821
    if len(projects) != len(project_ids):
        blocking_reasons.append({"error": "missing_projects", "project_ids": sorted(set(project_ids) - set(projects.ids))[:50]})
    if len(users) != len(user_ids):
        blocking_reasons.append({"error": "missing_users", "user_ids": sorted(set(user_ids) - set(users.ids))[:50]})

    rollback_rows = [
        {
            "planned_import_batch": RUN_ID,
            "legacy_member_id": clean(row.get("legacy_member_id")),
            "legacy_project_id": clean(row.get("legacy_project_id")),
            "project_id": clean(row.get("project_id")),
            "user_id": clean(row.get("mapped_user_id")),
            "role_fact_status": "missing",
            "planned_action": "create_neutral_evidence_row",
        }
        for row in rows
    ]
    write_csv(
        ROLLBACK_PLAN_CSV,
        ["planned_import_batch", "legacy_member_id", "legacy_project_id", "project_id", "user_id", "role_fact_status", "planned_action"],
        rollback_rows,
    )

    payload = {
        "status": "PASS" if not blocking_reasons else "FAIL",
        "mode": "project_member_duplicate_relation_neutral_write_gate",
        "database": env.cr.dbname,  # noqa: F821
        "run_id": RUN_ID,
        "db_writes": 0,
        "target_model": TARGET_MODEL,
        "slice_rows": len(rows),
        "distinct_relation_keys": len(relation_counts),
        "max_rows_per_relation_key_in_slice": max(relation_counts.values()) if relation_counts else 0,
        "rollback_plan_rows": len(rollback_rows),
        "project_responsibility_writes": 0,
        "permission_or_visibility_semantics": "not_in_scope",
        "blocking_reasons": blocking_reasons,
        "artifacts": {"rollback_plan": str(ROLLBACK_PLAN_CSV)},
    }
    write_json(OUTPUT_JSON, payload)
    env.cr.rollback()  # noqa: F821
    print("PROJECT_MEMBER_DUPLICATE_RELATION_WRITE_GATE=" + json.dumps({
        "status": payload["status"],
        "slice_rows": payload["slice_rows"],
        "distinct_relation_keys": payload["distinct_relation_keys"],
        "rollback_plan_rows": payload["rollback_plan_rows"],
        "db_writes": payload["db_writes"],
    }, ensure_ascii=False, sort_keys=True))
    if blocking_reasons:
        raise RuntimeError({"project_member_duplicate_relation_write_gate_failed": blocking_reasons})


main()
