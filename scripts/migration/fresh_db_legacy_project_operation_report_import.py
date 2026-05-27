#!/usr/bin/env python3
"""Import old SELECT_XMJYTJB rows into sc.legacy.project.operation.report.fact."""

from __future__ import annotations

import csv
import json
import os
from pathlib import Path


AMOUNT_FIELDS = [
    "current_receipt_amount",
    "current_deduction_registered_amount",
    "current_subcontract_amount",
    "personal_income_tax_amount",
    "enterprise_income_tax_amount",
    "interest_amount",
    "management_fee_refundable_amount",
    "management_fee_nonrefundable_amount",
    "other_amount",
    "vat_nonrefundable_amount",
    "vat_three_percent_amount",
    "construction_stamp_tax_amount",
    "prepaid_vat_amount",
    "purchase_sale_stamp_tax_amount",
    "risk_reserve_amount",
    "surcharge_nonrefundable_amount",
    "surcharge_amount",
    "vat_amount",
    "output_tax_amount",
    "input_tax_amount",
    "actual_deduction_vat_amount",
    "deductible_surcharge_amount",
    "actual_deduction_surcharge_amount",
    "net_income_amount",
    "operation_income_amount",
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
    if not text:
        return 0.0
    return float(text)


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return [dict(row) for row in csv.DictReader(handle)]


def write_json(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


ensure_allowed_db()

csv_path = Path(
    os.getenv(
        "LEGACY_PROJECT_OPERATION_REPORT_CSV",
        "/mnt/artifacts/migration/legacy_project_operation_report_v1.csv",
    )
)
artifact_root = Path(os.getenv("MIGRATION_ARTIFACT_ROOT", "/mnt/artifacts/migration"))
output_json = artifact_root / "fresh_db_legacy_project_operation_report_import_result_v1.json"

if not csv_path.exists():
    raise RuntimeError({"missing_project_operation_report_csv": str(csv_path)})

rows = read_csv(csv_path)
Model = env["sc.legacy.project.operation.report.fact"].sudo().with_context(active_test=False)  # noqa: F821
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
        "legacy_pid": clean(row.get("legacy_pid")),
        "legacy_project_name": clean(row.get("legacy_project_name")),
        "project_id": project_id or False,
        "import_batch": clean(row.get("import_batch")) or "legacy_project_operation_report_v1",
        "deduction_rate": number(row.get("deduction_rate")),
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
    "mode": "fresh_db_legacy_project_operation_report_import",
    "database": env.cr.dbname,  # noqa: F821
    "input_rows": len(rows),
    "created_rows": created,
    "updated_rows": updated,
    "missing_project_rows": missing_project,
    "db_writes": created + updated,
    "csv_path": str(csv_path),
}
write_json(output_json, payload)
print("FRESH_DB_LEGACY_PROJECT_OPERATION_REPORT_IMPORT=" + json.dumps(payload, ensure_ascii=False, sort_keys=True))
