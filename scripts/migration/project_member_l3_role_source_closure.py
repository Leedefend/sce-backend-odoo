"""Approved-only closure gate for L3 project_member responsibility candidates."""

from __future__ import annotations

import csv
import json
import os
from pathlib import Path


RUN_ID = "ITER-2026-04-14-L3-ROLE-SOURCE-CLOSURE"
SAMPLE_SIZE = 3
VALID_ROLE_KEYS = {"manager", "cost", "finance", "cashier", "material", "safety", "quality", "document"}

ARTIFACT_ROOT = Path("/mnt/artifacts") if Path("/mnt/artifacts").exists() else Path("artifacts")
MIGRATION_DIR = ARTIFACT_ROOT / "migration"

SOURCE_JSON = MIGRATION_DIR / "project_member_l3_role_source_review_packet_v1.json"
CHECKLIST_CSV = MIGRATION_DIR / "project_member_l3_business_review_checklist_v1.csv"
CHECKLIST_JSON = MIGRATION_DIR / "project_member_l3_business_review_checklist_v1.json"
RULE_JSON = MIGRATION_DIR / "project_member_l3_role_source_rule_v1.json"
DRY_RUN_JSON = MIGRATION_DIR / "project_member_l3_apply_dry_run_result_v1.json"
WRITE_RESULT_JSON = MIGRATION_DIR / "project_member_l3_apply_write_result_v1.json"
AUDIT_JSON = MIGRATION_DIR / "project_member_l3_post_write_audit_result_v1.json"
ROLLBACK_CSV = MIGRATION_DIR / "project_member_l3_responsibility_rollback_targets_v1.csv"


def clean(value):
    return ("" if value is None else str(value)).strip()


def boolish(value):
    return clean(value).lower() in {"1", "true", "yes", "y", "approved"}


def write_json(path, payload):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def read_csv(path):
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        return list(reader.fieldnames or []), [dict(row) for row in reader]


