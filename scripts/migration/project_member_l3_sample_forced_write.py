"""Force-write the first three L3 checklist rows into project.responsibility."""

from __future__ import annotations

import csv
import json
from pathlib import Path


RUN_ID = "ITER-2026-04-14-L3-SAMPLE-FORCED-WRITE"
FORCED_ROLE_KEY = "project_member"
FORCED_ROLE_SOURCE = "migration_l3_sample_forced_write_v1"
FORCED_REVIEWER = "system_migration_task"
SAMPLE_SIZE = 3

ARTIFACT_ROOT = Path("/mnt/artifacts") if Path("/mnt/artifacts").exists() else Path("artifacts")
MIGRATION_DIR = ARTIFACT_ROOT / "migration"
CHECKLIST_CSV = MIGRATION_DIR / "project_member_l3_business_review_checklist_v1.csv"
WRITE_RESULT_JSON = MIGRATION_DIR / "project_member_l3_sample_forced_write_result_v1.json"
POST_AUDIT_JSON = MIGRATION_DIR / "project_member_l3_sample_forced_write_post_audit_v1.json"
ROLLBACK_CSV = MIGRATION_DIR / "project_member_l3_sample_forced_write_rollback_targets_v1.csv"


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


def ensure_odoo_env():
    if "env" not in globals():
        raise RuntimeError({"odoo_env_required": True})
    if env.cr.dbname != "sc_demo":  # noqa: F821
        raise RuntimeError({"db_name_not_sc_demo": env.cr.dbname})  # noqa: F821


def load_first_three_rows():
    fields, rows = read_csv(CHECKLIST_CSV)
    required = {"review_rank", "pair_key", "project_id", "project_name", "user_id", "user_name"}
    missing = sorted(required - set(fields))
    if missing:
        raise RuntimeError({"missing_checklist_columns": missing})
    selected = sorted(rows, key=lambda row: int(clean(row.get("review_rank")) or "0"))[:SAMPLE_SIZE]
    if len(selected) != SAMPLE_SIZE:
        raise RuntimeError({"sample_size_not_3": len(selected)})
    if [int(clean(row["review_rank"])) for row in selected] != [1, 2, 3]:
        raise RuntimeError({"first_three_review_ranks_not_selected": [row.get("review_rank") for row in selected]})
    return selected


def audit(created_rows, write_status):
    responsibility = env["project.responsibility"].sudo()  # noqa: F821
    ids = [row["responsibility_id"] for row in created_rows]
    records = responsibility.browse(ids).exists()
    audit_rows = []
    for record in records:
        audit_rows.append(
            {
                "responsibility_id": record.id,
                "project_id": record.project_id.id,
                "user_id": record.user_id.id,
                "role_key": record.role_key or "",
                "note_contains_run_id": bool(record.note and RUN_ID in record.note),
                "rollback_eligible": bool(record.note and RUN_ID in record.note),
            }
        )
    blocking_reasons = []
    if write_status != "PASS":
        blocking_reasons.append("write_result_not_pass")
    if len(audit_rows) != SAMPLE_SIZE:
        blocking_reasons.append("matched_records_not_3")
    if any(row["role_key"] != FORCED_ROLE_KEY for row in audit_rows):
        blocking_reasons.append("role_key_mismatch")
    if any(not row["rollback_eligible"] for row in audit_rows):
        blocking_reasons.append("rollback_eligibility_missing")
    payload = {
        "status": "PASS" if not blocking_reasons else "FAIL",
        "run_id": RUN_ID,
        "matched_records": len(audit_rows),
        "rollback_eligible_rows": sum(1 for row in audit_rows if row["rollback_eligible"]),
        "db_writes": 0,
        "blocking_reasons": blocking_reasons,
        "rows": audit_rows,
    }
    write_json(POST_AUDIT_JSON, payload)
    return payload


