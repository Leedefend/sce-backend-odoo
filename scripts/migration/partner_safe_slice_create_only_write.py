"""Create-only partner safe-slice write for Odoo shell."""

from __future__ import annotations

import csv
import json
from collections import Counter
from pathlib import Path


SAFE_SLICE_CSV = Path("/mnt/artifacts/migration/partner_safe_slice_v1.csv")
DRY_RUN_JSON = Path("/mnt/artifacts/migration/partner_dry_run_result_v1.json")
PRE_WRITE_SNAPSHOT_CSV = Path("/mnt/artifacts/migration/partner_safe_slice_pre_write_snapshot_v1.csv")
POST_WRITE_SNAPSHOT_CSV = Path("/mnt/artifacts/migration/partner_safe_slice_post_write_snapshot_v1.csv")
WRITE_RESULT_JSON = Path("/mnt/artifacts/migration/partner_write_result_v1.json")
ROLLBACK_TARGET_CSV = Path("/mnt/artifacts/migration/partner_rollback_targets_v1.csv")

EXPECTED_COUNT = 100
LEGACY_SOURCE = "cooperat_company"
RUN_ID = "ITER-2026-04-14-0029"
SAFE_FIELDS = [
    "name",
    "company_type",
    "phone",
    "email",
    "customer_rank",
    "supplier_rank",
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


def truthy(value):
    return clean(value).lower() in {"1", "true", "yes", "y", "是"}


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
    return [("legacy_partner_source", "=", LEGACY_SOURCE), ("legacy_partner_id", "in", ids)]


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
                "phone": rec.phone or "",
                "email": rec.email or "",
                "customer_rank": rec.customer_rank if "customer_rank" in model._fields else "",
                "supplier_rank": rec.supplier_rank if "supplier_rank" in model._fields else "",
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
            "phone",
            "email",
            "customer_rank",
            "supplier_rank",
        ],
        rows,
    )
    return records


def build_create_vals(row):
    legacy_id = clean(row.get("legacy_partner_id"))
    name = clean(row.get("partner_name"))
    tax_number = clean(row.get("tax_number"))
    source = clean(row.get("sources"))
    if source != "company":
        raise RuntimeError({"unsupported_safe_slice_source": source, "legacy_partner_id": legacy_id})
    return {
        "name": name,
        "company_type": "company",
        "phone": clean(row.get("phone")),
        "email": clean(row.get("email")),
        "customer_rank": 1 if truthy(row.get("customer_flag")) else 0,
        "supplier_rank": 1 if truthy(row.get("supplier_flag")) else 0,
        "legacy_partner_id": legacy_id,
        "legacy_partner_source": LEGACY_SOURCE,
        "legacy_partner_name": name,
        "legacy_credit_code": tax_number,
        "legacy_tax_no": tax_number,
        "legacy_deleted_flag": "",
        "legacy_source_evidence": "partner_safe_slice_v1:company:tax_number",
    }


