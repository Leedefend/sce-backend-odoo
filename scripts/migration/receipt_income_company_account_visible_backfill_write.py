#!/usr/bin/env python3
"""Backfill company income visible account/audit fields from C_CWSFK_GSCWSR."""

from __future__ import annotations

import csv
import json
import os
import re
from pathlib import Path


DEFAULT_SOURCE = Path("/tmp/c_cwsfk_gscwsr_visible.csv")


def clean(value: object) -> str:
    if value in (None, False):
        return ""
    text = re.sub(r"\s+", " ", str(value).replace("\u3000", " ").strip())
    return "" if text in {"False", "false", "None", "NULL"} else text


def source_csv() -> Path:
    path = Path(os.getenv("C_CWSFK_GSCWSR_VISIBLE_CSV") or DEFAULT_SOURCE)
    if not path.exists():
        raise RuntimeError({"c_cwsfk_gscwsr_visible_csv_missing": str(path)})
    return path


def read_rows(path: Path) -> dict[str, dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        sample = handle.read(4096)
        handle.seek(0)
        try:
            dialect = csv.Sniffer().sniff(sample, delimiters=",|\t") if sample else csv.excel
        except csv.Error:
            dialect = csv.excel()
            dialect.delimiter = "|"
        rows = {}
        for row in csv.DictReader(handle, dialect=dialect):
            legacy_id = clean(row.get("Id"))
            if legacy_id:
                rows[legacy_id] = {key: clean(value) for key, value in row.items()}
        return rows


def ensure_allowed_db() -> None:
    allowlist = {
        item.strip()
        for item in os.getenv("MIGRATION_REPLAY_DB_ALLOWLIST", "sc_demo").split(",")
        if item.strip()
    }
    if env.cr.dbname not in allowlist:  # noqa: F821
        raise RuntimeError({"db_name_not_allowed_for_replay": env.cr.dbname, "allowlist": sorted(allowlist)})  # noqa: F821


ensure_allowed_db()

rows = read_rows(source_csv())
Receipt = env["sc.receipt.income"].sudo().with_context(active_test=False)  # noqa: F821
records = Receipt.search([("legacy_source_table", "=", "C_CWSFK_GSCWSR"), ("legacy_record_id", "in", list(rows))])

updated = 0
samples = []
for record in records:
    row = rows.get(clean(record.legacy_record_id), {})
    vals = {
        "receiving_account": clean(row.get("SKZH")) or False,
        "receiving_account_name": clean(row.get("SKZH")) or False,
        "receiving_account_no": clean(row.get("SKZHID")) or False,
        "legacy_receipt_subtype": clean(row.get("D_SCBSJS_CWSRLB")) or clean(row.get("SKLB")) or False,
        "income_category": clean(row.get("D_SCBSJS_CWSRLB")) or clean(row.get("SKLB")) or False,
        "creator_legacy_user_id": clean(row.get("LRRID")) or False,
        "creator_name": clean(row.get("LRR")) or clean(row.get("TXR")) or False,
        "created_time": clean(row.get("LRSJ")) or False,
    }
    if not any(record[key] != value for key, value in vals.items() if key in record._fields):
        continue
    env.cr.execute(  # noqa: F821
        """
        UPDATE sc_receipt_income
           SET receiving_account = %s,
               receiving_account_name = %s,
               receiving_account_no = %s,
               legacy_receipt_subtype = %s,
               income_category = %s,
               creator_legacy_user_id = %s,
               creator_name = %s,
               created_time = %s,
               write_uid = %s,
               write_date = NOW()
         WHERE id = %s
        """,
        [
            vals["receiving_account"],
            vals["receiving_account_name"],
            vals["receiving_account_no"],
            vals["legacy_receipt_subtype"],
            vals["income_category"],
            vals["creator_legacy_user_id"],
            vals["creator_name"],
            vals["created_time"],
            env.uid,  # noqa: F821
            record.id,
        ],
    )
    updated += 1
    if len(samples) < 20:
        samples.append(
            {
                "id": record.id,
                "document_no": record.document_no or record.name,
                "receiving_account": vals["receiving_account"],
                "creator_name": vals["creator_name"],
                "created_time": vals["created_time"],
            }
        )

env.cr.commit()  # noqa: F821

payload = {
    "status": "PASS",
    "mode": "receipt_income_company_account_visible_backfill_write",
    "database": env.cr.dbname,  # noqa: F821
    "source_rows": len(rows),
    "matched_records": len(records),
    "updated_records": updated,
    "samples": samples,
    "decision": "filled_company_income_visible_account_and_audit_fields_from_c_cwsfk_gscwsr",
}
print("RECEIPT_INCOME_COMPANY_VISIBLE_BACKFILL=" + json.dumps(payload, ensure_ascii=False, sort_keys=True))
