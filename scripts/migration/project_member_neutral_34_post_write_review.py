"""Readonly post-write review for 34-row project_member neutral carrier write."""

from __future__ import annotations

import csv
import json
from collections import Counter
from pathlib import Path


SAFE_SLICE_CSV = Path("/mnt/artifacts/migration/project_member_no_placeholder_safe_slice_v1.csv")
ROLLBACK_TARGET_CSV = Path("/mnt/artifacts/migration/project_member_rollback_targets_v1.csv")
WRITE_RESULT_JSON = Path("/mnt/artifacts/migration/project_member_neutral_34_write_result_v1.json")
OUTPUT_JSON = Path("/mnt/artifacts/migration/project_member_neutral_34_post_write_review_result_v1.json")

RUN_ID = "ITER-2026-04-14-0030N"
EXPECTED_COUNT = 34
TARGET_MODEL = "sc.project.member.staging"


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
    _safe_fields, safe_rows = read_csv(SAFE_SLICE_CSV)
    _target_fields, target_rows = read_csv(ROLLBACK_TARGET_CSV)
    legacy_ids = [clean(row.get("legacy_member_id")) for row in safe_rows]
    target_ids = [int(clean(row.get("neutral_id"))) for row in target_rows if clean(row.get("neutral_id"))]
    model = env[TARGET_MODEL].sudo()  # noqa: F821
    records = model.search([("id", "in", target_ids), ("import_batch", "=", RUN_ID)], order="id")
    project_ids = [int(clean(row.get("project_id"))) for row in target_rows if clean(row.get("project_id"))]
    user_ids = [int(clean(row.get("user_id"))) for row in target_rows if clean(row.get("user_id"))]
    safe_pairs = {(str(project_id), str(user_id)) for project_id, user_id in zip(project_ids, user_ids)}
    responsibility_records = env["project.responsibility"].sudo().search([("project_id", "in", project_ids), ("user_id", "in", user_ids)])  # noqa: F821
    responsibility_pair_matches = [
        {
            "id": record.id,
            "project_id": record.project_id.id,
            "user_id": record.user_id.id,
            "role_key": record.role_key or "",
        }
        for record in responsibility_records
        if (str(record.project_id.id), str(record.user_id.id)) in safe_pairs
    ]
    records_by_legacy = {}
    for record in records:
        records_by_legacy.setdefault(record.legacy_member_id or "", []).append(record)

    blocking_reasons = []
    if write_result.get("status") != "PASS":
        blocking_reasons.append("write_result_not_pass")
    if write_result.get("project_responsibility_writes") != 0:
        blocking_reasons.append("project_responsibility_write_detected")
    if responsibility_pair_matches:
        blocking_reasons.append("project_responsibility_pair_match_detected")
    if write_result.get("visibility_changed"):
        blocking_reasons.append("visibility_changed")
    if len(safe_rows) != EXPECTED_COUNT:
        blocking_reasons.append("safe_slice_not_34_rows")
    if len(target_rows) != EXPECTED_COUNT:
        blocking_reasons.append("rollback_targets_not_34_rows")
    if len(records) != EXPECTED_COUNT:
        blocking_reasons.append("matched_neutral_records_not_34")

    duplicate_safe_ids = [key for key, count in Counter(legacy_ids).items() if key and count > 1]
    duplicate_record_ids = [key for key, value in records_by_legacy.items() if key and len(value) > 1]
    if duplicate_safe_ids:
        blocking_reasons.append("duplicate_safe_legacy_member_id")
    if duplicate_record_ids:
        blocking_reasons.append("duplicate_neutral_legacy_member_id")

    rows = []
    safe_id_set = set(legacy_ids)
    for record in records:
        rollback_eligible = (
            record.legacy_member_id in safe_id_set
            and record.import_batch == RUN_ID
            and record.role_fact_status == "missing"
            and len(records_by_legacy.get(record.legacy_member_id or "", [])) == 1
        )
        if not rollback_eligible:
            blocking_reasons.append("not_all_rows_rollback_eligible")
        rows.append(
            {
                "neutral_id": record.id,
                "legacy_member_id": record.legacy_member_id or "",
                "project_id": record.project_id.id,
                "user_id": record.user_id.id,
                "role_fact_status": record.role_fact_status,
                "import_batch": record.import_batch,
                "rollback_eligible": rollback_eligible,
            }
        )

    blocking_reasons = sorted(set(blocking_reasons))
    payload = {
        "status": "ROLLBACK_READY" if not blocking_reasons else "ROLLBACK_BLOCKED",
        "mode": "project_member_neutral_34_post_write_review",
        "database": env.cr.dbname,  # noqa: F821
        "target_model": TARGET_MODEL,
        "safe_slice_rows": len(safe_rows),
        "rollback_target_rows": len(target_rows),
        "matched_neutral_records": len(records),
        "rollback_eligible_rows": sum(1 for row in rows if row["rollback_eligible"]),
        "project_responsibility_pair_matches": responsibility_pair_matches,
        "blocking_reasons": blocking_reasons,
        "rows": rows,
    }
    write_json(OUTPUT_JSON, payload)
    env.cr.rollback()  # noqa: F821
    print("PROJECT_MEMBER_NEUTRAL_34_POST_WRITE_REVIEW=" + json.dumps({
        "status": payload["status"],
        "matched_neutral_records": payload["matched_neutral_records"],
        "rollback_eligible_rows": payload["rollback_eligible_rows"],
        "blocking_reasons": payload["blocking_reasons"],
    }, ensure_ascii=False, sort_keys=True))
    if blocking_reasons:
        raise RuntimeError({"project_member_neutral_post_write_review_failed": blocking_reasons})


main()
