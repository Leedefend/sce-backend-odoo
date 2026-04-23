"""Create-only 30-row partner write for Odoo shell.

Run only through:

    DB_NAME=sc_demo make odoo.shell.exec < scripts/migration/partner_30_row_create_only_write.py

The script expects the Odoo shell global ``env``. It refuses update/upsert,
writes exactly the approved 30-row partner sample, and emits rollback targets
keyed only by legacy_partner_source + legacy_partner_id.
"""

from __future__ import annotations

import csv
import json
from collections import Counter
from pathlib import Path


SAMPLE_CSV = Path("/mnt/artifacts/migration/partner_30_row_create_only_sample_v1.csv")
EVIDENCE_CSV = Path("/mnt/artifacts/migration/partner_strong_evidence_dry_run_input_v1.csv")
PRE_WRITE_SNAPSHOT_CSV = Path("/mnt/artifacts/migration/partner_30_row_pre_write_snapshot_v1.csv")
POST_WRITE_SNAPSHOT_CSV = Path("/mnt/artifacts/migration/partner_30_row_post_write_snapshot_v1.csv")
WRITE_RESULT_JSON = Path("/mnt/artifacts/migration/partner_30_row_write_result_v1.json")
ROLLBACK_TARGET_CSV = Path("/mnt/artifacts/migration/partner_30_row_rollback_target_list_v1.csv")

EXPECTED_COUNT = 30
SOURCE_TABLE = "T_Base_CooperatCompany"
LEGACY_SOURCE = "cooperat_company"
SAFE_FIELDS = [
    "name",
    "company_type",
    "legacy_partner_id",
    "legacy_partner_source",
    "legacy_partner_name",
    "legacy_credit_code",
    "legacy_tax_no",
    "legacy_deleted_flag",
    "legacy_source_evidence",
]


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


def legacy_domain(ids):
    return [
        ("legacy_partner_source", "=", LEGACY_SOURCE),
        ("legacy_partner_id", "in", ids),
    ]


def snapshot(model, path, ids):
    records = model.search(legacy_domain(ids), order="legacy_partner_id,id")
    rows = []
    for rec in records:
        rows.append(
            {
                "id": rec.id,
                "legacy_partner_source": rec.legacy_partner_source or "",
                "legacy_partner_id": rec.legacy_partner_id or "",
                "name": rec.name or "",
                "legacy_partner_name": rec.legacy_partner_name or "",
                "legacy_credit_code": rec.legacy_credit_code or "",
                "legacy_tax_no": rec.legacy_tax_no or "",
                "legacy_deleted_flag": rec.legacy_deleted_flag or "",
                "legacy_source_evidence": rec.legacy_source_evidence or "",
            }
        )
    write_csv(
        path,
        [
            "id",
            "legacy_partner_source",
            "legacy_partner_id",
            "name",
            "legacy_partner_name",
            "legacy_credit_code",
            "legacy_tax_no",
            "legacy_deleted_flag",
            "legacy_source_evidence",
        ],
        rows,
    )
    return records


def build_evidence_index():
    _columns, rows = read_csv(EVIDENCE_CSV)
    return {clean(row.get("legacy_partner_id")): row for row in rows if clean(row.get("legacy_partner_id"))}


def build_create_vals(sample_row, evidence_row):
    legacy_id = clean(sample_row.get("legacy_partner_id"))
    partner_name = clean(sample_row.get("partner_name"))
    source = clean(sample_row.get("source"))
    if source != SOURCE_TABLE:
        raise RuntimeError({"unsupported_source": source, "legacy_partner_id": legacy_id})
    return {
        "name": partner_name,
        "company_type": "company",
        "legacy_partner_id": legacy_id,
        "legacy_partner_source": LEGACY_SOURCE,
        "legacy_partner_name": partner_name,
        "legacy_credit_code": clean(evidence_row.get("company_credit_code")),
        "legacy_tax_no": clean(evidence_row.get("company_tax_no")),
        "legacy_deleted_flag": "",
        "legacy_source_evidence": clean(evidence_row.get("source_evidence")) or "C_JFHKLR.SGHTID/WLDWID single-counterparty contracts",
    }


