#!/usr/bin/env python3
"""Replay project-member neutral staging rows into sc_migration_fresh."""

from __future__ import annotations

import csv
import json
from collections import Counter
from pathlib import Path


REPO_ROOT = Path("/mnt")
INPUT_CSV = REPO_ROOT / "artifacts/migration/fresh_db_project_member_neutral_replay_payload_v1.csv"
OUTPUT_JSON = REPO_ROOT / "artifacts/migration/fresh_db_project_member_neutral_replay_write_result_v1.json"
ROLLBACK_CSV = REPO_ROOT / "artifacts/migration/fresh_db_project_member_neutral_replay_rollback_targets_v1.csv"
PRE_VISIBILITY_JSON = REPO_ROOT / "artifacts/migration/fresh_db_project_member_neutral_replay_pre_visibility_v1.json"
POST_VISIBILITY_JSON = REPO_ROOT / "artifacts/migration/fresh_db_project_member_neutral_replay_post_visibility_v1.json"
EXPECTED_ROWS = 7389
TARGET_MODEL = "sc.project.member.staging"
FORBIDDEN_MODEL = "project.responsibility"


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


def visibility_snapshot(project_ids: list[int], user_ids: list[int]) -> dict[str, object]:
    project_model = env["project.project"]  # noqa: F821
    users = env["res.users"].sudo().browse(user_ids).exists()  # noqa: F821
    rows = []
    for user in users:
        visible_ids = project_model.with_user(user).search([("id", "in", project_ids)]).ids
        rows.append(
            {
                "user_id": user.id,
                "user_name": user.name,
                "visible_project_count": len(visible_ids),
                "visible_project_ids": sorted(visible_ids),
            }
        )
    return {"project_ids": sorted(project_ids), "user_ids": sorted(user_ids), "rows": rows}


def build_vals(row: dict[str, str]) -> dict[str, object]:
    return {
        "legacy_member_id": clean(row.get("legacy_member_id")),
        "legacy_project_id": clean(row.get("legacy_project_id")),
        "legacy_user_ref": clean(row.get("legacy_user_ref")),
        "project_id": int(clean(row.get("fresh_project_id"))),
        "user_id": int(clean(row.get("target_user_id"))),
        "legacy_role_text": "",
        "role_fact_status": clean(row.get("role_fact_status")) or "missing",
        "import_batch": clean(row.get("import_batch")),
        "evidence": clean(row.get("evidence")) or "fresh_db_project_member_neutral_replay_payload_v1.csv",
        "notes": clean(row.get("notes")) or "Fresh replay of neutral carrier only.",
        "active": clean(row.get("active")).lower() not in {"0", "false", "no", "n"},
    }


if env.cr.dbname != "sc_migration_fresh":  # noqa: F821
    raise RuntimeError({"db_name_not_sc_migration_fresh": env.cr.dbname})  # noqa: F821

Model = env[TARGET_MODEL].sudo()  # noqa: F821
Responsibility = env[FORBIDDEN_MODEL].sudo()  # noqa: F821
Project = env["project.project"].sudo()  # noqa: F821
Users = env["res.users"].sudo()  # noqa: F821

rows = read_csv(INPUT_CSV)
errors: list[dict[str, object]] = []
if len(rows) != EXPECTED_ROWS:
    errors.append({"error": "unexpected_row_count", "actual": len(rows), "expected": EXPECTED_ROWS})
keys = [clean(row.get("idempotency_key")) for row in rows]
duplicate_keys = [key for key, count in Counter(keys).items() if key and count > 1]
if duplicate_keys:
    errors.append({"error": "duplicate_payload_identity", "samples": duplicate_keys[:20]})

create_vals = []
for index, row in enumerate(rows, start=2):
    vals = build_vals(row)
    if clean(row.get("replay_action")) != "create_if_missing":
        errors.append({"line": index, "error": "unexpected_replay_action", "value": clean(row.get("replay_action"))})
    if vals["role_fact_status"] != "missing":
        errors.append({"line": index, "error": "role_fact_status_not_missing", "value": vals["role_fact_status"]})
    if not Project.browse(vals["project_id"]).exists():
        errors.append({"line": index, "error": "project_missing", "project_id": vals["project_id"]})
    if not Users.browse(vals["user_id"]).exists():
        errors.append({"line": index, "error": "user_missing", "user_id": vals["user_id"]})
    create_vals.append(vals)

