#!/usr/bin/env python3
"""Write core receipt rows as receive requests in sc_migration_fresh."""

from __future__ import annotations

import csv
import json
from pathlib import Path


REPO_ROOT = Path("/mnt")
PAYLOAD_CSV = REPO_ROOT / "artifacts/migration/fresh_db_receipt_write_design_payload_v1.csv"
OUTPUT_JSON = REPO_ROOT / "artifacts/migration/fresh_db_receipt_core_write_result_v1.json"
ROLLBACK_CSV = REPO_ROOT / "artifacts/migration/fresh_db_receipt_core_rollback_targets_v1.csv"
PRE_SNAPSHOT_CSV = REPO_ROOT / "artifacts/migration/fresh_db_receipt_core_pre_write_snapshot_v1.csv"
POST_SNAPSHOT_CSV = REPO_ROOT / "artifacts/migration/fresh_db_receipt_core_post_write_snapshot_v1.csv"
EXPECTED_ROWS = 1683
MIGRATION_MARKER = "[migration:receipt_core]"
SAFE_FIELDS = {"type", "project_id", "contract_id", "partner_id", "amount", "date_request", "note"}
SNAPSHOT_FIELDS = [
    "request_id",
    "name",
    "type",
    "project_id",
    "contract_id",
    "partner_id",
    "amount",
    "date_request",
    "state",
    "legacy_receipt_id",
]


def clean(value: object) -> str:
    return "" if value is None else str(value).strip()


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return [dict(row) for row in csv.DictReader(handle)]


