#!/usr/bin/env python3
"""Write core receipt rows as receive requests in sc_migration_fresh."""

from __future__ import annotations

import csv
import json
import os
from pathlib import Path


def repo_root() -> Path:
    env_root = os.getenv("MIGRATION_REPO_ROOT")
    candidates = []
    if env_root:
        candidates.append(Path(env_root))
    candidates.extend([Path("/mnt"), Path.cwd()])
    for candidate in candidates:
        if (candidate / "artifacts/migration/fresh_db_replay_manifest_v1.json").exists():
            return candidate
    return Path.cwd()


def ensure_allowed_db() -> None:
    allowlist = {item.strip() for item in os.getenv("MIGRATION_REPLAY_DB_ALLOWLIST", "sc_migration_fresh").split(",") if item.strip()}
    if env.cr.dbname not in allowlist:  # noqa: F821
        raise RuntimeError({"db_name_not_allowed_for_replay": env.cr.dbname, "allowlist": sorted(allowlist)})  # noqa: F821


REPO_ROOT = repo_root()
ARTIFACT_ROOT = Path(os.getenv("MIGRATION_ARTIFACT_ROOT", str(REPO_ROOT / "artifacts/migration")))
PAYLOAD_CSV = REPO_ROOT / "artifacts/migration/fresh_db_receipt_write_design_payload_v1.csv"
OUTPUT_JSON = ARTIFACT_ROOT / "fresh_db_receipt_core_write_result_v1.json"
ROLLBACK_CSV = ARTIFACT_ROOT / "fresh_db_receipt_core_rollback_targets_v1.csv"
PRE_SNAPSHOT_CSV = ARTIFACT_ROOT / "fresh_db_receipt_core_pre_write_snapshot_v1.csv"
POST_SNAPSHOT_CSV = ARTIFACT_ROOT / "fresh_db_receipt_core_post_write_snapshot_v1.csv"
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


def resolve_project_id(row: dict[str, str], project_model) -> int | None:
    legacy_project_id = clean(row.get("legacy_project_id"))
    if legacy_project_id:
        matches = project_model.search([("legacy_project_id", "=", legacy_project_id)], limit=2)
        if len(matches) == 1:
            return matches.id
        if len(matches) > 1:
            raise RuntimeError({"duplicate_legacy_project_matches": legacy_project_id, "project_ids": matches.ids})
    project_id = clean(row.get("project_id"))
    if project_id:
        rec = project_model.browse(int(project_id)).exists()
        if rec:
            return rec.id
    return None


def resolve_contract_id(row: dict[str, str], contract_model) -> int | None:
    legacy_contract_id = clean(row.get("legacy_contract_id"))
    if legacy_contract_id:
        matches = contract_model.search([("legacy_contract_id", "=", legacy_contract_id)], limit=2)
        if len(matches) == 1:
            return matches.id
        if len(matches) > 1:
            raise RuntimeError({"duplicate_legacy_contract_matches": legacy_contract_id, "contract_ids": matches.ids})
    contract_id = clean(row.get("contract_id"))
    if contract_id:
        rec = contract_model.browse(int(contract_id)).exists()
        if rec:
            return rec.id
    return None


def resolve_partner_id(row: dict[str, str], partner_model) -> int | None:
    legacy_partner_id = clean(row.get("legacy_partner_id"))
    if legacy_partner_id:
        matches = partner_model.search([("legacy_partner_id", "=", legacy_partner_id)], order="id")
        if len(matches) == 1:
            return matches.id
        if len(matches) > 1:
            return matches[0].id
    partner_id = clean(row.get("partner_id"))
    if partner_id:
        rec = partner_model.browse(int(partner_id)).exists()
        if rec:
            return rec.id
    partner_name = clean(row.get("partner_name"))
    if partner_name:
        matches = partner_model.search([("name", "=", partner_name)], order="id")
        if len(matches) == 1:
            return matches.id
        if len(matches) > 1:
            migration_matches = matches.filtered(lambda rec: rec.legacy_partner_id or rec.legacy_source_evidence)
            return (migration_matches or matches)[0].id
    return None


def count_model(model_name: str) -> int:
    if model_name not in env.registry:  # noqa: F821
        return 0
    return env[model_name].sudo().search_count([])  # noqa: F821


ensure_allowed_db()

Request = env["payment.request"].sudo()  # noqa: F821
Project = env["project.project"].sudo()  # noqa: F821
Contract = env["construction.contract"].sudo()  # noqa: F821
Partner = env["res.partner"].sudo()  # noqa: F821

