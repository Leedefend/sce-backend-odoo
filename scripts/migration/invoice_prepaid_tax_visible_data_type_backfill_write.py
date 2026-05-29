#!/usr/bin/env python3
"""Backfill legacy-visible invoice data type from income invoice CSV."""

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


def add_column() -> None:
    env.cr.execute("ALTER TABLE sc_invoice_registration ADD COLUMN IF NOT EXISTS legacy_visible_data_type text")  # noqa: F821
    env.cr.execute("ALTER TABLE sc_invoice_registration ADD COLUMN IF NOT EXISTS legacy_visible_project_name text")  # noqa: F821


def source_csv() -> Path:
    candidates = [
        os.getenv("LEGACY_INCOME_INVOICE_VISIBLE_CSV"),
        "/tmp/legacy_income_invoice_visible.csv",
        "artifacts/migration/fresh_db_legacy_income_invoice_replay_payload_v1.csv",
    ]
    for candidate in candidates:
        if candidate and Path(candidate).exists():
            return Path(candidate)
    raise RuntimeError({"legacy_income_invoice_visible_csv_missing": [item for item in candidates if item]})


def read_rows(path: Path) -> dict[str, dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        sample = handle.read(4096)
        handle.seek(0)
        first_line = sample.splitlines()[0] if sample else ""
        dialect = csv.excel()
        dialect.delimiter = "|" if first_line.count("|") > first_line.count(",") else ","
        rows = {}
        for row in csv.DictReader(handle, dialect=dialect):
            key = clean(row.get("legacy_record_id"))
            if key:
                rows[key] = {name: clean(value) for name, value in row.items()}
        return rows


allowlist = {item.strip() for item in os.getenv("MIGRATION_REPLAY_DB_ALLOWLIST", "sc_demo").split(",") if item.strip()}
if env.cr.dbname not in allowlist:  # noqa: F821
    raise RuntimeError({"db_name_not_allowed_for_replay": env.cr.dbname, "allowlist": sorted(allowlist)})  # noqa: F821

add_column()
rows = read_rows(source_csv())
Invoice = env["sc.invoice.registration"].sudo().with_context(active_test=False)  # noqa: F821
updated = 0
for record in Invoice.search([("legacy_source_table", "in", ["C_JXXP_YJSKDJ", "C_JXXP_YJSKDJ_CB"])]):
    row = rows.get(clean(record.legacy_record_id))
    if not row:
        continue
    data_type = clean(row.get("source_dataset")) or None
    project_name = clean(row.get("project_name")) or None
    env.cr.execute(  # noqa: F821
        """
        UPDATE sc_invoice_registration
           SET legacy_visible_data_type = %s,
               legacy_visible_project_name = %s,
               write_uid = %s,
               write_date = NOW()
         WHERE id = %s
        """,
        [data_type, project_name, env.uid, record.id],  # noqa: F821
    )
    updated += 1

env.cr.commit()  # noqa: F821
print(
    "INVOICE_PREPAID_TAX_VISIBLE_DATA_TYPE_BACKFILL="
    + json.dumps(
        {
            "status": "PASS",
            "database": env.cr.dbname,  # noqa: F821
            "source_rows": len(rows),
            "updated_records": updated,
        },
        ensure_ascii=False,
        sort_keys=True,
    )
)
