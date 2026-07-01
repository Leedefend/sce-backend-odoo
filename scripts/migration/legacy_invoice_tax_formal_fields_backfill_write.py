#!/usr/bin/env python3
"""Backfill formal invoice tax fields from historical/source carriers."""

from __future__ import annotations

import json
import os
from pathlib import Path


def _artifact_path() -> Path:
    root = Path(os.getenv("MIGRATION_ARTIFACT_ROOT") or "/tmp")
    root.mkdir(parents=True, exist_ok=True)
    return root / "legacy_invoice_tax_formal_fields_backfill_result.json"


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


TABLE = "sc_legacy_invoice_tax_fact"
required_columns = {
    "document_state_text",
    "legacy_state",
    "invoice_partner_name",
    "legacy_partner_name",
    "amount_total",
    "tax_amount",
    "amount_untaxed",
    "source_amount",
    "source_tax_amount",
    "source_amount_untaxed",
}
missing = sorted(column for column in required_columns if not _column_exists(TABLE, column))
if missing:
    result = {"mode": "legacy_invoice_tax_formal_fields_backfill", "status": "skipped", "missing_columns": missing}
else:
    env.cr.execute(  # noqa: F821
        """
        UPDATE sc_legacy_invoice_tax_fact
           SET document_state_text = COALESCE(NULLIF(document_state_text, ''), NULLIF(legacy_state, '')),
               invoice_partner_name = COALESCE(NULLIF(invoice_partner_name, ''), NULLIF(legacy_partner_name, '')),
               amount_total = COALESCE(NULLIF(amount_total, 0.0), source_amount),
               tax_amount = COALESCE(NULLIF(tax_amount, 0.0), source_tax_amount),
               amount_untaxed = COALESCE(NULLIF(amount_untaxed, 0.0), NULLIF(source_amount_untaxed, 0.0), source_amount)
         WHERE COALESCE(document_state_text, '') = ''
            OR COALESCE(invoice_partner_name, '') = ''
            OR COALESCE(amount_total, 0.0) = 0.0
            OR COALESCE(tax_amount, 0.0) = 0.0
            OR COALESCE(amount_untaxed, 0.0) = 0.0
        """
    )
    updated = env.cr.rowcount  # noqa: F821
    env.cr.commit()  # noqa: F821
    result = {"mode": "legacy_invoice_tax_formal_fields_backfill", "status": "ok", "updated": updated}

output = _artifact_path()
output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print(json.dumps(result, ensure_ascii=False, indent=2))
