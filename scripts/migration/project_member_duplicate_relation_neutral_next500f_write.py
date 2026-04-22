"""Inlined writer for the next500f project_member neutral carrier."""

from __future__ import annotations

import csv
import json
from pathlib import Path


PLAN_JSON = Path("/mnt/artifacts/migration/project_member_neutral_expansion_plan_v1.json")
DUPLICATE_SLICE_CSV = Path("/mnt/artifacts/migration/project_member_neutral_expansion_duplicate_relation_evidence_slice_v1.csv")
PRE_VISIBILITY_JSON = Path("/mnt/artifacts/migration/project_member_duplicate_relation_next500f_pre_visibility_v1.json")
POST_VISIBILITY_JSON = Path("/mnt/artifacts/migration/project_member_duplicate_relation_next500f_post_visibility_v1.json")
WRITE_RESULT_JSON = Path("/mnt/artifacts/migration/project_member_duplicate_relation_next500f_write_result_v1.json")
ROLLBACK_TARGET_CSV = Path("/mnt/artifacts/migration/project_member_duplicate_relation_next500f_rollback_targets_v1.csv")

RUN_ID = "ITER-2026-04-15-1986N"
TARGET_MODEL = "sc.project.member.staging"
EXPECTED_ROWS = 500


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


def visibility_snapshot(project_ids, user_ids):
    project_model = env["project.project"]  # noqa: F821
    users = env["res.users"].sudo().browse(user_ids).exists()  # noqa: F821
    rows = []
    for user in users:
        visible_ids = project_model.with_user(user).search([("id", "in", project_ids)]).ids
        rows.append({
            "user_id": user.id,
            "user_name": user.name,
            "visible_project_count": len(visible_ids),
            "visible_project_ids": sorted(visible_ids),
        })
    return {"project_ids": sorted(project_ids), "user_ids": sorted(user_ids), "rows": rows}


def build_vals(row):
    return {
        "legacy_member_id": clean(row.get("legacy_member_id")),
        "legacy_project_id": clean(row.get("legacy_project_id")),
        "legacy_user_ref": clean(row.get("legacy_user_id")),
        "project_id": int(clean(row.get("project_id"))),
        "user_id": int(clean(row.get("mapped_user_id"))),
        "legacy_role_text": "",
        "role_fact_status": "missing",
        "import_batch": RUN_ID,
        "evidence": "project_member_neutral_expansion_duplicate_relation_evidence_slice_v1.csv",
        "notes": "Duplicate relation evidence only; neutral migration carrier; not responsibility or permission truth.",
        "active": True,
    }


def main():
    if env.cr.dbname != "sc_demo":  # noqa: F821
        raise RuntimeError({"db_name_not_sc_demo": env.cr.dbname})  # noqa: F821

    plan = json.loads(PLAN_JSON.read_text(encoding="utf-8"))
    if plan.get("status") != "PASS":
        raise RuntimeError({"project_member_neutral_expansion_plan_not_pass": plan.get("status")})
    if plan.get("duplicate_relation_evidence_slice_rows") != EXPECTED_ROWS:
        raise RuntimeError({
            "duplicate_relation_evidence_slice_rows_not_expected": plan.get("duplicate_relation_evidence_slice_rows"),
            "expected": EXPECTED_ROWS,
        })

    _columns, rows = read_csv(DUPLICATE_SLICE_CSV)
    errors = []
    if len(rows) != EXPECTED_ROWS:
        errors.append({"error": "slice_row_count_not_500", "rows": len(rows)})

    legacy_ids = [clean(row.get("legacy_member_id")) for row in rows]
    create_vals = [build_vals(row) for row in rows]
    project_ids = sorted({vals["project_id"] for vals in create_vals})
    user_ids = sorted({vals["user_id"] for vals in create_vals})

    model = env[TARGET_MODEL].sudo()  # noqa: F821
    existing_same_legacy = model.search([("legacy_member_id", "in", legacy_ids)])
    existing_same_batch = model.search([("import_batch", "=", RUN_ID)])
    if existing_same_legacy:
        errors.append({"error": "existing_neutral_legacy_conflict", "ids": existing_same_legacy.ids[:100]})
    if existing_same_batch:
        errors.append({"error": "target_import_batch_not_empty", "ids": existing_same_batch.ids[:100]})

    pre_visibility = visibility_snapshot(project_ids, user_ids)
    write_json(PRE_VISIBILITY_JSON, pre_visibility)
    if errors:
        env.cr.rollback()  # noqa: F821
        raise RuntimeError({"duplicate_relation_neutral_precheck_failed": errors})

    created_rows = []
    try:
        for vals in create_vals:
            rec = model.create(vals)
            created_rows.append({
                "neutral_id": rec.id,
                "legacy_member_id": rec.legacy_member_id,
                "project_id": rec.project_id.id,
                "user_id": rec.user_id.id,
                "role_fact_status": rec.role_fact_status,
                "import_batch": rec.import_batch,
            })
        env.cr.commit()  # noqa: F821
    except Exception:
        env.cr.rollback()  # noqa: F821
        raise

    post_visibility = visibility_snapshot(project_ids, user_ids)
    write_json(POST_VISIBILITY_JSON, post_visibility)
    visibility_changed = pre_visibility != post_visibility

    rollback_rows = [
        {
            "run_id": RUN_ID,
            "neutral_id": row["neutral_id"],
            "legacy_member_id": row["legacy_member_id"],
            "project_id": row["project_id"],
            "user_id": row["user_id"],
            "role_fact_status": row["role_fact_status"],
            "write_action_result": "created",
        }
        for row in created_rows
    ]
    write_csv(
        ROLLBACK_TARGET_CSV,
        ["run_id", "neutral_id", "legacy_member_id", "project_id", "user_id", "role_fact_status", "write_action_result"],
        rollback_rows,
    )

    post_errors = []
    if len(created_rows) != EXPECTED_ROWS:
        post_errors.append({"error": "created_count_not_500", "created": len(created_rows)})
    if len(rollback_rows) != EXPECTED_ROWS:
        post_errors.append({"error": "rollback_target_count_not_500", "rows": len(rollback_rows)})
    if visibility_changed:
        post_errors.append({"error": "project_visibility_changed"})

    payload = {
        "status": "PASS" if not post_errors else "FAIL",
        "mode": "project_member_duplicate_relation_neutral_next500f_write",
        "database": env.cr.dbname,  # noqa: F821
        "run_id": RUN_ID,
        "target_model": TARGET_MODEL,
        "created": len(created_rows),
        "updated": 0,
        "rollback_target_rows": len(rollback_rows),
        "project_responsibility_writes": 0,
        "visibility_changed": visibility_changed,
        "errors": post_errors,
        "artifacts": {
            "pre_visibility": str(PRE_VISIBILITY_JSON),
            "post_visibility": str(POST_VISIBILITY_JSON),
            "rollback_targets": str(ROLLBACK_TARGET_CSV),
        },
    }
    write_json(WRITE_RESULT_JSON, payload)
    print("PROJECT_MEMBER_DUPLICATE_RELATION_NEUTRAL_NEXT500F_WRITE=" + json.dumps({
        "status": payload["status"],
        "created": payload["created"],
        "rollback_target_rows": payload["rollback_target_rows"],
        "project_responsibility_writes": payload["project_responsibility_writes"],
        "visibility_changed": payload["visibility_changed"],
    }, ensure_ascii=False, sort_keys=True))
    if post_errors:
        raise RuntimeError({"duplicate_relation_neutral_next500f_write_failed": post_errors})


main()
