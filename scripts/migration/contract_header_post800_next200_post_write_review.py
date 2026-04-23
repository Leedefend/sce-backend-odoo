"""Readonly post-write review for the post800 next 200-row contract header write batch."""

from __future__ import annotations

import csv
import json
from collections import Counter
from pathlib import Path


ROLLBACK_TARGET_CSV = Path("/mnt/artifacts/migration/contract_header_post800_next200_rollback_targets_v1.csv")
WRITE_RESULT_JSON = Path("/mnt/artifacts/migration/contract_header_post800_next200_write_result_v1.json")
OUTPUT_JSON = Path("/mnt/artifacts/migration/contract_header_post800_next200_post_write_review_result_v1.json")
EXPECTED_COUNT = 200


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
    _target_fields, target_rows = read_csv(ROLLBACK_TARGET_CSV)
    legacy_ids = [clean(row.get("legacy_contract_id")) for row in target_rows]
    contract_ids = [int(clean(row.get("contract_id"))) for row in target_rows if clean(row.get("contract_id"))]

    model = env["construction.contract"].sudo()  # noqa: F821
    records = model.search([("id", "in", contract_ids)], order="id")
    by_id = {rec.id: rec for rec in records}
    by_legacy = {}
    for rec in records:
        by_legacy.setdefault(rec.legacy_contract_id or "", []).append(rec)

    target_input_duplicates = sorted(identity for identity, count in Counter(legacy_ids).items() if identity and count > 1)
    missing_contract_ids = [contract_id for contract_id in contract_ids if contract_id not in by_id]
    missing_legacy_matches = []
    duplicate_legacy_matches = []
    rows = []

    for target in target_rows:
        contract_id = int(clean(target.get("contract_id"))) if clean(target.get("contract_id")) else 0
        legacy_contract_id = clean(target.get("legacy_contract_id"))
        rec = by_id.get(contract_id)
        matches = by_legacy.get(legacy_contract_id, [])
        if not matches:
            missing_legacy_matches.append({"legacy_contract_id": legacy_contract_id})
        if len(matches) > 1:
            duplicate_legacy_matches.append({"legacy_contract_id": legacy_contract_id, "ids": [item.id for item in matches]})
        line_count = len(rec.line_ids) if rec else None
        rollback_eligible = bool(rec) and len(matches) == 1 and rec.state == "draft" and line_count == 0 and not rec.is_locked
        rows.append(
            {
                "contract_id": contract_id,
                "matched": bool(rec),
                "legacy_contract_id": legacy_contract_id,
                "name": rec.name if rec else "",
                "state": rec.state if rec else "",
                "line_count": line_count,
                "is_locked": bool(rec.is_locked) if rec else None,
                "match_count": len(matches),
                "rollback_eligible": rollback_eligible,
            }
        )

    blocking_reasons = []
    if write_result.get("status") != "PASS":
        blocking_reasons.append("write_result_not_pass")
    if len(target_rows) != EXPECTED_COUNT:
        blocking_reasons.append("rollback_target_not_200_rows")
    if len(records) != EXPECTED_COUNT:
        blocking_reasons.append("matched_contract_rows_not_200")
    if target_input_duplicates:
        blocking_reasons.append("rollback_target_duplicate_legacy_contract_id")
    if missing_contract_ids:
        blocking_reasons.append("rollback_target_contract_id_missing")
    if missing_legacy_matches:
        blocking_reasons.append("rollback_target_legacy_identity_missing")
    if duplicate_legacy_matches:
        blocking_reasons.append("duplicate_legacy_identity_matches")
    if any(not row["rollback_eligible"] for row in rows):
        blocking_reasons.append("not_all_rows_rollback_eligible")

    payload = {
        "status": "ROLLBACK_READY" if not blocking_reasons else "ROLLBACK_BLOCKED",
        "mode": "contract_header_post800_next200_post_write_readonly_review",
        "database": env.cr.dbname,  # noqa: F821
        "rollback_key": "legacy_contract_id",
        "target_rows": len(target_rows),
        "matched_contract_rows": len(records),
        "rollback_eligible_rows": sum(1 for row in rows if row["rollback_eligible"]),
        "missing_contract_ids": missing_contract_ids,
        "target_input_duplicates": target_input_duplicates,
        "missing_legacy_matches": missing_legacy_matches,
        "duplicate_legacy_matches": duplicate_legacy_matches,
        "blocking_reasons": blocking_reasons,
        "rows": rows,
    }
    write_json(OUTPUT_JSON, payload)
    print(
        "CONTRACT_HEADER_POST800_NEXT200_POST_WRITE_REVIEW="
        + json.dumps(
            {
                "status": payload["status"],
                "target_rows": payload["target_rows"],
                "matched_contract_rows": payload["matched_contract_rows"],
                "rollback_eligible_rows": payload["rollback_eligible_rows"],
                "blocking_reasons": payload["blocking_reasons"],
            },
            ensure_ascii=False,
            sort_keys=True,
        )
    )
    if blocking_reasons:
        raise RuntimeError({"contract_header_post800_next200_post_write_review_failed": blocking_reasons})


main()
