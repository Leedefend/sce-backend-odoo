#!/usr/bin/env python3
"""Backfill formal business-entity fields from historical visible columns.

Run with:
  DB_NAME=sc_demo scripts/ops/odoo_shell_exec.sh < scripts/migration/business_entity_formal_fields_backfill_write.py
"""

from __future__ import annotations

import json
import os
from pathlib import Path


def _artifact_path() -> Path:
    root = Path(os.getenv("MIGRATION_ARTIFACT_ROOT") or "/tmp")
    root.mkdir(parents=True, exist_ok=True)
    return root / "business_entity_formal_fields_backfill_result.json"


def _column_exists(table: str, column: str) -> bool:
    env.cr.execute(  # noqa: F821
        """
        SELECT 1
          FROM information_schema.columns
         WHERE table_name = %s
           AND column_name = %s
         LIMIT 1
        """,
        (table, column),
    )
    return bool(env.cr.fetchone())  # noqa: F821


TABLE = "sc_business_entity"
required_columns = {
    "project_name",
    "document_state_text",
    "push_result",
    "cooperation_type",
    "bank_name",
    "bank_account_no",
    "bank_account_holder",
    "social_credit_code",
    "main_tax_rate",
    "receipt_amount",
    "payment_amount",
    "entry_user_name",
    "entry_time",
    "legacy_xmmc",
    "legacy_visible_document_state",
    "legacy_visible_push_result",
    "legacy_visible_cooperation_type",
    "legacy_visible_bank_name",
    "legacy_visible_account_no",
    "legacy_visible_account_holder",
    "legacy_visible_social_credit_code",
    "legacy_visible_main_tax_rate",
    "legacy_visible_receipt_amount",
    "legacy_visible_payment_amount",
    "legacy_visible_creator_name",
    "legacy_visible_created_time",
}
missing = sorted(column for column in required_columns if not _column_exists(TABLE, column))
if missing:
    result = {"mode": "business_entity_formal_fields_backfill", "status": "skipped", "missing_columns": missing}
else:
    amount_expr = """
        CASE
            WHEN regexp_replace(%s, '[^0-9.-]', '', 'g') ~ '^-?[0-9]+(\\.[0-9]+)?$'
            THEN regexp_replace(%s, '[^0-9.-]', '', 'g')::numeric
            ELSE NULL
        END
    """
    env.cr.execute(  # noqa: F821
        f"""
        UPDATE sc_business_entity
           SET project_name = COALESCE(project_name, legacy_xmmc),
               document_state_text = COALESCE(document_state_text, legacy_visible_document_state),
               push_result = COALESCE(push_result, legacy_visible_push_result),
               cooperation_type = COALESCE(cooperation_type, legacy_visible_cooperation_type),
               bank_name = COALESCE(bank_name, legacy_visible_bank_name),
               bank_account_no = COALESCE(bank_account_no, legacy_visible_account_no),
               bank_account_holder = COALESCE(bank_account_holder, legacy_visible_account_holder),
               social_credit_code = COALESCE(social_credit_code, legacy_visible_social_credit_code),
               main_tax_rate = COALESCE(main_tax_rate, legacy_visible_main_tax_rate),
               receipt_amount = COALESCE(receipt_amount, {amount_expr % ('legacy_visible_receipt_amount', 'legacy_visible_receipt_amount')}),
               payment_amount = COALESCE(payment_amount, {amount_expr % ('legacy_visible_payment_amount', 'legacy_visible_payment_amount')}),
               entry_user_name = COALESCE(entry_user_name, legacy_visible_creator_name),
               entry_time = COALESCE(entry_time, legacy_visible_created_time)
         WHERE active IS TRUE
        """
    )
    updated = env.cr.rowcount  # noqa: F821
    env.cr.commit()  # noqa: F821
    result = {"mode": "business_entity_formal_fields_backfill", "status": "ok", "updated": updated}

output = _artifact_path()
output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print(json.dumps(result, ensure_ascii=False, indent=2))
