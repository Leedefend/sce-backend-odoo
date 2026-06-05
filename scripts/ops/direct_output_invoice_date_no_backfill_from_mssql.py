#!/usr/bin/env python3
"""Backfill direct-project output invoice date and number from legacy invoice detail rows.

This script is intended for Odoo shell after a JSON mapping has been generated
from legacy MSSQL ``C_JXXP_XXKPDJ`` + ``C_JXXP_XXKPDJ_CB`` using ``DJBH``.
The mapping format is:

{
  "XXKPDJ-20260316-001": {"开票日期": "2026-02-13", "发票号码": "265..."}
}
"""

from __future__ import annotations

import json
import os
import re
from pathlib import Path


SOURCE_MODEL = "online_old_scbsly:direct_acceptance:general_contract_input_tax_report:action933"
DEFAULT_MAPPING = "/tmp/direct_output_invoice_date_no_backfill_from_mssql.json"
MAPPING_PATH = Path(os.getenv("DIRECT_OUTPUT_INVOICE_DATE_NO_MAPPING", DEFAULT_MAPPING))


def first_iso_date(value):
    match = re.search(r"\d{4}-\d{2}-\d{2}", value or "")
    return match.group(0) if match else None


def ensure_allowed_db() -> None:
    allowlist = {
        item.strip()
        for item in os.getenv("MIGRATION_REPLAY_DB_ALLOWLIST", "sc_demo").split(",")  # noqa: F821
        if item.strip()
    }
    if env.cr.dbname not in allowlist:  # noqa: F821
        raise RuntimeError({"db_name_not_allowed_for_direct_invoice_date_no_backfill": env.cr.dbname, "allowlist": sorted(allowlist)})  # noqa: F821


ensure_allowed_db()
if not MAPPING_PATH.exists():
    raise RuntimeError({"missing_mapping_path": str(MAPPING_PATH)})

updates = json.loads(MAPPING_PATH.read_text(encoding="utf-8"))
Invoice = env["sc.invoice.registration"].sudo().with_context(active_test=False)  # noqa: F821
updated = 0
for document_no, values in updates.items():
    records = Invoice.search([("legacy_source_model", "=", SOURCE_MODEL), ("document_no", "=", document_no)])
    for record in records:
        visible_invoice_date = values.get("开票日期") or ""
        invoice_date = first_iso_date(visible_invoice_date)
        invoice_no = values.get("发票号码") or ""
        env.cr.execute(  # noqa: F821
            """
            UPDATE sc_invoice_registration
               SET invoice_date = COALESCE(%s::date, invoice_date),
                   invoice_no = COALESCE(NULLIF(%s, ''), invoice_no),
                   legacy_visible_invoice_no = COALESCE(NULLIF(%s, ''), legacy_visible_invoice_no),
                   write_date = now()
             WHERE id = %s
            """,
            [invoice_date, invoice_no, invoice_no, record.id],
        )
        env.cr.execute(  # noqa: F821
            """
            UPDATE sc_p1_legacy_visible_alias_payload
               SET payload = jsonb_set(
                       jsonb_set(payload, '{开票日期}', to_jsonb(%s::text), true),
                       '{发票号码}', to_jsonb(%s::text), true
                   ),
                   write_date = now()
             WHERE model = 'sc.invoice.registration' AND res_id = %s
            """,
            [visible_invoice_date, invoice_no, record.id],
        )
        updated += 1

env.cr.commit()  # noqa: F821
records = Invoice.search([("legacy_source_model", "=", SOURCE_MODEL)])
visible_date = sum(1 for record in records if record.p1_visible_d42c2d26610f)
visible_no = sum(1 for record in records if record.p1_visible_ed582efc6e34)
payload = {
    "status": "PASS",
    "database": env.cr.dbname,  # noqa: F821
    "source_model": SOURCE_MODEL,
    "mapping_count": len(updates),
    "updated": updated,
    "total": len(records),
    "visible_date": visible_date,
    "visible_no": visible_no,
}
print("DIRECT_OUTPUT_INVOICE_DATE_NO_BACKFILL=" + json.dumps(payload, ensure_ascii=False, sort_keys=True))