def main():
    ensure_odoo_env()
    selected = load_first_three_rows()
    responsibility = env["project.responsibility"].sudo()  # noqa: F821
    existing_conflicts = []
    created = []
    try:
        for row in selected:
            project_id = int(clean(row["project_id"]))
            user_id = int(clean(row["user_id"]))
            existing = responsibility.search(
                [
                    ("project_id", "=", project_id),
                    ("user_id", "=", user_id),
                    ("role_key", "=", FORCED_ROLE_KEY),
                ],
                limit=1,
            )
            if existing:
                existing_conflicts.append(
                    {
                        "responsibility_id": existing.id,
                        "pair_key": clean(row["pair_key"]),
                        "project_id": project_id,
                        "user_id": user_id,
                        "role_key": FORCED_ROLE_KEY,
                    }
                )
                continue
            rec = responsibility.create(
                {
                    "project_id": project_id,
                    "user_id": user_id,
                    "role_key": FORCED_ROLE_KEY,
                    "is_primary": False,
                    "note": (
                        f"{RUN_ID}; pair_key={clean(row['pair_key'])}; "
                        f"role_source_evidence={FORCED_ROLE_SOURCE}; "
                        f"business_reviewer={FORCED_REVIEWER}; "
                        "business_decision=forced_migration_assumption"
                    ),
                }
            )
            created.append(
                {
                    "responsibility_id": rec.id,
                    "project_id": project_id,
                    "project_name": clean(row["project_name"]),
                    "user_id": user_id,
                    "user_name": clean(row["user_name"]),
                    "role_key": rec.role_key or "",
                    "pair_key": clean(row["pair_key"]),
                    "role_source_evidence": FORCED_ROLE_SOURCE,
                    "business_reviewer": FORCED_REVIEWER,
                    "write_action_result": "created",
                }
            )
        if existing_conflicts:
            raise RuntimeError({"existing_project_responsibility_conflicts": existing_conflicts})
        env.cr.commit()  # noqa: F821
    except Exception as exc:
        env.cr.rollback()  # noqa: F821
        payload = {
            "status": "FAIL",
            "run_id": RUN_ID,
            "target_model": "project.responsibility",
            "forced_role_key": FORCED_ROLE_KEY,
            "sample_rows": SAMPLE_SIZE,
            "created": 0,
            "db_writes": 0,
            "error": repr(exc),
        }
        write_json(WRITE_RESULT_JSON, payload)
        write_csv(
            ROLLBACK_CSV,
            ["run_id", "responsibility_id", "project_id", "user_id", "role_key", "pair_key", "write_action_result"],
            [],
        )
        write_json(
            POST_AUDIT_JSON,
            {
                "status": "FAIL",
                "run_id": RUN_ID,
                "matched_records": 0,
                "rollback_eligible_rows": 0,
                "db_writes": 0,
                "blocking_reasons": ["write_failed"],
                "error": repr(exc),
            },
        )
        print("PROJECT_MEMBER_L3_SAMPLE_FORCED_WRITE=" + json.dumps(payload, ensure_ascii=False, sort_keys=True))
        raise

    write_csv(
        ROLLBACK_CSV,
        ["run_id", "responsibility_id", "project_id", "user_id", "role_key", "pair_key", "write_action_result"],
        [{"run_id": RUN_ID, **row} for row in created],
    )
    write_result = {
        "status": "PASS" if len(created) == SAMPLE_SIZE else "FAIL",
        "run_id": RUN_ID,
        "target_model": "project.responsibility",
        "forced_role_key": FORCED_ROLE_KEY,
        "role_source_evidence": FORCED_ROLE_SOURCE,
        "business_reviewer": FORCED_REVIEWER,
        "sample_rows": SAMPLE_SIZE,
        "created": len(created),
        "updated": 0,
        "db_writes": len(created),
        "created_rows": created,
        "rollback_targets": str(ROLLBACK_CSV),
    }
    write_json(WRITE_RESULT_JSON, write_result)
    audit_result = audit(created, write_result["status"])
    print("PROJECT_MEMBER_L3_SAMPLE_FORCED_WRITE=" + json.dumps({
        "status": write_result["status"],
        "created": write_result["created"],
        "db_writes": write_result["db_writes"],
        "audit_status": audit_result["status"],
        "forced_role_key": FORCED_ROLE_KEY,
    }, ensure_ascii=False, sort_keys=True))
    if write_result["status"] != "PASS" or audit_result["status"] != "PASS":
        raise RuntimeError({"project_member_l3_sample_forced_write_failed": write_result, "audit": audit_result})


main()
