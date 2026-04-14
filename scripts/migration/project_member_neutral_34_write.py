"""Create-only write for 34-row project_member neutral carrier safe slice."""

from __future__ import annotations

import csv
import json
from collections import Counter
from pathlib import Path


SAFE_SLICE_CSV = Path("/mnt/artifacts/migration/project_member_no_placeholder_safe_slice_v1.csv")
PRE_VISIBILITY_JSON = Path("/mnt/artifacts/migration/project_member_neutral_34_pre_visibility_v1.json")
POST_VISIBILITY_JSON = Path("/mnt/artifacts/migration/project_member_neutral_34_post_visibility_v1.json")
WRITE_RESULT_JSON = Path("/mnt/artifacts/migration/project_member_neutral_34_write_result_v1.json")
ROLLBACK_TARGET_CSV = Path("/mnt/artifacts/migration/project_member_rollback_targets_v1.csv")

RUN_ID = "ITER-2026-04-14-0030N"
EXPECTED_COUNT = 34
TARGET_MODEL = "sc.project.member.staging"
FORBIDDEN_MODEL = "project.responsibility"


def clean(value):
    return ("" if value is None else str(value)).replace("\r\n", "\n").replace("\r", "\n").strip()


def read_csv(path):
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        return list(reader.fieldnames or []), [dict(row) for row in reader]


