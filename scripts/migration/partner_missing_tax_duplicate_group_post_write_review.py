"""Readonly review for missing-tax duplicate group partner write."""

from __future__ import annotations

import csv
import json
from collections import Counter
from pathlib import Path


DESIGN_CSV = Path("/mnt/artifacts/migration/partner_l4_missing_tax_duplicate_group_write_design_rows_v1.csv")
ROLLBACK_TARGET_CSV = Path("/mnt/artifacts/migration/partner_l4_missing_tax_duplicate_group_175_rollback_targets_v1.csv")
WRITE_RESULT_JSON = Path("/mnt/artifacts/migration/partner_l4_missing_tax_duplicate_group_175_write_result_v1.json")
OUTPUT_JSON = Path("/mnt/artifacts/migration/partner_l4_missing_tax_duplicate_group_175_post_write_review_result_v1.json")
EXPECTED_COUNT = 175


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
    _design_fields, design_rows = read_csv(DESIGN_CSV)
    _target_fields, target_rows = read_csv(ROLLBACK_TARGET_CSV)
    design_keys = [(clean(row.get("legacy_partner_source")), clean(row.get("legacy_partner_id"))) for row in design_rows]
    target_keys = [(clean(row.get("legacy_partner_source")), clean(row.get("legacy_partner_id"))) for row in target_rows]
    target_partner_ids = [int(clean(row.get("partner_id"))) for row in target_rows if clean(row.get("partner_id"))]
    design_key_set = set(design_keys)
    model = env["res.partner"].sudo()  # noqa: F821
    records = model.search([("id", "in", target_partner_ids)], order="id")
    by_id = {rec.id: rec for rec in records}
    by_legacy = {}
    for rec in records:
        by_legacy.setdefault((rec.legacy_partner_source or "", rec.legacy_partner_id or ""), []).append(rec)

    blocking_reasons = []
    design_duplicates = sorted(key for key, count in Counter(design_keys).items() if key[0] and key[1] and count > 1)
    target_duplicates = sorted(key for key, count in Counter(target_keys).items() if key[0] and key[1] and count > 1)
    missing_partner_ids = [partner_id for partner_id in target_partner_ids if partner_id not in by_id]
    duplicate_legacy_matches = []
    missing_legacy_matches = []
    out_of_scope_targets = []
    wrong_rank_targets = []
    rows = []
    for target in target_rows:
        partner_id = int(clean(target.get("partner_id"))) if clean(target.get("partner_id")) else 0
        legacy_source = clean(target.get("legacy_partner_source"))
        legacy_id = clean(target.get("legacy_partner_id"))
        key = (legacy_source, legacy_id)
        rec = by_id.get(partner_id)
        matches = by_legacy.get(key, [])
        if not matches:
            missing_legacy_matches.append({"legacy_partner_source": legacy_source, "legacy_partner_id": legacy_id})
        if len(matches) > 1:
            duplicate_legacy_matches.append({"legacy_partner_source": legacy_source, "legacy_partner_id": legacy_id, "ids": [item.id for item in matches]})
        if key not in design_key_set:
            out_of_scope_targets.append({"partner_id": partner_id, "legacy_partner_source": legacy_source, "legacy_partner_id": legacy_id})
        if rec and rec.customer_rank != 1:
            wrong_rank_targets.append({"partner_id": partner_id, "customer_rank": rec.customer_rank, "supplier_rank": rec.supplier_rank})
        rows.append({"partner_id": partner_id, "rollback_eligible": bool(rec) and key in design_key_set and len(matches) == 1})

    if write_result.get("status") != "PASS":
        blocking_reasons.append("write_result_not_pass")
    if write_result.get("created") != EXPECTED_COUNT:
        blocking_reasons.append("write_result_created_not_expected")
    if len(design_rows) != EXPECTED_COUNT:
        blocking_reasons.append("design_not_expected_rows")
    if len(target_rows) != EXPECTED_COUNT:
        blocking_reasons.append("rollback_target_not_expected_rows")
    if len(records) != EXPECTED_COUNT:
        blocking_reasons.append("matched_partner_rows_not_expected")
    if design_duplicates:
        blocking_reasons.append("design_duplicate_legacy_key")
    if target_duplicates:
        blocking_reasons.append("rollback_target_duplicate_legacy_key")
    if missing_partner_ids:
        blocking_reasons.append("rollback_target_partner_id_missing")
    if missing_legacy_matches:
        blocking_reasons.append("rollback_target_legacy_identity_missing")
    if duplicate_legacy_matches:
        blocking_reasons.append("duplicate_legacy_identity_matches")
    if out_of_scope_targets:
        blocking_reasons.append("out_of_scope_rollback_targets")
    if wrong_rank_targets:
        blocking_reasons.append("wrong_rank_targets")
    if any(not row["rollback_eligible"] for row in rows):
        blocking_reasons.append("not_all_rows_rollback_eligible")

    payload = {
        "status": "ROLLBACK_READY" if not blocking_reasons else "ROLLBACK_BLOCKED",
        "mode": "partner_missing_tax_duplicate_group_post_write_readonly_review",
        "database": env.cr.dbname,  # noqa: F821
        "rollback_key": "legacy_partner_source + legacy_partner_id",
        "design_rows": len(design_rows),
        "rollback_target_rows": len(target_rows),
        "matched_partner_rows": len(records),
        "rollback_eligible_rows": sum(1 for row in rows if row["rollback_eligible"]),
        "blocking_reasons": blocking_reasons,
        "design_duplicates": design_duplicates,
        "target_duplicates": target_duplicates,
        "missing_partner_ids": missing_partner_ids,
        "missing_legacy_matches": missing_legacy_matches,
        "duplicate_legacy_matches": duplicate_legacy_matches,
        "out_of_scope_targets": out_of_scope_targets,
        "wrong_rank_targets": wrong_rank_targets,
    }
    write_json(OUTPUT_JSON, payload)
    env.cr.rollback()  # noqa: F821
    print(
        "PARTNER_MISSING_TAX_DUPLICATE_GROUP_POST_WRITE_REVIEW="
        + json.dumps(
            {
                "status": payload["status"],
                "design_rows": payload["design_rows"],
                "rollback_target_rows": payload["rollback_target_rows"],
                "matched_partner_rows": payload["matched_partner_rows"],
                "rollback_eligible_rows": payload["rollback_eligible_rows"],
                "blocking_reasons": payload["blocking_reasons"],
            },
            ensure_ascii=False,
            sort_keys=True,
        )
    )
    if blocking_reasons:
        raise RuntimeError({"partner_missing_tax_duplicate_group_post_write_review_failed": blocking_reasons})


main()
