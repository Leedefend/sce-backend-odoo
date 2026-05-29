#!/usr/bin/env python3
"""Backfill strict user-visible finance fields from legacy source CSVs."""

from __future__ import annotations

import csv
import json
import os
import re
from pathlib import Path


def clean(value: object) -> str:
    if value in (None, False):
        return ""
    text = re.sub(r"\s+", " ", str(value).replace("\u3000", " ").strip())
    return "" if text in {"False", "false", "None", "NULL"} else text


def path_for(env_name: str, default: str) -> Path:
    path = Path(os.getenv(env_name) or default)
    if not path.exists():
        raise RuntimeError({env_name.lower() + "_missing": str(path)})
    return path


def read_rows(path: Path, key: str = "Id") -> dict[str, dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        sample = handle.read(4096)
        handle.seek(0)
        try:
            dialect = csv.Sniffer().sniff(sample, delimiters=",|\t") if sample else csv.excel
        except csv.Error:
            dialect = csv.excel()
            dialect.delimiter = "|"
        result = {}
        for row in csv.DictReader(handle, dialect=dialect):
            row_key = clean(row.get(key))
            if row_key:
                result[row_key] = {name: clean(value) for name, value in row.items()}
        return result


def ensure_allowed_db() -> None:
    allowlist = {item.strip() for item in os.getenv("MIGRATION_REPLAY_DB_ALLOWLIST", "sc_demo").split(",") if item.strip()}
    if env.cr.dbname not in allowlist:  # noqa: F821
        raise RuntimeError({"db_name_not_allowed_for_replay": env.cr.dbname, "allowlist": sorted(allowlist)})  # noqa: F821


def add_column(table: str, column: str, column_type: str = "text") -> None:
    env.cr.execute(f"ALTER TABLE {table} ADD COLUMN IF NOT EXISTS {column} {column_type}")  # noqa: F821


ensure_allowed_db()

for column in (
    "legacy_visible_push_result",
    "legacy_visible_payment_time",
    "legacy_visible_expense_type",
    "legacy_visible_note",
    "legacy_visible_title",
    "legacy_visible_adjustment_item",
    "legacy_visible_returned_flag",
):
    add_column("sc_expense_claim", column)
for column in (
    "legacy_visible_document_no",
    "legacy_visible_project_name",
    "legacy_visible_supplier_name",
    "legacy_visible_payment_date",
    "legacy_visible_note",
    "legacy_visible_other_note",
    "legacy_visible_payment_method",
    "legacy_visible_receipt_bank_name",
    "legacy_visible_receipt_account_no",
    "legacy_visible_payment_account_no",
    "legacy_visible_payment_account_name",
    "legacy_visible_request_no",
):
    add_column("sc_payment_execution", column)

expense_rows = read_rows(path_for("C_CWSFK_GSCWZC_VISIBLE_CSV", "/tmp/c_cwsfk_gscwzc_visible.csv"))
supplier_rows = read_rows(path_for("T_FK_SUPPLIER_VISIBLE_CSV", "/tmp/t_fk_supplier_visible.csv"))
deduction_rows = read_rows(
    path_for(
        "DEDUCTION_ADJUSTMENT_LINE_CSV",
        "/mnt/artifacts/migration/fresh_db_legacy_deduction_adjustment_line_replay_payload_v1.csv",
    ),
    key="legacy_line_id",
)
account_transaction_rows = read_rows(
    path_for(
        "ACCOUNT_TRANSACTION_CSV",
        "/mnt/artifacts/migration/fresh_db_legacy_account_transaction_replay_payload_v1.csv",
    ),
    key="legacy_record_id",
)

Claim = env["sc.expense.claim"].sudo().with_context(active_test=False)  # noqa: F821
Execution = env["sc.payment.execution"].sudo().with_context(active_test=False)  # noqa: F821

expense_updated = 0
for claim in Claim.search([("legacy_source_table", "=", "C_CWSFK_GSCWZC"), ("legacy_record_id", "in", list(expense_rows))]):
    row = expense_rows.get(clean(claim.legacy_record_id), {})
    env.cr.execute(  # noqa: F821
        """
        UPDATE sc_expense_claim
           SET legacy_visible_push_result = %s,
               legacy_visible_payment_time = %s,
               legacy_visible_expense_type = %s,
               legacy_visible_note = %s,
               write_uid = %s,
               write_date = NOW()
         WHERE id = %s
        """,
        [
            clean(row.get("D_SCBSJS_IsPush")) or None,
            clean(row.get("FKSJ"))[:10] or None,
            clean(row.get("D_SCBSJS_CWZCLB")) or clean(row.get("CBLBMC")) or None,
            clean(row.get("BZ")) or None,
            env.uid,  # noqa: F821
            claim.id,
        ],
    )
    expense_updated += 1

deduction_updated = 0
for claim in Claim.search([("claim_type", "=", "expense"), ("expense_type", "=", "扣款实缴登记")]):
    legacy_id = clean(claim.legacy_record_id).split(":", 1)[0]
    row = deduction_rows.get(legacy_id)
    if not row:
        continue
    env.cr.execute(  # noqa: F821
        """
        UPDATE sc_expense_claim
           SET legacy_visible_title = %s,
               legacy_visible_adjustment_item = %s,
               legacy_visible_returned_flag = %s,
               write_uid = %s,
               write_date = NOW()
         WHERE id = %s
        """,
        [
            clean(row.get("title")) or None,
            clean(row.get("adjustment_item_name")) or None,
            clean(row.get("returned_flag")) or None,
            env.uid,  # noqa: F821
            claim.id,
        ],
    )
    deduction_updated += 1

deduction_refund_updated = 0
for claim in Claim.search([("claim_type", "=", "deduction_refund"), ("expense_type", "=", "扣款实缴退回")]):
    legacy_id = clean(claim.legacy_record_id).split(":", 1)[0]
    row = account_transaction_rows.get(legacy_id)
    if not row:
        continue
    env.cr.execute(  # noqa: F821
        """
        UPDATE sc_expense_claim
           SET legacy_visible_adjustment_item = %s,
               legacy_visible_returned_flag = %s,
               write_uid = %s,
               write_date = NOW()
         WHERE id = %s
        """,
        [
            clean(row.get("category") or row.get("counterparty_account_name")) or None,
            "是",
            env.uid,  # noqa: F821
            claim.id,
        ],
    )
    deduction_refund_updated += 1

execution_updated = 0
for execution in Execution.search([("legacy_source_table", "=", "T_FK_Supplier_CB")]):
    note = clean(execution.note)
    match = re.search(r"legacy_parent_id=([^;\n]+)", note)
    parent_id = clean(match.group(1)) if match else ""
    row = supplier_rows.get(parent_id)
    if not row:
        continue
    env.cr.execute(  # noqa: F821
        """
        UPDATE sc_payment_execution
           SET legacy_visible_document_no = %s,
               legacy_visible_project_name = %s,
               legacy_visible_supplier_name = %s,
               legacy_visible_payment_date = %s,
               legacy_visible_note = %s,
               legacy_visible_other_note = %s,
               legacy_visible_payment_method = %s,
               legacy_visible_receipt_bank_name = %s,
               legacy_visible_receipt_account_no = %s,
               legacy_visible_payment_account_no = %s,
               legacy_visible_payment_account_name = %s,
               legacy_visible_request_no = %s,
               write_uid = %s,
               write_date = NOW()
         WHERE id = %s
        """,
        [
            clean(row.get("DJBH")) or None,
            clean(row.get("XMMC")) or None,
            clean(row.get("f_SupplierName")) or None,
            clean(row.get("f_FKRQ"))[:10] or None,
            clean(row.get("f_BZ")) or None,
            clean(row.get("BZ")) or None,
            clean(row.get("f_FKFSMC")) or None,
            clean(row.get("KHH")) or None,
            clean(row.get("ZH")) or None,
            clean(row.get("FKZH")) or None,
            clean(row.get("FKZHMC")) or None,
            clean(row.get("ZFSQDH")) or None,
            env.uid,  # noqa: F821
            execution.id,
        ],
    )
    execution_updated += 1

env.cr.commit()  # noqa: F821

payload = {
    "status": "PASS",
    "mode": "scbs_visible_finance_strict_fields_backfill_write",
    "database": env.cr.dbname,  # noqa: F821
    "expense_source_rows": len(expense_rows),
    "expense_updated": expense_updated,
    "deduction_updated": deduction_updated,
    "deduction_refund_updated": deduction_refund_updated,
    "supplier_source_rows": len(supplier_rows),
    "execution_updated": execution_updated,
}
print("SCBS_VISIBLE_FINANCE_STRICT_FIELDS_BACKFILL=" + json.dumps(payload, ensure_ascii=False, sort_keys=True))