def write_csv(path, fieldnames, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def write_json(path, payload):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def visibility_snapshot(project_ids, user_ids):
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


def build_vals(row, line_no):
    return {
        "legacy_member_id": clean(row.get("legacy_member_id")),
        "legacy_project_id": clean(row.get("legacy_project_id")),
        "legacy_user_ref": clean(row.get("legacy_user_id")),
        "project_id": int(clean(row.get("project_id"))),
        "user_id": int(clean(row.get("mapped_user_id"))),
        "legacy_role_text": "",
        "role_fact_status": "missing",
        "import_batch": RUN_ID,
        "evidence": f"project_member_no_placeholder_safe_slice_v1.csv:{line_no}",
        "notes": "Neutral migration carrier only; not project.responsibility; not permission or responsibility truth.",
        "active": True,
    }


def main():
    if env.cr.dbname != "sc_demo":  # noqa: F821
        raise RuntimeError({"db_name_not_sc_demo": env.cr.dbname})  # noqa: F821

    if TARGET_MODEL not in env:  # noqa: F821
        raise RuntimeError({"neutral_carrier_model_missing": TARGET_MODEL})

    model = env[TARGET_MODEL].sudo()  # noqa: F821
    _forbidden = env[FORBIDDEN_MODEL].sudo()  # noqa: F821
    columns, rows = read_csv(SAFE_SLICE_CSV)
    required_columns = {
        "legacy_member_id",
        "legacy_project_id",
        "project_id",
        "legacy_user_id",
        "mapped_user_id",
        "user_match_mode",
    }
    missing_columns = sorted(required_columns - set(columns))
    precheck_errors = []
    if missing_columns:
        precheck_errors.append({"error": "missing_safe_slice_columns", "columns": missing_columns})
    if len(rows) != EXPECTED_COUNT:
        precheck_errors.append({"error": "safe_slice_not_34_rows", "rows": len(rows)})

    legacy_ids = [clean(row.get("legacy_member_id")) for row in rows]
    duplicate_legacy_ids = [key for key, count in Counter(legacy_ids).items() if key and count > 1]
    if duplicate_legacy_ids:
        precheck_errors.append({"error": "duplicate_legacy_member_id", "ids": duplicate_legacy_ids})

    create_vals = []
    for line_no, row in enumerate(rows, start=2):
        row_errors = []
        if clean(row.get("user_match_mode")) == "placeholder_user":
            row_errors.append("placeholder_user_not_allowed")
        for field in ["legacy_member_id", "legacy_project_id", "project_id", "legacy_user_id", "mapped_user_id"]:
            if not clean(row.get(field)):
                row_errors.append(f"missing_{field}")
        if row_errors:
            precheck_errors.extend({"line": line_no, "error": error, "legacy_member_id": clean(row.get("legacy_member_id"))} for error in row_errors)
        else:
            create_vals.append(build_vals(row, line_no))

    project_ids = sorted({vals["project_id"] for vals in create_vals})
    user_ids = sorted({vals["user_id"] for vals in create_vals})
    projects = env["project.project"].sudo().browse(project_ids).exists()  # noqa: F821
    users = env["res.users"].sudo().browse(user_ids).exists()  # noqa: F821
    if len(projects) != len(project_ids):
        precheck_errors.append({"error": "missing_project_records", "project_ids": sorted(set(project_ids) - set(projects.ids))})
    if len(users) != len(user_ids):
        precheck_errors.append({"error": "missing_user_records", "user_ids": sorted(set(user_ids) - set(users.ids))})

    existing = model.search([("legacy_member_id", "in", legacy_ids), ("import_batch", "=", RUN_ID)])
    if existing:
        precheck_errors.append({"error": "neutral_target_not_empty_before_write", "ids": existing.ids})

    pre_visibility = visibility_snapshot(project_ids, user_ids)
    write_json(PRE_VISIBILITY_JSON, pre_visibility)
    if precheck_errors:
        env.cr.rollback()  # noqa: F821
        raise RuntimeError({"neutral_precheck_failed": precheck_errors})

    created = []
    try:
        for vals in create_vals:
            rec = model.create(vals)
            created.append(
                {
                    "neutral_id": rec.id,
                    "legacy_member_id": rec.legacy_member_id,
                    "project_id": rec.project_id.id,
                    "user_id": rec.user_id.id,
                    "role_fact_status": rec.role_fact_status,
                    "import_batch": rec.import_batch,
                }
            )
        env.cr.commit()  # noqa: F821
    except Exception:
        env.cr.rollback()  # noqa: F821
        raise

    post_visibility = visibility_snapshot(project_ids, user_ids)
    write_json(POST_VISIBILITY_JSON, post_visibility)
    visibility_changed = pre_visibility != post_visibility

    rollback_rows = []
    for row in created:
        rollback_rows.append(
            {
                "run_id": RUN_ID,
                "neutral_id": row["neutral_id"],
                "legacy_member_id": row["legacy_member_id"],
                "project_id": row["project_id"],
                "user_id": row["user_id"],
                "role_fact_status": row["role_fact_status"],
                "write_action_result": "created",
            }
        )
    write_csv(
        ROLLBACK_TARGET_CSV,
        ["run_id", "neutral_id", "legacy_member_id", "project_id", "user_id", "role_fact_status", "write_action_result"],
        rollback_rows,
    )

    post_errors = []
    if len(created) != EXPECTED_COUNT:
        post_errors.append({"error": "created_count_not_34", "created": len(created)})
    if len(rollback_rows) != EXPECTED_COUNT:
        post_errors.append({"error": "rollback_target_count_not_34", "rows": len(rollback_rows)})
    if visibility_changed:
        post_errors.append({"error": "project_visibility_changed"})

    payload = {
        "status": "PASS" if not post_errors else "FAIL",
        "mode": "project_member_neutral_34_create_only_write",
        "database": env.cr.dbname,  # noqa: F821
        "target_model": TARGET_MODEL,
        "forbidden_model": FORBIDDEN_MODEL,
        "project_responsibility_writes": 0,
        "created": len(created),
        "updated": 0,
        "errors": len(post_errors),
        "rollback_target_rows": len(rollback_rows),
        "visibility_changed": visibility_changed,
        "post_errors": post_errors,
        "created_rows": created,
        "artifacts": {
            "pre_visibility": str(PRE_VISIBILITY_JSON),
            "post_visibility": str(POST_VISIBILITY_JSON),
            "rollback_targets": str(ROLLBACK_TARGET_CSV),
        },
    }
    write_json(WRITE_RESULT_JSON, payload)
    print("PROJECT_MEMBER_NEUTRAL_34_WRITE=" + json.dumps({
        "status": payload["status"],
        "created": payload["created"],
        "project_responsibility_writes": payload["project_responsibility_writes"],
        "visibility_changed": payload["visibility_changed"],
        "rollback_target_rows": payload["rollback_target_rows"],
    }, ensure_ascii=False, sort_keys=True))
    if post_errors:
        raise RuntimeError({"project_member_neutral_write_failed": post_errors})


main()
