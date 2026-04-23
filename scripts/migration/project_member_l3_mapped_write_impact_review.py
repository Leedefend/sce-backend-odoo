"""Readonly impact review for the three L3 mapped manager responsibility rows."""

from __future__ import annotations

import csv
import json
from pathlib import Path


RUN_ID = "ITER-2026-04-14-L3-ROLE-KEY-AUDIT-MAPPED-WRITE"
EXPECTED_COUNT = 3
ARTIFACT_ROOT = Path("/mnt/artifacts") if Path("/mnt/artifacts").exists() else Path("artifacts")
MIGRATION_DIR = ARTIFACT_ROOT / "migration"
ROLLBACK_CSV = MIGRATION_DIR / "project_member_l3_mapped_write_rollback_targets_v1.csv"
WRITE_RESULT_JSON = MIGRATION_DIR / "project_member_l3_mapped_write_result_v1.json"
POST_AUDIT_JSON = MIGRATION_DIR / "project_member_l3_mapped_write_post_audit_v1.json"
OUTPUT_JSON = MIGRATION_DIR / "project_member_l3_mapped_write_impact_review_v1.json"


def clean(value):
    return ("" if value is None else str(value)).strip()


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

    write_result = json.loads(WRITE_RESULT_JSON.read_text(encoding="utf-8"))
    post_audit = json.loads(POST_AUDIT_JSON.read_text(encoding="utf-8"))
    _fields, rollback_rows = read_csv(ROLLBACK_CSV)

    ids = [int(clean(row["responsibility_id"])) for row in rollback_rows if clean(row.get("responsibility_id"))]
    responsibility = env["project.responsibility"].sudo()  # noqa: F821
    records = responsibility.browse(ids).exists()
    review_rows = []
    follower_missing = []
    visibility_missing = []
    rollback_not_eligible = []

    for record in records:
        project = record.project_id
        user = record.user_id
        partner = user.partner_id
        follower_present = bool(partner and partner in project.message_partner_ids)
        visible_ids = env["project.project"].with_user(user).search([("id", "=", project.id)]).ids  # noqa: F821
        visible_to_user = project.id in visible_ids
        rollback_eligible = bool(record.note and RUN_ID in record.note and record.id in ids)
        row = {
            "responsibility_id": record.id,
            "project_id": project.id,
            "project_name": project.display_name,
            "user_id": user.id,
            "user_name": user.name,
            "role_key": record.role_key or "",
            "active": bool(record.active),
            "partner_id": partner.id if partner else None,
            "follower_present": follower_present,
            "visible_to_user": visible_to_user,
            "message_partner_count": len(project.message_partner_ids),
            "rollback_eligible": rollback_eligible,
        }
        review_rows.append(row)
        if not follower_present:
            follower_missing.append(row)
        if not visible_to_user:
            visibility_missing.append(row)
        if not rollback_eligible:
            rollback_not_eligible.append(row)

    blocking_reasons = []
    if write_result.get("status") != "PASS":
        blocking_reasons.append("write_result_not_pass")
    if post_audit.get("status") != "PASS":
        blocking_reasons.append("post_audit_not_pass")
    if len(rollback_rows) != EXPECTED_COUNT:
        blocking_reasons.append("rollback_target_count_not_3")
    if len(records) != EXPECTED_COUNT:
        blocking_reasons.append("responsibility_records_missing")
    if follower_missing:
        blocking_reasons.append("follower_missing_for_some_projects")
    if visibility_missing:
        blocking_reasons.append("visibility_missing_for_some_users")
    if rollback_not_eligible:
        blocking_reasons.append("rollback_eligibility_missing")

    payload = {
        "status": "PASS" if not blocking_reasons else "PASS_WITH_RISK",
        "run_id": "ITER-2026-04-14-L3-MAPPED-WRITE-IMPACT-REVIEW",
        "source_run_id": RUN_ID,
        "database": env.cr.dbname,  # noqa: F821
        "db_writes": 0,
        "responsibility_records_reviewed": len(records),
        "rollback_target_rows": len(rollback_rows),
        "follower_present_rows": sum(1 for row in review_rows if row["follower_present"]),
        "visible_to_user_rows": sum(1 for row in review_rows if row["visible_to_user"]),
        "rollback_eligible_rows": sum(1 for row in review_rows if row["rollback_eligible"]),
        "blocking_reasons": blocking_reasons,
        "rows": review_rows,
    }
    write_json(OUTPUT_JSON, payload)
    env.cr.rollback()  # noqa: F821
    print("PROJECT_MEMBER_L3_MAPPED_WRITE_IMPACT_REVIEW=" + json.dumps({
        "status": payload["status"],
        "reviewed": payload["responsibility_records_reviewed"],
        "follower_present_rows": payload["follower_present_rows"],
        "visible_to_user_rows": payload["visible_to_user_rows"],
        "rollback_eligible_rows": payload["rollback_eligible_rows"],
        "db_writes": payload["db_writes"],
    }, ensure_ascii=False, sort_keys=True))
    if blocking_reasons:
        raise RuntimeError({"project_member_l3_mapped_write_impact_review_risk": blocking_reasons})


main()