def main():
    if env.cr.dbname != "sc_demo":  # noqa: F821 - provided by Odoo shell
        raise RuntimeError({"db_name_not_sc_demo": env.cr.dbname})  # noqa: F821

    model = env["res.partner"].sudo()  # noqa: F821 - provided by Odoo shell
    missing_model_fields = [field for field in SAFE_FIELDS if field not in model._fields]
    if missing_model_fields:
        raise RuntimeError({"missing_model_fields": missing_model_fields})

    sample_columns, sample_rows = read_csv(SAMPLE_CSV)
    required_columns = {
        "row_no",
        "legacy_partner_id",
        "partner_name",
        "source",
        "dry_run_action",
        "blockers",
    }
    missing_columns = sorted(required_columns - set(sample_columns))
    if missing_columns:
        raise RuntimeError({"missing_sample_columns": missing_columns})

    evidence_by_id = build_evidence_index()
    ids = [clean(row.get("legacy_partner_id")) for row in sample_rows]
    id_counts = Counter(ids)

    precheck_errors = []
    if len(sample_rows) != EXPECTED_COUNT:
        precheck_errors.append({"error": "sample_not_30_rows", "rows": len(sample_rows)})

    create_vals = []
    for index, row in enumerate(sample_rows, start=2):
        legacy_id = clean(row.get("legacy_partner_id"))
        row_errors = []
        if not legacy_id:
            row_errors.append("missing_legacy_partner_id")
        if legacy_id and id_counts[legacy_id] > 1:
            row_errors.append("duplicate_legacy_partner_id_in_sample")
        if clean(row.get("dry_run_action")) != "create_candidate":
            row_errors.append("row_not_create_candidate")
        if clean(row.get("blockers")):
            row_errors.append("row_has_blockers")
        if clean(row.get("source")) != SOURCE_TABLE:
            row_errors.append("unsupported_source")
        if not clean(row.get("partner_name")):
            row_errors.append("missing_partner_name")
        if legacy_id not in evidence_by_id:
            row_errors.append("missing_evidence_row")
        if row_errors:
            for error in row_errors:
                precheck_errors.append({"line": index, "legacy_partner_id": legacy_id, "error": error})
            continue
        create_vals.append(build_create_vals(row, evidence_by_id[legacy_id]))

    existing = snapshot(model, PRE_WRITE_SNAPSHOT_CSV, [identity for identity in ids if identity])
    if existing:
        precheck_errors.append(
            {
                "error": "target_identity_not_empty_before_write",
                "matches": [
                    {
                        "id": rec.id,
                        "legacy_partner_source": rec.legacy_partner_source or "",
                        "legacy_partner_id": rec.legacy_partner_id or "",
                        "name": rec.name or "",
                    }
                    for rec in existing
                ],
            }
        )
    if precheck_errors:
        env.cr.rollback()  # noqa: F821
        raise RuntimeError({"pre_write_check_failed": precheck_errors})

    created = []
    try:
        for vals in create_vals:
            unsafe_fields = sorted(set(vals) - set(SAFE_FIELDS))
            if unsafe_fields:
                raise RuntimeError({"unsafe_fields": unsafe_fields})
            rec = model.create({field: value for field, value in vals.items() if value})
            created.append(
                {
                    "id": rec.id,
                    "legacy_partner_source": rec.legacy_partner_source or "",
                    "legacy_partner_id": rec.legacy_partner_id or "",
                    "name": rec.name or "",
                    "legacy_partner_name": rec.legacy_partner_name or "",
                    "legacy_source_evidence": rec.legacy_source_evidence or "",
                }
            )
        env.cr.commit()  # noqa: F821 - explicit authorized write commit
    except Exception:
        env.cr.rollback()  # noqa: F821
        raise

    post_records = snapshot(model, POST_WRITE_SNAPSHOT_CSV, ids)
    grouped = {}
    for rec in post_records:
        grouped.setdefault(rec.legacy_partner_id or "", []).append(rec)
    duplicate_matches = [
        {"legacy_partner_id": identity, "ids": [rec.id for rec in records]}
        for identity, records in sorted(grouped.items())
        if len(records) > 1
    ]
    missing_ids = [identity for identity in ids if identity not in grouped]
    out_of_scope = [
        {
            "id": rec.id,
            "legacy_partner_source": rec.legacy_partner_source or "",
            "legacy_partner_id": rec.legacy_partner_id or "",
            "name": rec.name or "",
        }
        for rec in post_records
        if (rec.legacy_partner_source or "") != LEGACY_SOURCE or (rec.legacy_partner_id or "") not in id_counts
    ]

    rollback_rows = []
    for row in sample_rows:
        legacy_id = clean(row.get("legacy_partner_id"))
        for rec in grouped.get(legacy_id, []):
            rollback_rows.append(
                {
                    "run_id": "ITER-2026-04-13-1860",
                    "partner_id": rec.id,
                    "legacy_partner_source": rec.legacy_partner_source or "",
                    "legacy_partner_id": rec.legacy_partner_id or "",
                    "partner_name": rec.name or "",
                    "legacy_source_evidence": rec.legacy_source_evidence or "",
                    "sample_row_no": clean(row.get("row_no")),
                    "write_action_result": "created",
                }
            )
    write_csv(
        ROLLBACK_TARGET_CSV,
        [
            "run_id",
            "partner_id",
            "legacy_partner_source",
            "legacy_partner_id",
            "partner_name",
            "legacy_source_evidence",
            "sample_row_no",
            "write_action_result",
        ],
        rollback_rows,
    )

    post_errors = []
    if len(created) != EXPECTED_COUNT:
        post_errors.append({"error": "created_count_not_30", "created": len(created)})
    if len(post_records) != EXPECTED_COUNT:
        post_errors.append({"error": "post_write_identity_count_mismatch", "count": len(post_records)})
    if duplicate_matches:
        post_errors.append({"error": "duplicate_legacy_partner_identity", "rows": duplicate_matches})
    if missing_ids:
        post_errors.append({"error": "missing_post_write_identity", "ids": missing_ids})
    if out_of_scope:
        post_errors.append({"error": "out_of_scope_post_write_match", "rows": out_of_scope})

    payload = {
        "status": "PASS" if not post_errors else "FAIL",
        "mode": "partner_30_row_create_only_write",
        "database": env.cr.dbname,  # noqa: F821
        "input": str(SAMPLE_CSV),
        "row_count": len(sample_rows),
        "safe_field_count": len(SAFE_FIELDS),
        "rollback_key": "legacy_partner_source + legacy_partner_id",
        "summary": {
            "created": len(created),
            "updated": 0,
            "errors": len(post_errors),
            "post_write_identity_count": len(post_records),
            "rollback_targets": len(rollback_rows),
        },
        "created": created,
        "post_errors": post_errors,
        "artifacts": {
            "pre_write_snapshot": str(PRE_WRITE_SNAPSHOT_CSV),
            "post_write_snapshot": str(POST_WRITE_SNAPSHOT_CSV),
            "rollback_target_list": str(ROLLBACK_TARGET_CSV),
        },
    }
    write_json(WRITE_RESULT_JSON, payload)
    print("ITER_1860_WRITE_RESULT=" + json.dumps(payload["summary"], ensure_ascii=False, sort_keys=True))
    if post_errors:
        raise RuntimeError({"post_write_check_failed": post_errors})


main()
