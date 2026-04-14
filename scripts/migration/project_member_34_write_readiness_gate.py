"""Readonly write-readiness gate for project_member 34-row safe slice."""

from __future__ import annotations

import csv
import json
from collections import Counter
from pathlib import Path


SAFE_SLICE_CSV = Path("/mnt/artifacts/migration/project_member_no_placeholder_safe_slice_v1.csv")
SOURCE_SHADOW_CSV = Path("/mnt/artifacts/migration/project_member_source_shadow_v1.csv")
SCREEN_RESULT_JSON = Path("/mnt/artifacts/migration/project_member_placeholder_screen_result_v1.json")
OUTPUT_JSON = Path("/mnt/artifacts/migration/project_member_34_write_readiness_result_v1.json")

EXPECTED_COUNT = 34
TARGET_MODEL = "project.responsibility"
ROLE_FIELD = "role_key"
RUN_ID = "ITER-2026-04-14-0030W"


def clean(value):
    return ("" if value is None else str(value)).replace("\r\n", "\n").replace("\r", "\n").strip()


def read_csv(path):
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        return list(reader.fieldnames or []), [dict(row) for row in reader]


def write_json(path, payload):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def main():
    if env.cr.dbname != "sc_demo":  # noqa: F821
        raise RuntimeError({"db_name_not_sc_demo": env.cr.dbname})  # noqa: F821

    model = env[TARGET_MODEL].sudo()  # noqa: F821
    screen_result = json.loads(SCREEN_RESULT_JSON.read_text(encoding="utf-8"))
    safe_columns, safe_rows = read_csv(SAFE_SLICE_CSV)
    source_columns, _source_rows = read_csv(SOURCE_SHADOW_CSV)

    role_field = model._fields.get(ROLE_FIELD)
    role_required = bool(getattr(role_field, "required", False)) if role_field else False
    role_selection = list(getattr(role_field, "selection", []) or []) if role_field else []
    role_column_candidates = [
        column
        for column in safe_columns + source_columns
        if clean(column).lower() in {"role", "role_key", "project_role", "project_role_code", "gw", "zw", "js", "roleid", "role_id"}
    ]

    required_safe_columns = {
        "legacy_member_id",
        "legacy_project_id",
        "project_id",
        "legacy_user_id",
        "mapped_user_id",
        "user_match_mode",
    }
    missing_safe_columns = sorted(required_safe_columns - set(safe_columns))
    pair_counts = Counter(
        (clean(row.get("project_id")), clean(row.get("mapped_user_id")))
        for row in safe_rows
    )
    duplicate_project_user_pairs = [
        {"project_id": project_id, "mapped_user_id": user_id, "count": count}
        for (project_id, user_id), count in sorted(pair_counts.items())
        if project_id and user_id and count > 1
    ]
    placeholder_rows = [
        {
            "legacy_member_id": clean(row.get("legacy_member_id")),
            "project_id": clean(row.get("project_id")),
            "mapped_user_id": clean(row.get("mapped_user_id")),
        }
        for row in safe_rows
        if clean(row.get("user_match_mode")) == "placeholder_user"
    ]
    missing_identity_rows = [
        {
            "line": index,
            "legacy_member_id": clean(row.get("legacy_member_id")),
            "project_id": clean(row.get("project_id")),
            "mapped_user_id": clean(row.get("mapped_user_id")),
        }
        for index, row in enumerate(safe_rows, start=2)
        if not clean(row.get("legacy_member_id")) or not clean(row.get("project_id")) or not clean(row.get("mapped_user_id"))
    ]

    project_ids = [int(clean(row.get("project_id"))) for row in safe_rows if clean(row.get("project_id"))]
    user_ids = [int(clean(row.get("mapped_user_id"))) for row in safe_rows if clean(row.get("mapped_user_id"))]
    projects = env["project.project"].sudo().search([("id", "in", project_ids)])  # noqa: F821
    users = env["res.users"].sudo().search([("id", "in", user_ids)])  # noqa: F821
    existing_pairs = []
    if project_ids and user_ids:
        existing = model.search([("project_id", "in", project_ids), ("user_id", "in", user_ids)], order="project_id,user_id,id")
        safe_pair_set = set(pair_counts)
        for record in existing:
            pair = (str(record.project_id.id), str(record.user_id.id))
            if pair in safe_pair_set:
                existing_pairs.append(
                    {
                        "id": record.id,
                        "project_id": record.project_id.id,
                        "user_id": record.user_id.id,
                        "role_key": record.role_key or "",
                        "note": record.note or "",
                    }
                )

    blocking_reasons = []
    if screen_result.get("status") != "PASS":
        blocking_reasons.append("upstream_screen_not_pass")
    if len(safe_rows) != EXPECTED_COUNT:
        blocking_reasons.append("safe_slice_row_count_not_34")
    if missing_safe_columns:
        blocking_reasons.append("missing_safe_slice_columns")
    if placeholder_rows:
        blocking_reasons.append("placeholder_user_rows_in_safe_slice")
    if duplicate_project_user_pairs:
        blocking_reasons.append("duplicate_project_user_pairs")
    if missing_identity_rows:
        blocking_reasons.append("missing_identity_rows")
    if len(projects) != len(set(project_ids)):
        blocking_reasons.append("project_records_missing")
    if len(users) != len(set(user_ids)):
        blocking_reasons.append("user_records_missing")
    if existing_pairs:
        blocking_reasons.append("target_project_user_pair_not_empty")
    if not role_field or not role_required:
        blocking_reasons.append("target_role_field_not_required_as_expected")
    if role_required and not role_column_candidates:
        blocking_reasons.append("required_role_fact_missing")

    status = "WRITE_READY" if not blocking_reasons else "WRITE_BLOCKED"
    payload = {
        "status": status,
        "run_id": RUN_ID,
        "mode": "project_member_34_write_readiness_gate",
        "database": env.cr.dbname,  # noqa: F821
        "target_model": TARGET_MODEL,
        "safe_slice_path": str(SAFE_SLICE_CSV),
        "safe_slice_rows": len(safe_rows),
        "expected_rows": EXPECTED_COUNT,
        "db_writes": 0,
        "target_model_role_field": {
            "name": ROLE_FIELD,
            "exists": bool(role_field),
            "required": role_required,
            "selection": role_selection,
        },
        "source_columns": source_columns,
        "safe_slice_columns": safe_columns,
        "role_column_candidates": role_column_candidates,
        "safe_slice_checks": {
            "missing_safe_columns": missing_safe_columns,
            "placeholder_rows": placeholder_rows,
            "duplicate_project_user_pairs": duplicate_project_user_pairs,
            "missing_identity_rows": missing_identity_rows,
            "unique_project_ids": len(set(project_ids)),
            "matched_project_records": len(projects),
            "unique_user_ids": len(set(user_ids)),
            "matched_user_records": len(users),
            "existing_target_project_user_pairs": existing_pairs,
        },
        "blocking_reasons": blocking_reasons,
        "decision": (
            "Do not run project_member create-only write until a legacy role mapping is defined."
            if status == "WRITE_BLOCKED"
            else "Safe slice may proceed to a dedicated create-only write task."
        ),
    }
    write_json(OUTPUT_JSON, payload)
    env.cr.rollback()  # noqa: F821
    print("PROJECT_MEMBER_34_WRITE_READINESS=" + json.dumps({
        "status": status,
        "safe_slice_rows": payload["safe_slice_rows"],
        "db_writes": payload["db_writes"],
        "blocking_reasons": blocking_reasons,
    }, ensure_ascii=False, sort_keys=True))


main()