legacy_batch_pairs = [(vals["legacy_member_id"], vals["import_batch"]) for vals in create_vals]
existing = Model.browse()
for legacy_member_id, import_batch in legacy_batch_pairs:
    existing |= Model.search([("legacy_member_id", "=", legacy_member_id), ("import_batch", "=", import_batch)], limit=1)
if existing:
    errors.append({"error": "target_identity_not_empty", "count": len(existing), "samples": existing[:20].mapped("id")})

project_ids = sorted({vals["project_id"] for vals in create_vals})
user_ids = sorted({vals["user_id"] for vals in create_vals})
responsibility_before = Responsibility.search_count([])
pre_visibility = visibility_snapshot(project_ids, user_ids)
write_json(PRE_VISIBILITY_JSON, pre_visibility)
if errors:
    env.cr.rollback()  # noqa: F821
    raise RuntimeError({"precheck_failed": errors[:40]})

created_rows = []
try:
    for vals in create_vals:
        rec = Model.create(vals)
        created_rows.append(
            {
                "neutral_id": rec.id,
                "legacy_member_id": rec.legacy_member_id or "",
                "legacy_project_id": rec.legacy_project_id or "",
                "project_id": rec.project_id.id or "",
                "user_id": rec.user_id.id or "",
                "role_fact_status": rec.role_fact_status or "",
                "import_batch": rec.import_batch or "",
            }
        )
    env.cr.commit()  # noqa: F821
except Exception:
    env.cr.rollback()  # noqa: F821
    raise

post_visibility = visibility_snapshot(project_ids, user_ids)
write_json(POST_VISIBILITY_JSON, post_visibility)
visibility_changed = pre_visibility != post_visibility
responsibility_after = Responsibility.search_count([])
project_responsibility_writes = responsibility_after - responsibility_before
write_csv(
    ROLLBACK_CSV,
    ["neutral_id", "legacy_member_id", "legacy_project_id", "project_id", "user_id", "role_fact_status", "import_batch"],
    created_rows,
)

post_errors = []
if len(created_rows) != EXPECTED_ROWS:
    post_errors.append({"error": "created_count_not_7389", "created": len(created_rows)})
if visibility_changed:
    post_errors.append({"error": "project_visibility_changed"})
if project_responsibility_writes != 0:
    post_errors.append({"error": "project_responsibility_writes_detected", "count": project_responsibility_writes})
status = "PASS" if not post_errors else "FAIL"
result = {
    "status": status,
    "mode": "fresh_db_project_member_neutral_replay_write",
    "database": env.cr.dbname,  # noqa: F821
    "target_model": TARGET_MODEL,
    "created_rows": len(created_rows),
    "updated_rows": 0,
    "rollback_target_rows": len(created_rows),
    "project_responsibility_writes": project_responsibility_writes,
    "visibility_changed": visibility_changed,
    "db_writes": len(created_rows),
    "demo_targets_executed": 0,
    "post_errors": post_errors,
    "artifacts": {
        "pre_visibility": str(PRE_VISIBILITY_JSON),
        "post_visibility": str(POST_VISIBILITY_JSON),
        "rollback_targets": str(ROLLBACK_CSV),
    },
    "decision": "project_member_neutral_replay_write_complete" if status == "PASS" else "STOP_REVIEW_REQUIRED",
    "next_step": "refresh fresh database replay manifest after project-member neutral replay",
}
write_json(OUTPUT_JSON, result)
print(
    "FRESH_DB_PROJECT_MEMBER_NEUTRAL_REPLAY_WRITE="
    + json.dumps(
        {
            "status": status,
            "created_rows": len(created_rows),
            "project_responsibility_writes": project_responsibility_writes,
            "visibility_changed": visibility_changed,
            "db_writes": len(created_rows),
        },
        ensure_ascii=False,
        sort_keys=True,
    )
)
if post_errors:
    raise RuntimeError({"project_member_neutral_replay_write_failed": post_errors})
