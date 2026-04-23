#!/usr/bin/env python3
"""Write remaining contract headers into sc_migration_fresh."""

from __future__ import annotations

import csv
import json
from collections import Counter
from pathlib import Path


REPO_ROOT = Path("/mnt")
PAYLOAD_CSV = REPO_ROOT / "artifacts/migration/fresh_db_contract_remaining_replay_payload_v1.csv"
OUTPUT_JSON = REPO_ROOT / "artifacts/migration/fresh_db_contract_remaining_write_result_v1.json"
ROLLBACK_CSV = REPO_ROOT / "artifacts/migration/fresh_db_contract_remaining_rollback_targets_v1.csv"
PRE_SNAPSHOT_CSV = REPO_ROOT / "artifacts/migration/fresh_db_contract_remaining_pre_write_snapshot_v1.csv"
POST_SNAPSHOT_CSV = REPO_ROOT / "artifacts/migration/fresh_db_contract_remaining_post_write_snapshot_v1.csv"
EXPECTED_ROWS = 1332
SAFE_FIELDS = {
    "legacy_contract_id",
    "legacy_project_id",
    "project_id",
    "partner_id",
    "subject",
    "type",
    "legacy_contract_no",
    "legacy_document_no",
    "legacy_external_contract_no",
    "legacy_status",
    "legacy_deleted_flag",
    "legacy_counterparty_text",
}
SNAPSHOT_FIELDS = [
    "contract_id",
    "legacy_contract_id",
    "legacy_project_id",
    "project_id",
    "project_name",
    "partner_id",
    "partner_name",
    "name",
    "subject",
    "type",
    "state",
    "legacy_contract_no",
    "legacy_document_no",
    "legacy_external_contract_no",
    "legacy_status",
    "legacy_deleted_flag",
    "legacy_counterparty_text",
    "line_count",
    "is_locked",
]


def clean(value: object) -> str:
    return "" if value is None else str(value).replace("\r\n", "\n").replace("\r", "\n").strip()


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


def snapshot(model, path: Path, ids: list[str]):
    records = model.search([("legacy_contract_id", "in", ids)], order="legacy_contract_id,id")
    rows = []
    for rec in records:
        rows.append(
            {
                "contract_id": rec.id,
                "legacy_contract_id": rec.legacy_contract_id or "",
                "legacy_project_id": rec.legacy_project_id or "",
                "project_id": rec.project_id.id or "",
                "project_name": rec.project_id.display_name or "",
                "partner_id": rec.partner_id.id or "",
                "partner_name": rec.partner_id.display_name or "",
                "name": rec.name or "",
                "subject": rec.subject or "",
                "type": rec.type or "",
                "state": rec.state or "",
                "legacy_contract_no": rec.legacy_contract_no or "",
                "legacy_document_no": rec.legacy_document_no or "",
                "legacy_external_contract_no": rec.legacy_external_contract_no or "",
                "legacy_status": rec.legacy_status or "",
                "legacy_deleted_flag": rec.legacy_deleted_flag or "",
                "legacy_counterparty_text": rec.legacy_counterparty_text or "",
                "line_count": len(rec.line_ids),
                "is_locked": bool(rec.is_locked),
            }
        )
    write_csv(path, SNAPSHOT_FIELDS, rows)
    return records


def build_vals(row: dict[str, str]) -> dict[str, object]:
    vals = {
        "legacy_contract_id": clean(row.get("legacy_contract_id")),
        "legacy_project_id": clean(row.get("legacy_project_id")),
        "project_id": int(clean(row.get("project_id"))),
        "partner_id": int(clean(row.get("partner_id"))),
        "subject": clean(row.get("subject")),
        "type": clean(row.get("type")),
        "legacy_contract_no": clean(row.get("legacy_contract_no")),
        "legacy_document_no": clean(row.get("legacy_document_no")),
        "legacy_external_contract_no": clean(row.get("legacy_external_contract_no")),
        "legacy_status": clean(row.get("legacy_status")),
        "legacy_deleted_flag": clean(row.get("legacy_deleted_flag")),
        "legacy_counterparty_text": clean(row.get("legacy_counterparty_text")),
    }
    return {field: value for field, value in vals.items() if value not in ("", None)}


if env.cr.dbname != "sc_migration_fresh":  # noqa: F821
    raise RuntimeError({"db_name_not_sc_migration_fresh": env.cr.dbname})  # noqa: F821

Contract = env["construction.contract"].sudo()  # noqa: F821
Project = env["project.project"].sudo()  # noqa: F821
Partner = env["res.partner"].sudo()  # noqa: F821

rows = read_csv(PAYLOAD_CSV)
ids = [clean(row.get("legacy_contract_id")) for row in rows]
duplicate_input_ids = sorted(identity for identity, count in Counter(ids).items() if identity and count > 1)
pre_records = snapshot(Contract, PRE_SNAPSHOT_CSV, ids)

errors: list[dict[str, object]] = []
if len(rows) != EXPECTED_ROWS:
    errors.append({"error": "unexpected_payload_rows", "actual": len(rows), "expected": EXPECTED_ROWS})
if duplicate_input_ids:
    errors.append({"error": "duplicate_input_legacy_contract_id", "ids": duplicate_input_ids[:20]})
if pre_records:
    errors.append(
        {
            "error": "pre_existing_contracts",
            "count": len(pre_records),
            "samples": [
                {"contract_id": rec.id, "legacy_contract_id": rec.legacy_contract_id or "", "name": rec.name or ""}
                for rec in pre_records[:20]
            ],
        }
    )

