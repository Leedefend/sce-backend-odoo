# -*- coding: utf-8 -*-
"""Backfill formal tax deduction handling fields from accepted legacy aliases.

Run inside Odoo shell:
    odoo shell -d sc_demo < scripts/migration/tax_deduction_formal_fields_backfill.py
"""

from __future__ import annotations

import json
import re
from decimal import Decimal, InvalidOperation
from pathlib import Path


OUTPUT_DIR = Path("/tmp/tax_deduction_formal_fields_backfill")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def _clean_text(value):
    text = str(value or "").strip()
    return text or False


def _amount(value):
    text = str(value or "").strip()
    if not text:
        return None
    match = re.search(r"-?\d+(?:,\d{3})*(?:\.\d+)?|-?\d+(?:\.\d+)?", text)
    if not match:
        return None
    try:
        return float(Decimal(match.group(0).replace(",", "")))
    except (InvalidOperation, ValueError):
        return None


Model = env["sc.tax.deduction.registration"].sudo()  # noqa: F821
records = Model.search([])

updated = 0
skipped = 0
for rec in records:
    vals = {}
    if not rec.deduction_reason:
        value = _clean_text(getattr(rec, "p1_visible_16e91e3d2738", False))
        if value:
            vals["deduction_reason"] = value
    if not rec.deduction_unit_name:
        value = _clean_text(getattr(rec, "p1_visible_ea75d3bba41c", False))
        if value:
            vals["deduction_unit_name"] = value
    if not rec.withholding_amount:
        value = _amount(getattr(rec, "p1_visible_9b5c1b5cbd69", False))
        if value is not None:
            vals["withholding_amount"] = value
    if not vals:
        skipped += 1
        continue
    rec.write(vals)
    updated += 1

env.cr.commit()  # noqa: F821

summary = {
    "migration": "tax_deduction_formal_fields_backfill",
    "records": len(records),
    "updated": updated,
    "skipped": skipped,
}

(OUTPUT_DIR / "summary.json").write_text(
    json.dumps(summary, ensure_ascii=False, indent=2) + "\n",
    encoding="utf-8",
)
print(json.dumps(summary, ensure_ascii=False))
