#!/usr/bin/env python3
"""Import old invoice cost progress report rows."""

from __future__ import annotations

import csv
import json
import os
from pathlib import Path


AMOUNT_FIELDS = [
    "progress_receipt_amount",
    "output_invoice_amount",
    "input_invoice_amount",
    "cost_difference_amount",
]


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


def number(value: object) -> float:
    text = clean(value)
    return float(text) if text else 0.0


ensure_allowed_db()

csv_path = Path(
    os.getenv(
        "LEGACY_INVOICE_COST_PROGRESS_REPORT_CSV",
        "/mnt/artifacts/migration/legacy_invoice_cost_progress_report_v1.csv",
    )
)
artifact_root = Path(os.getenv("MIGRATION_ARTIFACT_ROOT", "/mnt/artifacts/migration"))
output_json = artifact_root / "fresh_db_legacy_invoice_cost_progress_report_import_result_v1.json"

if not csv_path.exists():
    raise RuntimeError({"missing_invoice_cost_progress_report_csv": str(csv_path)})

with csv_path.open("r", encoding="utf-8-sig", newline="") as handle:
    rows = [dict(row) for row in csv.DictReader(handle)]

Model = env["sc.legacy.invoice.cost.progress.report.fact"].sudo().with_context(active_test=False)  # noqa: F821
Project = env["project.project"].sudo().with_context(active_test=False)  # noqa: F821
legacy_ids = sorted({clean(row.get("legacy_project_id")) for row in rows if clean(row.get("legacy_project_id"))})
project_map = {
    rec["legacy_project_id"]: rec["id"]
    for rec in Project.search_read([("legacy_project_id", "in", legacy_ids)], ["legacy_project_id"])
    if rec.get("legacy_project_id")
}

created = 0
updated = 0
missing_project = 0
for row in rows:
    legacy_project_id = clean(row.get("legacy_project_id"))
    project_id = project_map.get(legacy_project_id)
    if not project_id:
        missing_project += 1
    vals = {
        "legacy_project_id": legacy_project_id,
        "legacy_project_name": clean(row.get("legacy_project_name")),
        "project_id": project_id or False,
        "import_batch": clean(row.get("import_batch")) or "legacy_invoice_cost_progress_report_v1",
    }
    vals.update({field: number(row.get(field)) for field in AMOUNT_FIELDS})
    rec = Model.search([("legacy_project_id", "=", legacy_project_id)], limit=1)
    if rec:
        rec.write(vals)
        updated += 1
    else:
        Model.create(vals)
        created += 1

env.cr.commit()  # noqa: F821
payload = {
    "status": "PASS" if missing_project == 0 else "PASS_WITH_MISSING_PROJECTS",
    "mode": "fresh_db_legacy_invoice_cost_progress_report_import",
    "database": env.cr.dbname,  # noqa: F821
    "input_rows": len(rows),
    "created_rows": created,
    "updated_rows": updated,
    "missing_project_rows": missing_project,
    "db_writes": created + updated,
    "csv_path": str(csv_path),
}
output_json.parent.mkdir(parents=True, exist_ok=True)
output_json.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
print("FRESH_DB_LEGACY_INVOICE_COST_PROGRESS_REPORT_IMPORT=" + json.dumps(payload, ensure_ascii=False, sort_keys=True))