create_vals = []
for index, row in enumerate(rows, start=2):
    vals = build_vals(row)
    unsafe_fields = sorted(set(vals) - SAFE_FIELDS)
    if unsafe_fields:
        errors.append({"line": index, "legacy_contract_id": vals.get("legacy_contract_id"), "error": "unsafe_fields", "fields": unsafe_fields})
    if vals.get("type") not in {"out", "in"}:
        errors.append({"line": index, "legacy_contract_id": vals.get("legacy_contract_id"), "error": "invalid_contract_type", "type": vals.get("type")})
    if not vals.get("subject"):
        errors.append({"line": index, "legacy_contract_id": vals.get("legacy_contract_id"), "error": "missing_subject"})
    if not Project.browse(vals["project_id"]).exists():
        errors.append({"line": index, "legacy_contract_id": vals.get("legacy_contract_id"), "error": "project_missing", "project_id": vals["project_id"]})
    if not Partner.browse(vals["partner_id"]).exists():
        errors.append({"line": index, "legacy_contract_id": vals.get("legacy_contract_id"), "error": "partner_missing", "partner_id": vals["partner_id"]})
    create_vals.append(vals)

if errors:
    env.cr.rollback()  # noqa: F821
    raise RuntimeError({"precheck_failed": errors[:60]})

created = []
try:
    for vals in create_vals:
        rec = Contract.create(vals)
        created.append(
            {
                "contract_id": rec.id,
                "legacy_contract_id": rec.legacy_contract_id or "",
                "legacy_project_id": rec.legacy_project_id or "",
                "project_id": rec.project_id.id or "",
                "partner_id": rec.partner_id.id or "",
                "name": rec.name or "",
                "subject": rec.subject or "",
                "type": rec.type or "",
                "state": rec.state or "",
            }
        )
    env.cr.commit()  # noqa: F821
except Exception:
    env.cr.rollback()  # noqa: F821
    raise

post_records = snapshot(Contract, POST_SNAPSHOT_CSV, ids)
grouped: dict[str, list[object]] = {}
for rec in post_records:
    grouped.setdefault(rec.legacy_contract_id or "", []).append(rec)

rollback_rows = []
for rec in post_records:
    rollback_rows.append(
        {
            "contract_id": rec.id,
            "legacy_contract_id": rec.legacy_contract_id or "",
            "legacy_project_id": rec.legacy_project_id or "",
            "project_id": rec.project_id.id or "",
            "project_name": rec.project_id.display_name or "",
            "partner_id": rec.partner_id.id or "",
            "partner_name": rec.partner_id.display_name or "",
            "name": rec.name or "",
            "subject": rec.subject or "",
            "type": rec.type or "",
            "state": rec.state or "",
            "legacy_contract_no": rec.legacy_contract_no or "",
            "legacy_document_no": rec.legacy_document_no or "",
            "legacy_external_contract_no": rec.legacy_external_contract_no or "",
            "legacy_status": rec.legacy_status or "",
            "legacy_deleted_flag": rec.legacy_deleted_flag or "",
            "legacy_counterparty_text": rec.legacy_counterparty_text or "",
            "line_count": len(rec.line_ids),
            "is_locked": bool(rec.is_locked),
        }
    )
write_csv(ROLLBACK_CSV, SNAPSHOT_FIELDS, rollback_rows)

post_errors = []
if len(created) != EXPECTED_ROWS:
    post_errors.append({"error": "created_count_not_expected", "created": len(created), "expected": EXPECTED_ROWS})
if len(post_records) != EXPECTED_ROWS:
    post_errors.append({"error": "post_write_match_count_not_expected", "matched": len(post_records), "expected": EXPECTED_ROWS})
if any(len(records) > 1 for records in grouped.values()):
    post_errors.append({"error": "duplicate_legacy_identity_matches"})
if any(len(rec.line_ids) for rec in post_records):
    post_errors.append({"error": "unexpected_contract_line_rows"})

status = "PASS" if not post_errors else "FAIL"
result = {
    "status": status,
    "mode": "fresh_db_contract_remaining_write",
    "database": env.cr.dbname,  # noqa: F821
    "target_model": "construction.contract",
    "input_rows": len(rows),
    "created_rows": len(created),
    "post_write_match_count": len(post_records),
    "rollback_target_rows": len(rollback_rows),
    "updated_rows": 0,
    "contract_line_rows": 0,
    "payment_rows": 0,
    "settlement_rows": 0,
    "accounting_rows": 0,
    "demo_targets_executed": 0,
    "post_errors": post_errors,
    "artifacts": {
        "pre_write_snapshot": str(PRE_SNAPSHOT_CSV),
        "post_write_snapshot": str(POST_SNAPSHOT_CSV),
        "rollback_targets": str(ROLLBACK_CSV),
    },
    "decision": "contract_remaining_write_complete" if status == "PASS" else "STOP_REVIEW_REQUIRED",
    "next_step": "refresh fresh database replay manifest with full contract header replay",
}
write_json(OUTPUT_JSON, result)
print(
    "FRESH_DB_CONTRACT_REMAINING_WRITE="
    + json.dumps(
        {
            "status": status,
            "input_rows": len(rows),
            "created_rows": len(created),
            "post_write_match_count": len(post_records),
            "db_writes": len(created),
        },
        ensure_ascii=False,
        sort_keys=True,
    )
)
if status != "PASS":
    raise RuntimeError({"contract_remaining_write_failed": post_errors})