def write_csv(path, fieldnames, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def load_source_rows():
    source = json.loads(SOURCE_JSON.read_text(encoding="utf-8"))
    if source.get("status") != "PASS":
        raise RuntimeError({"l3_review_packet_not_pass": source.get("status")})
    rows = list(source.get("review_packet") or [])
    if len(rows) != 10:
        raise RuntimeError({"l3_review_packet_count_not_10": len(rows)})
    return rows


def rule_payload():
    return {
        "status": "FROZEN",
        "run_id": RUN_ID,
        "sample_size": SAMPLE_SIZE,
        "valid_role_keys": sorted(VALID_ROLE_KEYS),
        "write_rule": {
            "business_decision": "approved",
            "role_source_evidence": "required",
            "business_reviewer": "required",
            "proposed_role_key": "required_valid_selection",
            "sample_scope": "first_3_review_rows_only",
            "default_role_allowed": False,
            "role_key_fabrication_allowed": False,
        },
        "forbidden": [
            "write_pending_or_rejected_rows",
            "write_more_than_3_rows",
            "modify_acl_or_record_rule",
            "infer_role_key_from_evidence_count",
            "use_migration_authorization_as_business_role_source",
        ],
    }


def checklist_rows():
    rows = []
    for row in load_source_rows():
        review_rank = int(row["review_rank"])
        rows.append(
            {
                "review_rank": review_rank,
                "sample_scope": "yes" if review_rank <= SAMPLE_SIZE else "no",
                "pair_key": row["pair_key"],
                "project_id": row["project_id"],
                "project_name": row["project_name"],
                "user_id": row["user_id"],
                "user_name": row["user_name"],
                "evidence_count": row["evidence_count"],
                "candidate_level": row["candidate_level"],
                "role_fact_status": row["role_fact_status"],
                "proposed_role_key": clean(row.get("proposed_role_key")),
                "role_source_evidence": clean(row.get("role_source_evidence")),
                "business_reviewer": clean(row.get("business_reviewer")),
                "business_decision": clean(row.get("business_decision")) or "pending",
                "approval_required": "yes",
                "write_allowed": "no",
                "allowed_role_keys": ",".join(sorted(VALID_ROLE_KEYS)),
            }
        )
    return rows


def ensure_checklist(refresh=False):
    if refresh or not CHECKLIST_CSV.exists():
        rows = checklist_rows()
        fields = [
            "review_rank",
            "sample_scope",
            "pair_key",
            "project_id",
            "project_name",
            "user_id",
            "user_name",
            "evidence_count",
            "candidate_level",
            "role_fact_status",
            "proposed_role_key",
            "role_source_evidence",
            "business_reviewer",
            "business_decision",
            "approval_required",
            "write_allowed",
            "allowed_role_keys",
        ]
        write_csv(CHECKLIST_CSV, fields, rows)
        write_json(
            CHECKLIST_JSON,
            {
                "status": "PASS",
                "run_id": RUN_ID,
                "total_l3_rows": len(rows),
                "sample_rows": SAMPLE_SIZE,
                "rows": rows,
            },
        )
    write_json(RULE_JSON, rule_payload())


def load_checklist():
    ensure_checklist(refresh=False)
    _fields, rows = read_csv(CHECKLIST_CSV)
    return rows


def classify_rows(rows):
    selected = []
    blocked = []
    outside_approved = []
    for row in rows:
        review_rank = int(clean(row.get("review_rank")) or "0")
        is_sample = review_rank <= SAMPLE_SIZE
        is_approved = clean(row.get("business_decision")).lower() == "approved"
        role_key = clean(row.get("proposed_role_key"))
        reasons = []
        if not is_sample and is_approved:
            outside_approved.append(row)
            reasons.append("approved_outside_3_row_sample_scope")
        if is_sample:
            if not is_approved:
                reasons.append("business_decision_not_approved")
            if role_key not in VALID_ROLE_KEYS:
                reasons.append("invalid_or_missing_proposed_role_key")
            if not clean(row.get("role_source_evidence")):
                reasons.append("missing_role_source_evidence")
            if not clean(row.get("business_reviewer")):
                reasons.append("missing_business_reviewer")
            if reasons:
                blocked.append({**row, "blocking_reasons": reasons})
            else:
                selected.append(row)
    if outside_approved:
        blocked.extend({**row, "blocking_reasons": ["approved_outside_3_row_sample_scope"]} for row in outside_approved)
    return selected, blocked


def dry_run():
    rows = load_checklist()
    selected, blocked = classify_rows(rows)
    status = "PASS" if len(selected) == SAMPLE_SIZE and not blocked else "BLOCKED_BY_APPROVAL"
    payload = {
        "status": status,
        "run_id": RUN_ID,
        "mode": "dry-run",
        "sample_size": SAMPLE_SIZE,
        "total_l3_rows": len(rows),
        "approved_sample_rows": len(selected),
        "blocked_rows": len(blocked),
        "write_allowed": status == "PASS",
        "db_writes": 0,
        "selected_rows": selected,
        "blocked_rows_detail": blocked,
    }
    write_json(DRY_RUN_JSON, payload)
    print("PROJECT_MEMBER_L3_ROLE_SOURCE_DRY_RUN=" + json.dumps({
        "status": payload["status"],
        "approved_sample_rows": payload["approved_sample_rows"],
        "blocked_rows": payload["blocked_rows"],
        "write_allowed": payload["write_allowed"],
        "db_writes": payload["db_writes"],
    }, ensure_ascii=False, sort_keys=True))
    return payload


def write_empty_rollback():
    write_csv(
        ROLLBACK_CSV,
        ["run_id", "responsibility_id", "project_id", "user_id", "role_key", "pair_key", "write_action_result"],
        [],
    )


def ensure_odoo_env():
    if "env" not in globals():
        raise RuntimeError({"odoo_env_required": True})
    if env.cr.dbname != "sc_demo":  # noqa: F821
        raise RuntimeError({"db_name_not_sc_demo": env.cr.dbname})  # noqa: F821


def apply():
    ensure_odoo_env()
    dry = dry_run()
    if dry["status"] != "PASS":
        env.cr.rollback()  # noqa: F821
        write_empty_rollback()
        payload = {
            "status": "BLOCKED_BY_APPROVAL",
            "run_id": RUN_ID,
            "mode": "apply",
            "created": 0,
            "updated": 0,
            "db_writes": 0,
            "write_allowed": False,
            "blocking_reasons": ["approved_3_row_sample_required"],
            "dry_run_status": dry["status"],
        }
        write_json(WRITE_RESULT_JSON, payload)
        print("PROJECT_MEMBER_L3_ROLE_SOURCE_APPLY=" + json.dumps(payload, ensure_ascii=False, sort_keys=True))
        return payload

    responsibility = env["project.responsibility"].sudo()  # noqa: F821
    created = []
    try:
        for row in dry["selected_rows"]:
            project_id = int(clean(row["project_id"]))
            user_id = int(clean(row["user_id"]))
            role_key = clean(row["proposed_role_key"])
            existing = responsibility.search(
                [("project_id", "=", project_id), ("user_id", "=", user_id), ("role_key", "=", role_key)],
                limit=1,
            )
            if existing:
                raise RuntimeError({"existing_project_responsibility_conflict": existing.id, "pair_key": row["pair_key"], "role_key": role_key})
            rec = responsibility.create(
                {
                    "project_id": project_id,
                    "user_id": user_id,
                    "role_key": role_key,
                    "is_primary": False,
                    "note": (
                        f"{RUN_ID}; pair_key={row['pair_key']}; "
                        f"role_source_evidence={clean(row['role_source_evidence'])}; "
                        f"business_reviewer={clean(row['business_reviewer'])}"
                    ),
                }
            )
            created.append(
                {
                    "responsibility_id": rec.id,
                    "project_id": project_id,
                    "user_id": user_id,
                    "role_key": role_key,
                    "pair_key": row["pair_key"],
                    "write_action_result": "created",
                }
            )
        env.cr.commit()  # noqa: F821
    except Exception:
        env.cr.rollback()  # noqa: F821
        raise

    write_csv(
        ROLLBACK_CSV,
        ["run_id", "responsibility_id", "project_id", "user_id", "role_key", "pair_key", "write_action_result"],
        [{"run_id": RUN_ID, **row} for row in created],
    )
    payload = {
        "status": "PASS",
        "run_id": RUN_ID,
        "mode": "apply",
        "created": len(created),
        "updated": 0,
        "db_writes": len(created),
        "write_allowed": True,
        "created_rows": created,
        "rollback_targets": str(ROLLBACK_CSV),
    }
    write_json(WRITE_RESULT_JSON, payload)
    print("PROJECT_MEMBER_L3_ROLE_SOURCE_APPLY=" + json.dumps({
        "status": payload["status"],
        "created": payload["created"],
        "db_writes": payload["db_writes"],
    }, ensure_ascii=False, sort_keys=True))
    return payload


def audit():
    ensure_odoo_env()
    if not WRITE_RESULT_JSON.exists():
        payload = {"status": "SKIPPED_NO_WRITE_RESULT", "run_id": RUN_ID, "db_writes": 0}
        write_json(AUDIT_JSON, payload)
        print("PROJECT_MEMBER_L3_ROLE_SOURCE_AUDIT=" + json.dumps(payload, ensure_ascii=False, sort_keys=True))
        return payload
    write_result = json.loads(WRITE_RESULT_JSON.read_text(encoding="utf-8"))
    if write_result.get("status") != "PASS":
        env.cr.rollback()  # noqa: F821
        payload = {
            "status": "SKIPPED_NO_WRITE",
            "run_id": RUN_ID,
            "write_status": write_result.get("status"),
            "matched_records": 0,
            "rollback_eligible_rows": 0,
            "db_writes": 0,
            "blocking_reasons": write_result.get("blocking_reasons", []),
        }
        write_json(AUDIT_JSON, payload)
        print("PROJECT_MEMBER_L3_ROLE_SOURCE_AUDIT=" + json.dumps(payload, ensure_ascii=False, sort_keys=True))
        return payload

    _fields, rollback_rows = read_csv(ROLLBACK_CSV)
    responsibility = env["project.responsibility"].sudo()  # noqa: F821
    ids = [int(clean(row["responsibility_id"])) for row in rollback_rows if clean(row.get("responsibility_id"))]
    records = responsibility.browse(ids).exists()
    rows = []
    for record in records:
        rows.append(
            {
                "responsibility_id": record.id,
                "project_id": record.project_id.id,
                "user_id": record.user_id.id,
                "role_key": record.role_key,
                "rollback_eligible": bool(record.note and RUN_ID in record.note),
            }
        )
    blocking_reasons = []
    if len(rows) != SAMPLE_SIZE:
        blocking_reasons.append("matched_records_not_3")
    if any(not row["rollback_eligible"] for row in rows):
        blocking_reasons.append("rollback_eligibility_missing")
    env.cr.rollback()  # noqa: F821
    payload = {
        "status": "PASS" if not blocking_reasons else "BLOCKED",
        "run_id": RUN_ID,
        "write_status": write_result.get("status"),
        "matched_records": len(rows),
        "rollback_eligible_rows": sum(1 for row in rows if row["rollback_eligible"]),
        "db_writes": 0,
        "blocking_reasons": blocking_reasons,
        "rows": rows,
    }
    write_json(AUDIT_JSON, payload)
    print("PROJECT_MEMBER_L3_ROLE_SOURCE_AUDIT=" + json.dumps({
        "status": payload["status"],
        "matched_records": payload["matched_records"],
        "rollback_eligible_rows": payload["rollback_eligible_rows"],
        "blocking_reasons": payload["blocking_reasons"],
    }, ensure_ascii=False, sort_keys=True))
    return payload


def main():
    mode = clean(os.environ.get("PM_L3_ROLE_SOURCE_MODE") or "checklist")
    if mode == "checklist":
        ensure_checklist(refresh=True)
        print("PROJECT_MEMBER_L3_ROLE_SOURCE_CHECKLIST=" + json.dumps({
            "status": "PASS",
            "total_l3_rows": 10,
            "sample_size": SAMPLE_SIZE,
            "db_writes": 0,
        }, ensure_ascii=False, sort_keys=True))
    elif mode == "dry-run":
        ensure_checklist(refresh=False)
        dry_run()
    elif mode == "apply":
        ensure_checklist(refresh=False)
        apply()
    elif mode == "audit":
        audit()
    else:
        raise RuntimeError({"unknown_mode": mode})


main()
