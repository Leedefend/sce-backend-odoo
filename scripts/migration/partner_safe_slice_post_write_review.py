"""Readonly post-write review for partner safe-slice write."""

from __future__ import annotations

import csv
import json
from collections import Counter
from pathlib import Path


SAFE_SLICE_CSV = Path("/mnt/artifacts/migration/partner_safe_slice_v1.csv")
ROLLBACK_TARGET_CSV = Path("/mnt/artifacts/migration/partner_rollback_targets_v1.csv")
WRITE_RESULT_JSON = Path("/mnt/artifacts/migration/partner_write_result_v1.json")
OUTPUT_JSON = Path("/mnt/artifacts/migration/partner_safe_slice_post_write_review_result_v1.json")
EXPECTED_COUNT = 100
LEGACY_SOURCE = "cooperat_company"


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
    _slice_fields, safe_slice_rows = read_csv(SAFE_SLICE_CSV)
    _target_fields, target_rows = read_csv(ROLLBACK_TARGET_CSV)
    sample_ids = [clean(row.get("legacy_partner_id")) for row in safe_slice_rows]
    target_ids = [clean(row.get("legacy_partner_id")) for row in target_rows]
    target_partner_ids = [int(clean(row.get("partner_id"))) for row in target_rows if clean(row.get("partner_id"))]
    sample_id_set = set(sample_ids)

    model = env["res.partner"].sudo()  # noqa: F821
    records = model.search([("id", "in", target_partner_ids)], order="id")
    by_id = {rec.id: rec for rec in records}
    by_legacy = {}
    for rec in records:
        by_legacy.setdefault((rec.legacy_partner_source or "", rec.legacy_partner_id or ""), []).append(rec)

    sample_duplicates = sorted(identity for identity, count in Counter(sample_ids).items() if identity and count > 1)
    target_duplicates = sorted(identity for identity, count in Counter(target_ids).items() if identity and count > 1)
    missing_partner_ids = [partner_id for partner_id in target_partner_ids if partner_id not in by_id]
    rows = []
    duplicate_legacy_matches = []
    missing_legacy_matches = []
    out_of_scope_targets = []
    for target in target_rows:
        partner_id = int(clean(target.get("partner_id"))) if clean(target.get("partner_id")) else 0
        legacy_source = clean(target.get("legacy_partner_source"))
        legacy_id = clean(target.get("legacy_partner_id"))
        rec = by_id.get(partner_id)
        matches = by_legacy.get((legacy_source, legacy_id), [])
        if not matches:
            missing_legacy_matches.append({"legacy_partner_source": legacy_source, "legacy_partner_id": legacy_id})
        if len(matches) > 1:
            duplicate_legacy_matches.append({"legacy_partner_source": legacy_source, "legacy_partner_id": legacy_id, "ids": [item.id for item in matches]})
        if legacy_source != LEGACY_SOURCE or legacy_id not in sample_id_set:
            out_of_scope_targets.append({"partner_id": partner_id, "legacy_partner_source": legacy_source, "legacy_partner_id": legacy_id})
        rows.append(
            {
                "partner_id": partner_id,
                "matched": bool(rec),
                "legacy_partner_source": legacy_source,
                "legacy_partner_id": legacy_id,
                "name": rec.name if rec else "",
                "match_count": len(matches),
                "in_safe_slice": legacy_id in sample_id_set,
                "rollback_eligible": bool(rec)
                and legacy_source == LEGACY_SOURCE
                and legacy_id in sample_id_set
                and len(matches) == 1,
            }
        )

    blocking_reasons = []
    if write_result.get("status") != "PASS":
        blocking_reasons.append("write_result_not_pass")
    if write_result.get("created") != EXPECTED_COUNT:
        blocking_reasons.append("write_result_created_not_100")
    if len(safe_slice_rows) != EXPECTED_COUNT:
        blocking_reasons.append("safe_slice_not_100_rows")
    if len(target_rows) != EXPECTED_COUNT:
        blocking_reasons.append("rollback_target_not_100_rows")
    if len(records) != EXPECTED_COUNT:
        blocking_reasons.append("matched_partner_rows_not_100")
    if sample_duplicates:
        blocking_reasons.append("safe_slice_duplicate_legacy_partner_id")
    if target_duplicates:
        blocking_reasons.append("rollback_target_duplicate_legacy_partner_id")
    if missing_partner_ids:
        blocking_reasons.append("rollback_target_partner_id_missing")
    if missing_legacy_matches:
        blocking_reasons.append("rollback_target_legacy_identity_missing")
    if duplicate_legacy_matches:
        blocking_reasons.append("duplicate_legacy_identity_matches")
    if out_of_scope_targets:
        blocking_reasons.append("out_of_scope_rollback_targets")
    if any(not row["rollback_eligible"] for row in rows):
        blocking_reasons.append("not_all_rows_rollback_eligible")

    payload = {
        "status": "ROLLBACK_READY" if not blocking_reasons else "ROLLBACK_BLOCKED",
        "mode": "partner_safe_slice_post_write_readonly_review",
        "database": env.cr.dbname,  # noqa: F821
        "rollback_key": "legacy_partner_source + legacy_partner_id",
        "safe_slice_rows": len(safe_slice_rows),
        "rollback_target_rows": len(target_rows),
        "matched_partner_rows": len(records),
        "rollback_eligible_rows": sum(1 for row in rows if row["rollback_eligible"]),
        "blocking_reasons": blocking_reasons,
        "sample_duplicates": sample_duplicates,
        "target_duplicates": target_duplicates,
        "missing_partner_ids": missing_partner_ids,
        "missing_legacy_matches": missing_legacy_matches,
        "duplicate_legacy_matches": duplicate_legacy_matches,
        "out_of_scope_targets": out_of_scope_targets,
        "rows": rows,
    }
    write_json(OUTPUT_JSON, payload)
    env.cr.rollback()  # noqa: F821
    print("PARTNER_SAFE_SLICE_POST_WRITE_REVIEW=" + json.dumps({
        "status": payload["status"],
        "safe_slice_rows": payload["safe_slice_rows"],
        "rollback_target_rows": payload["rollback_target_rows"],
        "matched_partner_rows": payload["matched_partner_rows"],
        "rollback_eligible_rows": payload["rollback_eligible_rows"],
        "blocking_reasons": payload["blocking_reasons"],
    }, ensure_ascii=False, sort_keys=True))
    if blocking_reasons:
        raise RuntimeError({"partner_safe_slice_post_write_review_failed": blocking_reasons})


main()