def main():
    if env.cr.dbname != "sc_demo":  # noqa: F821
        raise RuntimeError({"db_name_not_sc_demo": env.cr.dbname})  # noqa: F821

    model = env["res.partner"].sudo()  # noqa: F821
    missing_model_fields = [field for field in SAFE_FIELDS if field not in model._fields]
    if missing_model_fields:
        raise RuntimeError({"missing_model_fields": missing_model_fields})

    dry_run = json.loads(DRY_RUN_JSON.read_text(encoding="utf-8"))
    if dry_run.get("status") != "PASS":
        raise RuntimeError({"dry_run_not_pass": dry_run.get("status")})
    if dry_run.get("safe_slice", {}).get("rows") != EXPECTED_COUNT:
        raise RuntimeError({"safe_slice_rows_not_100": dry_run.get("safe_slice", {}).get("rows")})

    columns, rows = read_csv(SAFE_SLICE_CSV)
    required_columns = {"legacy_partner_id", "partner_name", "tax_number", "sources", "merge_strategy"}
    missing_columns = sorted(required_columns - set(columns))
    if missing_columns:
        raise RuntimeError({"missing_safe_slice_columns": missing_columns})

    ids = [clean(row.get("legacy_partner_id")) for row in rows]
    id_counts = Counter(ids)
    precheck_errors = []
    if len(rows) != EXPECTED_COUNT:
        precheck_errors.append({"error": "safe_slice_not_100_rows", "rows": len(rows)})
    if any(count > 1 for count in id_counts.values()):
        precheck_errors.append({"error": "duplicate_legacy_partner_id_in_safe_slice", "ids": sorted([identity for identity, count in id_counts.items() if count > 1])})

    create_vals = []
    for index, row in enumerate(rows, start=2):
        row_errors = []
        if not clean(row.get("legacy_partner_id")):
            row_errors.append("missing_legacy_partner_id")
        if not clean(row.get("partner_name")):
            row_errors.append("missing_partner_name")
        if not clean(row.get("tax_number")):
            row_errors.append("missing_tax_number")
        if clean(row.get("sources")) != "company":
            row_errors.append("unsupported_source")
        if clean(row.get("merge_strategy")) != "create_single":
            row_errors.append("not_create_single")
        if row_errors:
            precheck_errors.extend({"line": index, "legacy_partner_id": clean(row.get("legacy_partner_id")), "error": error} for error in row_errors)
        else:
            create_vals.append(build_create_vals(row))

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
            rec = model.create({field: value for field, value in vals.items() if value not in ("", None)})
            created.append(
                {
                    "id": rec.id,
                    "legacy_partner_source": rec.legacy_partner_source or "",
                    "legacy_partner_id": rec.legacy_partner_id or "",
                    "name": rec.name or "",
                }
            )
        env.cr.commit()  # noqa: F821
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

    rollback_rows = []
    for rec in post_records:
        rollback_rows.append(
            {
                "run_id": RUN_ID,
                "partner_id": rec.id,
                "legacy_partner_source": rec.legacy_partner_source or "",
                "legacy_partner_id": rec.legacy_partner_id or "",
                "partner_name": rec.name or "",
                "write_action_result": "created",
            }
        )
    write_csv(
        ROLLBACK_TARGET_CSV,
        ["run_id", "partner_id", "legacy_partner_source", "legacy_partner_id", "partner_name", "write_action_result"],
        rollback_rows,
    )

    post_errors = []
    if len(created) != EXPECTED_COUNT:
        post_errors.append({"error": "created_count_not_100", "created": len(created)})
    if len(post_records) != EXPECTED_COUNT:
        post_errors.append({"error": "post_write_snapshot_not_100", "rows": len(post_records)})
    if len(rollback_rows) != EXPECTED_COUNT:
        post_errors.append({"error": "rollback_target_not_100", "rows": len(rollback_rows)})
    if missing_ids:
        post_errors.append({"error": "missing_ids_after_write", "ids": missing_ids})
    if duplicate_matches:
        post_errors.append({"error": "duplicate_legacy_identity_matches", "matches": duplicate_matches})

    payload = {
        "status": "PASS" if not post_errors else "FAIL",
        "mode": "partner_safe_slice_create_only_write",
        "database": env.cr.dbname,  # noqa: F821
        "input": str(SAFE_SLICE_CSV),
        "created": len(created),
        "updated": 0,
        "errors": len(post_errors),
        "rollback_target_rows": len(rollback_rows),
        "post_write_identity_count": len(post_records),
        "duplicate_matches": duplicate_matches,
        "missing_ids": missing_ids,
        "post_errors": post_errors,
        "created_rows": created,
        "artifacts": {
            "pre_write_snapshot": str(PRE_WRITE_SNAPSHOT_CSV),
            "post_write_snapshot": str(POST_WRITE_SNAPSHOT_CSV),
            "rollback_targets": str(ROLLBACK_TARGET_CSV),
        },
    }
    write_json(WRITE_RESULT_JSON, payload)
    print("PARTNER_SAFE_SLICE_WRITE_RESULT=" + json.dumps({
        "status": payload["status"],
        "created": payload["created"],
        "updated": payload["updated"],
        "errors": payload["errors"],
        "rollback_target_rows": payload["rollback_target_rows"],
    }, ensure_ascii=False, sort_keys=True))
    if post_errors:
        raise RuntimeError({"partner_safe_slice_write_failed": post_errors})


main()
