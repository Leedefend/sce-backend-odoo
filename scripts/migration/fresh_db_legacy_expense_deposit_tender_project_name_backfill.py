#!/usr/bin/env python3
"""Backfill legacy TBXMMC tender project names onto expense/deposit facts."""

from __future__ import annotations

import csv
import json
import os
from pathlib import Path


def ensure_allowed_db() -> None:
    allowlist = {
        item.strip()
        for item in os.getenv("MIGRATION_REPLAY_DB_ALLOWLIST", "sc_migration_fresh,sc_demo").split(",")
        if item.strip()
    }
    if env.cr.dbname not in allowlist:  # noqa: F821
        raise RuntimeError({"db_name_not_allowed_for_replay": env.cr.dbname, "allowlist": sorted(allowlist)})  # noqa: F821


def clean(value: object) -> str:
    text = "" if value is None else str(value).strip()
    return "" if text.upper() == "NULL" else text


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return [dict(row) for row in csv.DictReader(handle)]


def write_json(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


ensure_allowed_db()

csv_path = Path(
    os.getenv(
        "LEGACY_EXPENSE_DEPOSIT_TENDER_PROJECT_NAME_CSV",
        "/mnt/artifacts/migration/legacy_expense_deposit_tender_project_name_backfill_v1.csv",
    )
)
artifact_root = Path(os.getenv("MIGRATION_ARTIFACT_ROOT", "/mnt/artifacts/migration"))
output_json = artifact_root / "fresh_db_legacy_expense_deposit_tender_project_name_backfill_result_v1.json"

if not csv_path.exists():
    raise RuntimeError({"missing_backfill_csv": str(csv_path)})

rows = read_csv(csv_path)
Model = env["sc.legacy.expense.deposit.fact"].sudo().with_context(active_test=False)  # noqa: F821
RawModel = env["sc.legacy.tender.guarantee.report.fact"].sudo().with_context(active_test=False)  # noqa: F821

updated = 0
missing = 0
blank_tender_name = 0
raw_created = 0
raw_updated = 0
for row in rows:
    source_table = clean(row.get("legacy_source_table") or row.get("source_table"))
    legacy_record_id = clean(row.get("legacy_record_id") or row.get("legacy_id"))
    tender_project_name = clean(row.get("legacy_tender_project_name") or row.get("tender_project_name"))
    if not source_table or not legacy_record_id:
        missing += 1
        continue
    if not tender_project_name:
        blank_tender_name += 1
    rec = Model.search(
        [("legacy_source_table", "=", source_table), ("legacy_record_id", "=", legacy_record_id)],
        limit=1,
    )
    if not rec:
        missing += 1
    elif clean(rec.legacy_tender_project_name) != tender_project_name:
        rec.write({"legacy_tender_project_name": tender_project_name})
        updated += 1
    amount_text = clean(row.get("source_amount"))
    if "source_amount" in row:
        raw_vals = {
            "legacy_source_table": source_table,
            "legacy_record_id": legacy_record_id,
            "legacy_tender_project_name": tender_project_name,
            "source_amount": float(amount_text or 0.0),
            "source_amount_field": clean(row.get("source_amount_field")),
            "import_batch": clean(row.get("import_batch")) or "legacy_tender_guarantee_report_v1",
        }
        raw = RawModel.search(
            [("legacy_source_table", "=", source_table), ("legacy_record_id", "=", legacy_record_id)],
            limit=1,
        )
        if raw:
            raw.write(raw_vals)
            raw_updated += 1
        else:
            RawModel.create(raw_vals)
            raw_created += 1

env.cr.commit()  # noqa: F821
payload = {
    "status": "PASS" if missing == 0 else "PASS_WITH_MISSING_FACTS",
    "mode": "fresh_db_legacy_expense_deposit_tender_project_name_backfill",
    "database": env.cr.dbname,  # noqa: F821
    "input_rows": len(rows),
    "updated_rows": updated,
    "missing_rows": missing,
    "blank_tender_name_rows": blank_tender_name,
    "raw_created_rows": raw_created,
    "raw_updated_rows": raw_updated,
    "db_writes": updated + raw_created + raw_updated,
    "csv_path": str(csv_path),
}
write_json(output_json, payload)
print("FRESH_DB_LEGACY_EXPENSE_DEPOSIT_TENDER_PROJECT_NAME_BACKFILL=" + json.dumps(payload, ensure_ascii=False, sort_keys=True))
