#!/usr/bin/env python3
"""Backfill legacy-visible payment request fields from C_ZFSQGL raw export."""

from __future__ import annotations

import csv
import json
import os
import re
from decimal import Decimal, InvalidOperation
from pathlib import Path


DEFAULT_SOURCE = Path("tmp/raw/payment/payment.csv")


def clean(value: object) -> str:
    if value is None or value is False:
        return ""
    text = re.sub(r"\s+", " ", str(value).replace("\u3000", " ").strip())
    return "" if text in {"False", "false", "None", "NULL"} else text


def clean_decimal(value: object) -> str:
    text = clean(value)
    if not text:
        return ""
    try:
        number = Decimal(text)
    except InvalidOperation:
        return text
    return format(number.normalize(), "f")


def source_csv() -> Path:
    candidates = [
        os.getenv("PAYMENT_REQUEST_RAW_CSV"),
        str(DEFAULT_SOURCE),
        "/mnt/extra-addons/tmp/raw/payment/payment.csv",
        "/tmp/payment_request_raw_payment.csv",
    ]
    for candidate in candidates:
        if candidate and Path(candidate).exists():
            return Path(candidate)
    raise RuntimeError({"payment_request_raw_csv_missing": [item for item in candidates if item]})


def ensure_allowed_db() -> None:
    allowlist = {
        item.strip()
        for item in os.getenv("MIGRATION_REPLAY_DB_ALLOWLIST", "sc_demo").split(",")
        if item.strip()
    }
    if env.cr.dbname not in allowlist:  # noqa: F821
        raise RuntimeError({"db_name_not_allowed_for_replay": env.cr.dbname, "allowlist": sorted(allowlist)})  # noqa: F821


ensure_allowed_db()

Request = env["payment.request"].sudo().with_context(active_test=False)  # noqa: F821
path = source_csv()

rows_by_id: dict[str, dict[str, str]] = {}
with path.open("r", encoding="utf-8-sig", newline="") as handle:
    for row in csv.DictReader(handle):
        legacy_id = clean(row.get("Id"))
        if legacy_id:
            rows_by_id[legacy_id] = dict(row)

records = Request.search([("legacy_source_table", "=", "C_ZFSQGL"), ("legacy_record_id", "in", list(rows_by_id))])
updated = 0
unchanged = 0
filled_counts = {
    "legacy_visible_cost_category_name": 0,
    "legacy_visible_remark": 0,
    "legacy_visible_amount_uppercase": 0,
    "legacy_visible_actual_paid_amount": 0,
    "legacy_visible_available_balance": 0,
    "legacy_payment_account_name": 0,
    "legacy_payment_account_no": 0,
    "legacy_payee_account_name": 0,
    "legacy_payee_bank_name": 0,
    "legacy_payee_account_no": 0,
}

for record in records:
    row = rows_by_id.get(clean(record.legacy_record_id), {})
    vals = {
        "legacy_visible_cost_category_name": clean(row.get("f_CBFLMC")),
        "legacy_visible_remark": clean(row.get("f_Remark")),
        "legacy_visible_amount_uppercase": clean(row.get("JEDX")),
        "legacy_visible_actual_paid_amount": clean_decimal(row.get("f_SFJE")) or clean_decimal(row.get("LJFK")),
        "legacy_visible_available_balance": clean_decimal(row.get("SJKYYE")) or clean_decimal(row.get("ZMYE")),
        "legacy_payment_account_name": clean(row.get("FKZHMC")),
        "legacy_payment_account_no": clean(row.get("FKZH")),
        "legacy_payee_account_name": clean(row.get("HM")) or clean(row.get("f_GYSMC")),
        "legacy_payee_bank_name": clean(row.get("f_KHH")),
        "legacy_payee_account_no": clean(row.get("f_ZH")),
    }
    vals = {key: value or False for key, value in vals.items()}
    for key, value in vals.items():
        if value:
            filled_counts[key] += 1
    if any(record[key] != value for key, value in vals.items()):
        record.write(vals)
        updated += 1
    else:
        unchanged += 1

env.cr.commit()  # noqa: F821

payload = {
    "status": "PASS",
    "mode": "payment_request_visible_history_backfill_write",
    "database": env.cr.dbname,  # noqa: F821
    "source_csv": str(path),
    "source_rows": len(rows_by_id),
    "matched_records": len(records),
    "updated_records": updated,
    "unchanged_records": unchanged,
    "filled_counts": filled_counts,
    "decision": "used_raw_migration_c_zfsqgl_not_excel_rows",
}
print("PAYMENT_REQUEST_VISIBLE_HISTORY_BACKFILL=" + json.dumps(payload, ensure_ascii=False, sort_keys=True))
