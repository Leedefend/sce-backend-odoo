#!/usr/bin/env python3
"""Replay project anchors into sc_migration_fresh."""

from __future__ import annotations

import csv
import json
from collections import Counter
from pathlib import Path


REPO_ROOT = Path("/mnt")
INPUT_CSV = REPO_ROOT / "artifacts/migration/fresh_db_project_anchor_replay_payload_v1.csv"
OUTPUT_JSON = REPO_ROOT / "artifacts/migration/fresh_db_project_anchor_replay_write_result_v1.json"
ROLLBACK_CSV = REPO_ROOT / "artifacts/migration/fresh_db_project_anchor_replay_rollback_targets_v1.csv"
EXPECTED_ROWS = 755
OPTIONAL_SOURCE_ONLY_FIELDS = {"legacy_deleted_flag", "current_db_project_id", "evidence_file", "idempotency_key", "replay_action"}
SAFE_FIELDS = [
    "name",
    "short_name",
    "project_environment",
    "legacy_project_id",
    "legacy_parent_id",
    "legacy_company_id",
    "legacy_company_name",
    "legacy_specialty_type_id",
    "specialty_type_name",
    "legacy_price_method",
    "business_nature",
    "detail_address",
    "project_profile",
    "project_area",
    "legacy_is_shared_base",
    "legacy_sort",
    "legacy_attachment_ref",
    "project_overview",
    "legacy_project_nature",
    "legacy_is_material_library",
    "other_system_id",
    "other_system_code",
    "legacy_stage_id",
    "legacy_stage_name",
    "legacy_region_id",
    "legacy_region_name",
    "legacy_state",
    "legacy_project_manager_name",
    "legacy_technical_responsibility_name",
]


def clean(value: object) -> str:
    return "" if value is None else str(value).strip()


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return [dict(row) for row in csv.DictReader(handle)]


def write_csv(path: Path, fieldnames: list[str], rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def write_json(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def build_vals(row: dict[str, str], existing_fields: set[str]) -> dict[str, object]:
    vals = {field: clean(row.get(field)) for field in SAFE_FIELDS if field in existing_fields}
    return {field: value for field, value in vals.items() if value not in ("", None)}


if env.cr.dbname != "sc_migration_fresh":  # noqa: F821
    raise RuntimeError({"db_name_not_sc_migration_fresh": env.cr.dbname})  # noqa: F821

Project = env["project.project"].sudo()  # noqa: F821
existing_fields = set(Project._fields)
missing_fields = [field for field in SAFE_FIELDS if field not in existing_fields]
if missing_fields:
    raise RuntimeError({"missing_project_fields": missing_fields})

rows = read_csv(INPUT_CSV)
errors: list[dict[str, object]] = []
if len(rows) != EXPECTED_ROWS:
    errors.append({"error": "unexpected_row_count", "actual": len(rows), "expected": EXPECTED_ROWS})

keys = [clean(row.get("legacy_project_id")) for row in rows]
key_counts = Counter(keys)
duplicates = [key for key, count in key_counts.items() if key and count > 1]
if duplicates:
    errors.append({"error": "duplicate_payload_identity", "samples": duplicates[:20]})
for index, row in enumerate(rows, start=2):
    if not clean(row.get("legacy_project_id")):
        errors.append({"line": index, "error": "missing_legacy_project_id"})
    if not clean(row.get("name")):
        errors.append({"line": index, "error": "missing_name"})
    if clean(row.get("replay_action")) != "create_if_missing":
        errors.append({"line": index, "error": "unexpected_replay_action", "value": clean(row.get("replay_action"))})

existing = Project.browse()
for legacy_project_id in keys:
    if legacy_project_id:
        existing |= Project.search([("legacy_project_id", "=", legacy_project_id)], limit=1)
if existing:
    errors.append({"error": "target_identity_not_empty", "count": len(existing), "samples": existing[:20].mapped("id")})
if errors:
    env.cr.rollback()  # noqa: F821
    raise RuntimeError({"precheck_failed": errors[:30]})

created_rows: list[dict[str, object]] = []
try:
    for row in rows:
        vals = build_vals(row, existing_fields)
        rec = Project.create(vals)
        created_rows.append(
            {
                "id": rec.id,
                "legacy_project_id": rec.legacy_project_id or "",
                "project_code": rec.project_code or "",
                "name": rec.name or "",
            }
        )
    env.cr.commit()  # noqa: F821
except Exception:
    env.cr.rollback()  # noqa: F821
    raise

post_count = 0
for legacy_project_id in keys:
    post_count += Project.search_count([("legacy_project_id", "=", legacy_project_id)])

status = "PASS" if len(created_rows) == EXPECTED_ROWS and post_count == EXPECTED_ROWS else "FAIL"
result = {
    "status": status,
    "mode": "fresh_db_project_anchor_replay_write",
    "database": env.cr.dbname,  # noqa: F821
    "target_model": "project.project",
    "input_rows": len(rows),
    "created_rows": len(created_rows),
    "post_write_identity_count": post_count,
    "skipped_existing": 0,
    "db_writes": len(created_rows),
    "demo_targets_executed": 0,
    "source_only_fields_not_written": sorted(OPTIONAL_SOURCE_ONLY_FIELDS),
    "write_payload": str(INPUT_CSV),
    "rollback_targets": str(ROLLBACK_CSV),
    "decision": "project_anchor_replay_write_complete" if status == "PASS" else "STOP_REVIEW_REQUIRED",
    "next_step": "replay contract partner anchors into sc_migration_fresh",
}
write_csv(
    ROLLBACK_CSV,
    ["id", "legacy_project_id", "project_code", "name"],
    created_rows,
)
write_json(OUTPUT_JSON, result)
print(
    "FRESH_DB_PROJECT_ANCHOR_REPLAY_WRITE="
    + json.dumps(
        {
            "status": status,
            "input_rows": len(rows),
            "created_rows": len(created_rows),
            "post_write_identity_count": post_count,
            "db_writes": len(created_rows),
        },
        ensure_ascii=False,
        sort_keys=True,
    )
)
