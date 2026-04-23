"""Create partner records for same-tax company canonical rows."""

from __future__ import annotations

import csv
import json
from collections import Counter
from pathlib import Path


DESIGN_CSV = Path("/mnt/artifacts/migration/partner_l4_same_tax_company_canonical_20_write_design_rows_v1.csv")
PRE_WRITE_SNAPSHOT_CSV = Path("/mnt/artifacts/migration/partner_l4_same_tax_company_canonical_20_pre_write_snapshot_v1.csv")
POST_WRITE_SNAPSHOT_CSV = Path("/mnt/artifacts/migration/partner_l4_same_tax_company_canonical_20_post_write_snapshot_v1.csv")
WRITE_RESULT_JSON = Path("/mnt/artifacts/migration/partner_l4_same_tax_company_canonical_20_write_result_v1.json")
ROLLBACK_TARGET_CSV = Path("/mnt/artifacts/migration/partner_l4_same_tax_company_canonical_20_rollback_targets_v1.csv")
EXPECTED_COUNT = 20
RUN_ID = "ITER-2026-04-14-PARTNER-L4-SAME-TAX-COMPANY-CANONICAL-20-WRITE"
LEGACY_SOURCE = "cooperat_company"
SAFE_FIELDS = ["name", "company_type", "customer_rank", "supplier_rank", "legacy_partner_id", "legacy_partner_source", "legacy_partner_name", "legacy_credit_code", "legacy_tax_no", "legacy_source_evidence"]


def clean(value):
    return ("" if value is None else str(value)).strip()


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


def snapshot(model, path, ids):
    records = model.search([("legacy_partner_source", "=", LEGACY_SOURCE), ("legacy_partner_id", "in", ids)], order="legacy_partner_id,id")
    rows = []
    for rec in records:
        rows.append({"id": rec.id, "legacy_partner_source": rec.legacy_partner_source or "", "legacy_partner_id": rec.legacy_partner_id or "", "name": rec.name or "", "legacy_partner_name": rec.legacy_partner_name or "", "legacy_credit_code": rec.legacy_credit_code or "", "legacy_tax_no": rec.legacy_tax_no or "", "legacy_source_evidence": rec.legacy_source_evidence or "", "customer_rank": rec.customer_rank if "customer_rank" in model._fields else "", "supplier_rank": rec.supplier_rank if "supplier_rank" in model._fields else ""})
    write_csv(path, ["id", "legacy_partner_source", "legacy_partner_id", "name", "legacy_partner_name", "legacy_credit_code", "legacy_tax_no", "legacy_source_evidence", "customer_rank", "supplier_rank"], rows)
    return records


