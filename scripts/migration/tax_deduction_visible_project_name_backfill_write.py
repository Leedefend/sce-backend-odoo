#!/usr/bin/env python3
"""Backfill legacy-visible project name for tax deduction registration."""

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


def read_rows(path: Path) -> dict[str, dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        sample = handle.read(4096)
        handle.seek(0)
        first_line = sample.splitlines()[0] if sample else ""
        dialect = csv.excel()
        dialect.delimiter = "|" if first_line.count("|") > first_line.count(",") else ","
        rows = {}
        for row in csv.DictReader(handle, dialect=dialect):
            key = clean(row.get("legacy_line_id"))
            if key:
                rows[key] = {name: clean(value) for name, value in row.items()}
        return rows


allowlist = {item.strip() for item in os.getenv("MIGRATION_REPLAY_DB_ALLOWLIST", "sc_demo").split(",") if item.strip()}
if env.cr.dbname not in allowlist:  # noqa: F821
    raise RuntimeError({"db_name_not_allowed_for_replay": env.cr.dbname, "allowlist": sorted(allowlist)})  # noqa: F821

path = Path(os.getenv("LEGACY_TAX_DEDUCTION_VISIBLE_CSV") or "/tmp/legacy_tax_deduction_visible.csv")
if not path.exists():
    raise RuntimeError({"legacy_tax_deduction_visible_csv_missing": str(path)})

env.cr.execute("ALTER TABLE sc_tax_deduction_registration ADD COLUMN IF NOT EXISTS legacy_visible_project_name text")  # noqa: F821
rows = read_rows(path)
Tax = env["sc.tax.deduction.registration"].sudo().with_context(active_test=False)  # noqa: F821
updated = 0
for record in Tax.search([("legacy_source_table", "in", ["C_JXXP_DKDJ_New", "C_JXXP_DKDJ_CB"])]):
    row = rows.get(clean(record.legacy_record_id))
    if not row:
        continue
    env.cr.execute(  # noqa: F821
        """
        UPDATE sc_tax_deduction_registration
           SET legacy_visible_project_name = %s,
               write_uid = %s,
               write_date = NOW()
         WHERE id = %s
        """,
        [clean(row.get("project_name")) or None, env.uid, record.id],  # noqa: F821
    )
    updated += 1

env.cr.commit()  # noqa: F821
print(
    "TAX_DEDUCTION_VISIBLE_PROJECT_NAME_BACKFILL="
    + json.dumps({"status": "PASS", "database": env.cr.dbname, "source_rows": len(rows), "updated_records": updated}, ensure_ascii=False, sort_keys=True)  # noqa: F821
)
