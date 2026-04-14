"""Readonly post-write review for partner 30-row write batch.

Run only through:

    DB_NAME=sc_demo make odoo.shell.exec < scripts/migration/partner_30_row_post_write_review.py

This script is read-only. It does not call create/write/unlink or commit.
"""

from __future__ import annotations

import csv
import json
from collections import Counter
from pathlib import Path


SAMPLE_CSV = Path("/mnt/artifacts/migration/partner_30_row_create_only_sample_v1.csv")
ROLLBACK_TARGET_CSV = Path("/mnt/artifacts/migration/partner_30_row_rollback_target_list_v1.csv")
OUTPUT_JSON = Path("/mnt/artifacts/migration/partner_30_row_post_write_review_result_v1.json")
EXPECTED_COUNT = 30
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
    if env.cr.dbname != "sc_demo":  # noqa: F821 - provided by Odoo shell
        raise RuntimeError({"db_name_not_sc_demo": env.cr.dbname})  # noqa: F821

    _sample_fields, sample_rows = read_csv(SAMPLE_CSV)
    _target_fields, target_rows = read_csv(ROLLBACK_TARGET_CSV)
    sample_ids = [clean(row.get("legacy_partner_id")) for row in sample_rows]
    sample_id_set = set(sample_ids)
    target_ids = [clean(row.get("legacy_partner_id")) for row in target_rows]
    target_partner_ids = [int(clean(row.get("partner_id"))) for row in target_rows if clean(row.get("partner_id"))]

    model = env["res.partner"].sudo()  # noqa: F821 - provided by Odoo shell
    records = model.search([("id", "in", target_partner_ids)], order="id")
    by_id = {rec.id: rec for rec in records}
    by_legacy = {}
    for rec in records:
        by_legacy.setdefault((rec.legacy_partner_source or "", rec.legacy_partner_id or ""), []).append(rec)

    missing_partner_ids = [partner_id for partner_id in target_partner_ids if partner_id not in by_id]
    target_input_duplicates = sorted(identity for identity, count in Counter(target_ids).items() if identity and count > 1)
    sample_duplicates = sorted(identity for identity, count in Counter(sample_ids).items() if identity and count > 1)
    out_of_scope_targets = []
    duplicate_legacy_matches = []
    missing_legacy_matches = []
    rows = []

    for target in target_rows:
        partner_id = int(clean(target.get("partner_id"))) if clean(target.get("partner_id")) else 0
        legacy_source = clean(target.get("legacy_partner_source"))
        legacy_id = clean(target.get("legacy_partner_id"))
        rec = by_id.get(partner_id)
        matches = by_legacy.get((legacy_source, legacy_id), [])
        if not matches:
            missing_legacy_matches.append({"legacy_partner_source": legacy_source, "legacy_partner_id": legacy_id})
        if len(matches) > 1:
            duplicate_legacy_matches.append(
                {
                    "legacy_partner_source": legacy_source,
                    "legacy_partner_id": legacy_id,
                    "ids": [item.id for item in matches],
                }
            )
        if legacy_source != LEGACY_SOURCE or legacy_id not in sample_id_set:
            out_of_scope_targets.append(
                {
                    "partner_id": partner_id,
                    "legacy_partner_source": legacy_source,
                    "legacy_partner_id": legacy_id,
                }
            )
        rows.append(
            {
                "partner_id": partner_id,
                "matched": bool(rec),
                "legacy_partner_source": legacy_source,
                "legacy_partner_id": legacy_id,
                "name": rec.name if rec else "",
                "match_count": len(matches),
                "in_sample": legacy_id in sample_id_set,
                "rollback_eligible": bool(rec)
                and legacy_source == LEGACY_SOURCE
                and legacy_id in sample_id_set
                and len(matches) == 1,
            }
        )

    blocking_reasons = []
    if len(sample_rows) != EXPECTED_COUNT:
        blocking_reasons.append("sample_not_30_rows")
    if len(target_rows) != EXPECTED_COUNT:
        blocking_reasons.append("rollback_target_not_30_rows")
    if sample_duplicates:
        blocking_reasons.append("sample_duplicate_legacy_partner_id")
    if target_input_duplicates:
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
        "mode": "partner_30_row_post_write_readonly_review",
        "database": env.cr.dbname,  # noqa: F821
        "rollback_key": "legacy_partner_source + legacy_partner_id",
        "sample_rows": len(sample_rows),
        "rollback_target_rows": len(target_rows),
        "matched_partner_rows": len(records),
        "missing_partner_ids": missing_partner_ids,
        "sample_duplicates": sample_duplicates,
        "target_input_duplicates": target_input_duplicates,
        "missing_legacy_matches": missing_legacy_matches,
        "duplicate_legacy_matches": duplicate_legacy_matches,
        "out_of_scope_targets": out_of_scope_targets,
        "blocking_reasons": blocking_reasons,
        "rollback_eligible_rows": sum(1 for row in rows if row["rollback_eligible"]),
        "rows": rows,
    }
    write_json(OUTPUT_JSON, payload)
    print(
        "ITER_1861_REVIEW_RESULT="
        + json.dumps(
            {
                "status": payload["status"],
                "sample_rows": payload["sample_rows"],
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
        raise RuntimeError({"rollback_dry_run_blocked": blocking_reasons})


main()