def main():
    if env.cr.dbname != "sc_demo":  # noqa: F821
        raise RuntimeError({"db_name_not_sc_demo": env.cr.dbname})  # noqa: F821
    model = env["res.partner"].sudo()  # noqa: F821
    missing_model_fields = [field for field in SAFE_FIELDS if field not in model._fields]
    if missing_model_fields:
        raise RuntimeError({"missing_model_fields": missing_model_fields})
    columns, rows = read_csv(DESIGN_CSV)
    required = {"proposed_action", "legacy_partner_source", "legacy_partner_id", "partner_name", "tax_number", "customer_flag", "supplier_flag", "rollback_key_source", "rollback_key_legacy_id"}
    precheck_errors = []
    missing_columns = sorted(required - set(columns))
    if missing_columns:
        precheck_errors.append({"error": "missing_design_columns", "columns": missing_columns})
    if len(rows) != EXPECTED_COUNT:
        precheck_errors.append({"error": "design_not_expected_rows", "rows": len(rows), "expected": EXPECTED_COUNT})
    ids = [clean(row.get("legacy_partner_id")) for row in rows]
    duplicate_ids = sorted(identity for identity, count in Counter(ids).items() if identity and count > 1)
    if duplicate_ids:
        precheck_errors.append({"error": "duplicate_legacy_partner_id_in_design", "ids": duplicate_ids})
    create_vals = []
    for index, row in enumerate(rows, start=2):
        row_errors = []
        if clean(row.get("proposed_action")) != "create_company_partner_with_canonical_tax_number":
            row_errors.append("proposed_action_mismatch")
        if clean(row.get("legacy_partner_source")) != LEGACY_SOURCE or clean(row.get("rollback_key_source")) != LEGACY_SOURCE:
            row_errors.append("legacy_source_mismatch")
        if clean(row.get("legacy_partner_id")) != clean(row.get("rollback_key_legacy_id")):
            row_errors.append("rollback_legacy_id_mismatch")
        if clean(row.get("customer_flag")) != "true" or clean(row.get("supplier_flag")) != "false":
            row_errors.append("rank_flag_mismatch")
        if not clean(row.get("legacy_partner_id")) or not clean(row.get("partner_name")) or not clean(row.get("tax_number")):
            row_errors.append("missing_required_value")
        if row_errors:
            precheck_errors.extend({"line": index, "legacy_partner_id": clean(row.get("legacy_partner_id")), "error": error} for error in row_errors)
        else:
            name = clean(row.get("partner_name"))
            tax = clean(row.get("tax_number"))
            create_vals.append({"name": name, "company_type": "company", "customer_rank": 1, "supplier_rank": 0, "legacy_partner_id": clean(row.get("legacy_partner_id")), "legacy_partner_source": LEGACY_SOURCE, "legacy_partner_name": name, "legacy_credit_code": tax, "legacy_tax_no": tax, "legacy_source_evidence": "partner_l4_same_tax_company_canonical_20_write_design_v1"})
    existing = snapshot(model, PRE_WRITE_SNAPSHOT_CSV, [identity for identity in ids if identity])
    if existing:
        precheck_errors.append({"error": "target_identity_not_empty_before_write", "matches": [{"id": rec.id, "legacy_partner_id": rec.legacy_partner_id or "", "name": rec.name or ""} for rec in existing]})
    if precheck_errors:
        env.cr.rollback()  # noqa: F821
        raise RuntimeError({"pre_write_check_failed": precheck_errors})
    created = []
    try:
        for vals in create_vals:
            unsafe_fields = sorted(set(vals) - set(SAFE_FIELDS))
            if unsafe_fields:
                raise RuntimeError({"unsafe_fields": unsafe_fields})
            rec = model.create(vals)
            created.append({"id": rec.id, "legacy_partner_id": rec.legacy_partner_id or "", "name": rec.name or ""})
        env.cr.commit()  # noqa: F821
    except Exception:
        env.cr.rollback()  # noqa: F821
        raise
    post_records = snapshot(model, POST_WRITE_SNAPSHOT_CSV, ids)
    grouped = {}
    for rec in post_records:
        grouped.setdefault(rec.legacy_partner_id or "", []).append(rec)
    duplicate_matches = [{"legacy_partner_id": identity, "ids": [rec.id for rec in records]} for identity, records in sorted(grouped.items()) if len(records) > 1]
    missing_ids = [identity for identity in ids if identity not in grouped]
    rollback_rows = [{"run_id": RUN_ID, "partner_id": rec.id, "legacy_partner_source": rec.legacy_partner_source or "", "legacy_partner_id": rec.legacy_partner_id or "", "partner_name": rec.name or "", "write_action_result": "created"} for rec in post_records]
    write_csv(ROLLBACK_TARGET_CSV, ["run_id", "partner_id", "legacy_partner_source", "legacy_partner_id", "partner_name", "write_action_result"], rollback_rows)
    post_errors = []
    if len(created) != EXPECTED_COUNT:
        post_errors.append({"error": "created_count_not_expected", "created": len(created), "expected": EXPECTED_COUNT})
    if len(rollback_rows) != EXPECTED_COUNT:
        post_errors.append({"error": "rollback_target_not_expected", "rows": len(rollback_rows), "expected": EXPECTED_COUNT})
    if missing_ids:
        post_errors.append({"error": "missing_ids_after_write", "ids": missing_ids})
    if duplicate_matches:
        post_errors.append({"error": "duplicate_legacy_identity_matches", "matches": duplicate_matches})
    payload = {"status": "PASS" if not post_errors else "FAIL", "mode": "partner_same_tax_company_canonical_20_create_write", "database": env.cr.dbname, "input": str(DESIGN_CSV), "created": len(created), "updated": 0, "errors": len(post_errors), "rollback_target_rows": len(rollback_rows), "post_write_identity_count": len(post_records), "duplicate_matches": duplicate_matches, "missing_ids": missing_ids, "post_errors": post_errors, "artifacts": {"pre_write_snapshot": str(PRE_WRITE_SNAPSHOT_CSV), "post_write_snapshot": str(POST_WRITE_SNAPSHOT_CSV), "rollback_targets": str(ROLLBACK_TARGET_CSV)}}  # noqa: F821
    write_json(WRITE_RESULT_JSON, payload)
    print("PARTNER_SAME_TAX_COMPANY_CANONICAL_20_WRITE_RESULT=" + json.dumps({"status": payload["status"], "created": payload["created"], "updated": payload["updated"], "errors": payload["errors"], "rollback_target_rows": payload["rollback_target_rows"]}, ensure_ascii=False, sort_keys=True))
    if post_errors:
        raise RuntimeError({"partner_same_tax_company_canonical_20_write_failed": post_errors})


main()