def write_csv(path: Path, fieldnames: list[str], rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def write_json(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def legacy_marker(legacy_receipt_id: str) -> str:
    return f"{MIGRATION_MARKER} legacy_receipt_id={legacy_receipt_id}"


def note_with_marker(row: dict[str, str]) -> str:
    note = clean(row.get("note"))
    marker = legacy_marker(clean(row.get("legacy_receipt_id")))
    return marker if not note else f"{marker}\n{note}"


def extract_legacy_receipt_id(note: object) -> str:
    text = clean(note)
    token = "legacy_receipt_id="
    if token not in text:
        return ""
    return text.split(token, 1)[1].split()[0].strip()


def snapshot(model, path: Path):
    records = model.search([("note", "ilike", MIGRATION_MARKER)], order="id")
    rows = []
    for rec in records:
        rows.append(
            {
                "request_id": rec.id,
                "name": rec.name or "",
                "type": rec.type or "",
                "project_id": rec.project_id.id or "",
                "contract_id": rec.contract_id.id or "",
                "partner_id": rec.partner_id.id or "",
                "amount": rec.amount or 0,
                "date_request": rec.date_request or "",
                "state": rec.state or "",
                "legacy_receipt_id": extract_legacy_receipt_id(rec.note),
            }
        )
    write_csv(path, SNAPSHOT_FIELDS, rows)
    return records


def count_model(model_name: str) -> int:
    if model_name not in env.registry:  # noqa: F821
        return 0
    return env[model_name].sudo().search_count([])  # noqa: F821


if env.cr.dbname != "sc_migration_fresh":  # noqa: F821
    raise RuntimeError({"db_name_not_sc_migration_fresh": env.cr.dbname})  # noqa: F821

Request = env["payment.request"].sudo()  # noqa: F821
Project = env["project.project"].sudo()  # noqa: F821
Contract = env["construction.contract"].sudo()  # noqa: F821
Partner = env["res.partner"].sudo()  # noqa: F821

rows = read_csv(PAYLOAD_CSV)
pre_records = snapshot(Request, PRE_SNAPSHOT_CSV)
ledger_before = count_model("payment.ledger")
settlement_before = count_model("sc.settlement.order")
account_move_before = count_model("account.move")

errors: list[dict[str, object]] = []
if len(rows) != EXPECTED_ROWS:
    errors.append({"error": "unexpected_payload_rows", "actual": len(rows), "expected": EXPECTED_ROWS})
if pre_records:
    errors.append({"error": "pre_existing_receipt_core_requests", "count": len(pre_records), "samples": pre_records[:20].mapped("id")})

create_vals = []
for index, row in enumerate(rows, start=2):
    vals = {
        "type": "receive",
        "project_id": int(clean(row.get("project_id"))),
        "contract_id": int(clean(row.get("contract_id"))),
        "partner_id": int(clean(row.get("partner_id"))),
        "amount": float(clean(row.get("amount"))),
        "date_request": clean(row.get("date_request")),
        "note": note_with_marker(row),
    }
    unsafe_fields = sorted(set(vals) - SAFE_FIELDS)
    if unsafe_fields:
        errors.append({"line": index, "error": "unsafe_fields", "fields": unsafe_fields})
    if vals["type"] != "receive":
        errors.append({"line": index, "error": "non_receive_type"})
    if vals["amount"] <= 0:
        errors.append({"line": index, "error": "non_positive_amount", "amount": vals["amount"]})
    if not Project.browse(vals["project_id"]).exists():
        errors.append({"line": index, "error": "project_missing", "project_id": vals["project_id"]})
    if not Contract.browse(vals["contract_id"]).exists():
        errors.append({"line": index, "error": "contract_missing", "contract_id": vals["contract_id"]})
    if not Partner.browse(vals["partner_id"]).exists():
        errors.append({"line": index, "error": "partner_missing", "partner_id": vals["partner_id"]})
    create_vals.append(vals)

if errors:
    env.cr.rollback()  # noqa: F821
    raise RuntimeError({"precheck_failed": errors[:60]})

created = []
try:
    for vals in create_vals:
        rec = Request.create(vals)
        created.append(
            {
                "request_id": rec.id,
                "name": rec.name or "",
                "type": rec.type or "",
                "project_id": rec.project_id.id or "",
                "contract_id": rec.contract_id.id or "",
                "partner_id": rec.partner_id.id or "",
                "amount": rec.amount or 0,
                "date_request": rec.date_request or "",
                "state": rec.state or "",
                "legacy_receipt_id": extract_legacy_receipt_id(rec.note),
            }
        )
    env.cr.commit()  # noqa: F821
except Exception:
    env.cr.rollback()  # noqa: F821
    raise

post_records = snapshot(Request, POST_SNAPSHOT_CSV)
write_csv(ROLLBACK_CSV, SNAPSHOT_FIELDS, created)
ledger_after = count_model("payment.ledger")
settlement_after = count_model("sc.settlement.order")
account_move_after = count_model("account.move")

post_errors = []
if len(created) != EXPECTED_ROWS:
    post_errors.append({"error": "created_count_not_expected", "created": len(created), "expected": EXPECTED_ROWS})
if len(post_records) != EXPECTED_ROWS:
    post_errors.append({"error": "post_marker_count_not_expected", "count": len(post_records), "expected": EXPECTED_ROWS})
if ledger_after != ledger_before:
    post_errors.append({"error": "ledger_count_changed", "before": ledger_before, "after": ledger_after})
if settlement_after != settlement_before:
    post_errors.append({"error": "settlement_count_changed", "before": settlement_before, "after": settlement_after})
if account_move_after != account_move_before:
    post_errors.append({"error": "account_move_count_changed", "before": account_move_before, "after": account_move_after})

status = "PASS" if not post_errors else "FAIL"
result = {
    "status": status,
    "mode": "fresh_db_receipt_core_write",
    "database": env.cr.dbname,  # noqa: F821
    "target_model": "payment.request",
    "target_type": "receive",
    "input_rows": len(rows),
    "created_rows": len(created),
    "post_write_match_count": len(post_records),
    "rollback_target_rows": len(created),
    "ledger_rows_created": ledger_after - ledger_before,
    "settlement_rows_created": settlement_after - settlement_before,
    "account_move_rows_created": account_move_after - account_move_before,
    "demo_targets_executed": 0,
    "post_errors": post_errors,
    "artifacts": {
        "pre_write_snapshot": str(PRE_SNAPSHOT_CSV),
        "post_write_snapshot": str(POST_SNAPSHOT_CSV),
        "rollback_targets": str(ROLLBACK_CSV),
    },
    "decision": "receipt_core_write_complete" if status == "PASS" else "STOP_REVIEW_REQUIRED",
    "next_step": "refresh fresh database replay manifest with receipt core write",
}
write_json(OUTPUT_JSON, result)
print(
    "FRESH_DB_RECEIPT_CORE_WRITE="
    + json.dumps(
        {
            "status": status,
            "input_rows": len(rows),
            "created_rows": len(created),
            "post_write_match_count": len(post_records),
            "ledger_rows_created": ledger_after - ledger_before,
            "settlement_rows_created": settlement_after - settlement_before,
            "account_move_rows_created": account_move_after - account_move_before,
        },
        ensure_ascii=False,
        sort_keys=True,
    )
)
if status != "PASS":
    raise RuntimeError({"receipt_core_write_failed": post_errors})
