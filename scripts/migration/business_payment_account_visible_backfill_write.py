#!/usr/bin/env python3
"""Backfill user-visible payment account fields from legacy payment sources."""

from __future__ import annotations

import csv
import json
import os
import re
from pathlib import Path


EXPENSE_SOURCE = Path("/tmp/c_cwsfk_gscwzc_accounts.csv")
SUPPLIER_SOURCE = Path("/tmp/t_fk_supplier_accounts.csv")


def clean(value: object) -> str:
    if value in (None, False):
        return ""
    text = re.sub(r"\s+", " ", str(value).replace("\u3000", " ").strip())
    return "" if text in {"False", "false", "None", "NULL"} else text


def csv_path(env_name: str, default: Path) -> Path:
    path = Path(os.getenv(env_name) or default)
    if not path.exists():
        raise RuntimeError({env_name.lower() + "_missing": str(path)})
    return path


def read_rows(path: Path, key: str) -> dict[str, dict[str, str]]:
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
            row_key = clean(row.get(key))
            if row_key:
                rows[row_key] = {column: clean(value) for column, value in row.items()}
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

expense_rows = read_rows(csv_path("C_CWSFK_GSCWZC_ACCOUNTS_CSV", EXPENSE_SOURCE), "Id")
supplier_rows = read_rows(csv_path("T_FK_SUPPLIER_ACCOUNTS_CSV", SUPPLIER_SOURCE), "Id")

Claim = env["sc.expense.claim"].sudo().with_context(active_test=False)  # noqa: F821
Execution = env["sc.payment.execution"].sudo().with_context(active_test=False)  # noqa: F821

expense_updated = 0
expense_seen = Claim.search([("legacy_source_table", "=", "C_CWSFK_GSCWZC"), ("legacy_record_id", "in", list(expense_rows))])
for claim in expense_seen:
    row = expense_rows.get(clean(claim.legacy_record_id), {})
    vals = {
        "payment_account_name": clean(row.get("FKZHMC")) or False,
        "payer_account": clean(row.get("FKZH")) or False,
        "payer_bank": clean(row.get("KHYH")) or False,
        "creator_name": clean(row.get("LRR")) or False,
        "created_time": clean(row.get("LRSJ")) or False,
    }
    vals = {key: value for key, value in vals.items() if key in claim._fields and claim[key] != value}
    if vals:
        env.cr.execute(  # noqa: F821
            """
            UPDATE sc_expense_claim
               SET payment_account_name = %s,
                   payer_account = %s,
                   payer_bank = %s,
                   creator_name = %s,
                   created_time = %s,
                   write_uid = %s,
                   write_date = NOW()
             WHERE id = %s
            """,
            [
                vals.get("payment_account_name", claim.payment_account_name or None),
                vals.get("payer_account", claim.payer_account or None),
                vals.get("payer_bank", claim.payer_bank or None),
                vals.get("creator_name", claim.creator_name or None),
                vals.get("created_time", claim.created_time or None),
                env.uid,  # noqa: F821
                claim.id,
            ],
        )
        expense_updated += 1

execution_updated = 0
executions = Execution.search([("legacy_source_table", "=", "T_FK_Supplier_CB")])
for execution in executions:
    parent_id = clean(execution.note).split("legacy_parent_id=", 1)[-1].split(";", 1)[0].strip() if "legacy_parent_id=" in clean(execution.note) else ""
    row = supplier_rows.get(parent_id)
    if not row:
        continue
    vals = {
        "payment_account_name": clean(row.get("FKZHMC")) or False,
        "payment_account_no": clean(row.get("FKZH")) or False,
        "payment_bank_name": clean(row.get("KHH")) or False,
        "receipt_account_no": clean(row.get("ZH")) or False,
        "receipt_bank_name": clean(row.get("KHH")) or False,
        "handler_name": clean(row.get("f_TXR")) or clean(row.get("f_LRR")) or False,
        "creator_name": clean(row.get("f_LRR")) or False,
        "created_time": clean(row.get("f_LRSJ")) or False,
    }
    vals = {key: value for key, value in vals.items() if key in execution._fields and execution[key] != value}
    if vals:
        env.cr.execute(  # noqa: F821
            """
            UPDATE sc_payment_execution
               SET payment_account_name = %s,
                   payment_account_no = %s,
                   payment_bank_name = %s,
                   receipt_account_no = %s,
                   receipt_bank_name = %s,
                   handler_name = %s,
                   creator_name = %s,
                   created_time = %s,
                   write_uid = %s,
                   write_date = NOW()
             WHERE id = %s
            """,
            [
                vals.get("payment_account_name", execution.payment_account_name or None),
                vals.get("payment_account_no", execution.payment_account_no or None),
                vals.get("payment_bank_name", execution.payment_bank_name or None),
                vals.get("receipt_account_no", execution.receipt_account_no or None),
                vals.get("receipt_bank_name", execution.receipt_bank_name or None),
                vals.get("handler_name", execution.handler_name or None),
                vals.get("creator_name", execution.creator_name or None),
                vals.get("created_time", execution.created_time or None),
                env.uid,  # noqa: F821
                execution.id,
            ],
        )
        execution_updated += 1

env.cr.commit()  # noqa: F821

payload = {
    "status": "PASS",
    "mode": "business_payment_account_visible_backfill_write",
    "database": env.cr.dbname,  # noqa: F821
    "expense_source_rows": len(expense_rows),
    "expense_matched": len(expense_seen),
    "expense_updated": expense_updated,
    "supplier_source_rows": len(supplier_rows),
    "execution_scanned": len(executions),
    "execution_updated": execution_updated,
    "decision": "filled_visible_payment_accounts_from_legacy_sources_without_guessing",
}
print("BUSINESS_PAYMENT_ACCOUNT_VISIBLE_BACKFILL=" + json.dumps(payload, ensure_ascii=False, sort_keys=True))
