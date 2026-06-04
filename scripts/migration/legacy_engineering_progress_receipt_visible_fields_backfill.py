#!/usr/bin/env python3
"""Backfill old-page visible fields for engineering-progress receipt facts.

Run through ``odoo shell`` after exporting a CSV with columns:
legacy_record_id, legacy_company_name, legacy_contract_no, legacy_receiving_account,
legacy_attachment_ref.
"""

from __future__ import annotations

import csv
import json
import os
from pathlib import Path


SOURCE_TABLE = "C_JFHKLR"
SOURCE_FAMILY = "engineering_progress_receipt_visible"
DEFAULT_INPUT_CSV = "/tmp/legacy_engineering_progress_receipt_visible_fields.csv"


def clean(value: object) -> str:
    return "" if value is None else str(value).strip()


def ensure_allowed_db() -> None:
    allowlist = {
        item.strip()
        for item in os.getenv("MIGRATION_REPLAY_DB_ALLOWLIST", "sc_demo").split(",")
        if item.strip()
    }
    if env.cr.dbname not in allowlist:  # noqa: F821
        raise RuntimeError({"db_name_not_allowed_for_backfill": env.cr.dbname, "allowlist": sorted(allowlist)})  # noqa: F821


def read_rows(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return [dict(row) for row in csv.DictReader(handle)]


def main() -> int:
    ensure_allowed_db()
    input_csv = Path(os.getenv("LEGACY_ENGINEERING_PROGRESS_RECEIPT_FIELDS_CSV", DEFAULT_INPUT_CSV))
    operation_strategy = clean(os.getenv("LEGACY_ENGINEERING_PROGRESS_RECEIPT_STRATEGY", "joint"))
    if not input_csv.exists():
        raise RuntimeError({"missing_visible_fields_csv": str(input_csv)})

    rows = read_rows(input_csv)
    values_by_legacy_id = {
        clean(row.get("legacy_record_id")): {
            "legacy_company_name": clean(row.get("legacy_company_name")),
            "legacy_contract_no": clean(row.get("legacy_contract_no")),
            "legacy_receiving_account": clean(row.get("legacy_receiving_account")),
            "legacy_attachment_ref": clean(row.get("legacy_attachment_ref")),
        }
        for row in rows
        if clean(row.get("legacy_record_id"))
    }
    Model = env["sc.legacy.receipt.income.fact"].sudo().with_context(active_test=False)  # noqa: F821
    domain = [
        ("legacy_source_table", "=", SOURCE_TABLE),
        ("source_family", "=", SOURCE_FAMILY),
        ("operation_strategy", "=", operation_strategy),
    ]
    facts = Model.search(domain)
    updated = 0
    unchanged = 0
    missing_source = 0
    for fact in facts:
        values = values_by_legacy_id.get(clean(fact.legacy_record_id))
        if values is None:
            missing_source += 1
            continue
        next_values = {
            field: value or False
            for field, value in values.items()
            if clean(getattr(fact, field, "")) != value
        }
        if next_values:
            fact.write(next_values)
            updated += 1
        else:
            unchanged += 1

    env.cr.commit()  # noqa: F821
    payload = {
        "status": "PASS" if missing_source == 0 else "WARN",
        "database": env.cr.dbname,  # noqa: F821
        "input_csv": str(input_csv),
        "input_rows": len(rows),
        "source_table": SOURCE_TABLE,
        "source_family": SOURCE_FAMILY,
        "operation_strategy": operation_strategy,
        "target_rows": len(facts),
        "updated_rows": updated,
        "unchanged_rows": unchanged,
        "missing_source_rows": missing_source,
    }
    print("LEGACY_ENGINEERING_PROGRESS_RECEIPT_VISIBLE_FIELDS_BACKFILL=" + json.dumps(payload, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
