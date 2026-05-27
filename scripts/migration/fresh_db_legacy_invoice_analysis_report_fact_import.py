#!/usr/bin/env python3
"""Import raw facts required by the legacy invoice analysis report."""

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
        "LEGACY_INVOICE_ANALYSIS_REPORT_FACT_CSV",
        "/mnt/artifacts/migration/legacy_invoice_analysis_report_fact_v1.csv",
    )
)
artifact_root = Path(os.getenv("MIGRATION_ARTIFACT_ROOT", "/mnt/artifacts/migration"))
output_json = artifact_root / "fresh_db_legacy_invoice_analysis_report_fact_import_result_v1.json"

if not csv_path.exists():
    raise RuntimeError({"missing_invoice_analysis_csv": str(csv_path)})

rows = read_csv(csv_path)
Model = env["sc.legacy.invoice.analysis.report.fact"].sudo().with_context(active_test=False)  # noqa: F821
Project = env["project.project"].sudo().with_context(active_test=False)  # noqa: F821

project_ids = sorted({clean(row.get("legacy_project_id")) for row in rows if clean(row.get("legacy_project_id"))})
project_map = {
    rec["legacy_project_id"]: rec["id"]
    for rec in Project.search_read([("legacy_project_id", "in", project_ids)], ["legacy_project_id"])
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
        continue
    vals = {
        "legacy_source_table": clean(row.get("legacy_source_table")),
        "legacy_record_id": clean(row.get("legacy_record_id")),
        "fact_type": clean(row.get("fact_type")),
        "legacy_project_id": legacy_project_id,
        "legacy_project_name": clean(row.get("legacy_project_name")),
        "project_id": project_id,
        "invoice_company_type": clean(row.get("invoice_company_type")),
        "source_amount": float(clean(row.get("source_amount")) or 0.0),
        "source_amount_field": clean(row.get("source_amount_field")),
        "import_batch": clean(row.get("import_batch")) or "legacy_invoice_analysis_report_v1",
    }
    rec = Model.search(
        [
            ("legacy_source_table", "=", vals["legacy_source_table"]),
            ("legacy_record_id", "=", vals["legacy_record_id"]),
            ("fact_type", "=", vals["fact_type"]),
        ],
        limit=1,
    )
    if rec:
        rec.write(vals)
        updated += 1
    else:
        Model.create(vals)
        created += 1

env.cr.commit()  # noqa: F821
payload = {
    "status": "PASS" if missing_project == 0 else "PASS_WITH_MISSING_PROJECTS",
    "mode": "fresh_db_legacy_invoice_analysis_report_fact_import",
    "database": env.cr.dbname,  # noqa: F821
    "input_rows": len(rows),
    "created_rows": created,
    "updated_rows": updated,
    "missing_project_rows": missing_project,
    "db_writes": created + updated,
    "csv_path": str(csv_path),
}
write_json(output_json, payload)
print("FRESH_DB_LEGACY_INVOICE_ANALYSIS_REPORT_FACT_IMPORT=" + json.dumps(payload, ensure_ascii=False, sort_keys=True))