rows = read_csv(PAYLOAD_CSV)
payload_receipt_ids = {clean(row.get("legacy_receipt_id")) for row in rows if clean(row.get("legacy_receipt_id"))}
pre_records = snapshot(Request, PRE_SNAPSHOT_CSV)
pre_existing_receipt_ids = {
    legacy_id
    for rec in pre_records
    if (legacy_id := extract_legacy_receipt_id(rec.note)) in payload_receipt_ids
}
ledger_before = count_model("payment.ledger")
settlement_before = count_model("sc.settlement.order")
account_move_before = count_model("account.move")

errors: list[dict[str, object]] = []
deferred_rows: list[dict[str, object]] = []
if len(rows) != EXPECTED_ROWS:
    errors.append({"error": "unexpected_payload_rows", "actual": len(rows), "expected": EXPECTED_ROWS})

create_vals = []
for index, row in enumerate(rows, start=2):
    if clean(row.get("legacy_receipt_id")) in pre_existing_receipt_ids:
        continue
    resolved_project_id = resolve_project_id(row, Project)
    resolved_contract_id = resolve_contract_id(row, Contract)
    resolved_partner_id = resolve_partner_id(row, Partner)
    contract = Contract.browse(resolved_contract_id).exists() if resolved_contract_id else Contract.browse()
    if not contract:
        deferred_rows.append(
            {
                "line": index,
                "legacy_receipt_id": clean(row.get("legacy_receipt_id")),
                "legacy_contract_id": clean(row.get("legacy_contract_id")),
                "legacy_project_id": clean(row.get("legacy_project_id")),
                "reason": "missing_contract_anchor",
            }
        )
        continue
    request_type = "receive" if contract.type == "out" else "pay"
    vals = {
        "type": request_type,
        "project_id": contract.project_id.id or resolved_project_id or 0,
        "contract_id": contract.id,
        "partner_id": contract.partner_id.id or resolved_partner_id or 0,
        "amount": float(clean(row.get("amount"))),
        "date_request": clean(row.get("date_request")),
        "note": note_with_marker(row),
    }
    unsafe_fields = sorted(set(vals) - SAFE_FIELDS)
    if unsafe_fields:
        errors.append({"line": index, "error": "unsafe_fields", "fields": unsafe_fields})
    if vals["amount"] <= 0:
        errors.append({"line": index, "error": "non_positive_amount", "amount": vals["amount"]})
    if not vals["project_id"] or not Project.browse(vals["project_id"]).exists():
        errors.append({"line": index, "error": "project_missing", "legacy_project_id": clean(row.get("legacy_project_id")), "project_id": vals["project_id"]})
    if not vals["partner_id"] or not Partner.browse(vals["partner_id"]).exists():
        errors.append({"line": index, "error": "partner_missing", "legacy_partner_id": clean(row.get("legacy_partner_id")), "partner_name": clean(row.get("partner_name")), "partner_id": vals["partner_id"]})
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

post_records = snapshot(Request, POST_SNAPSHOT_CSV).filtered(lambda rec: extract_legacy_receipt_id(rec.note) in payload_receipt_ids)
write_csv(ROLLBACK_CSV, SNAPSHOT_FIELDS, created)
ledger_after = count_model("payment.ledger")
settlement_after = count_model("sc.settlement.order")
account_move_after = count_model("account.move")

post_errors = []
expected_creatable = EXPECTED_ROWS - len(deferred_rows)
skipped_existing = len(pre_existing_receipt_ids)
if len(created) + skipped_existing != expected_creatable:
    post_errors.append({"error": "resolved_count_not_expected", "created": len(created), "skipped_existing": skipped_existing, "expected": expected_creatable})
if len(post_records) != expected_creatable:
    post_errors.append({"error": "post_marker_count_not_expected", "count": len(post_records), "expected": expected_creatable})
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
    "skipped_existing": skipped_existing,
    "post_write_match_count": len(post_records),
    "deferred_missing_contract_rows": len(deferred_rows),
    "deferred_missing_contract_samples": deferred_rows[:20],
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
    "decision": "receipt_core_write_complete" if status == "PASS" and not deferred_rows else ("receipt_core_write_partial_with_deferred_contract_gap" if status == "PASS" else "STOP_REVIEW_REQUIRED"),
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
            "skipped_existing": skipped_existing,
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
