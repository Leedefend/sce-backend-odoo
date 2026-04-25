#!/usr/bin/env python3
"""Replay receipt invoice line facts into allowed replay databases."""

from __future__ import annotations

import csv
import json
import os
import re
from pathlib import Path


def repo_root() -> Path:
    env_root = os.getenv("MIGRATION_REPO_ROOT")
    candidates = []
    if env_root:
        candidates.append(Path(env_root))
    candidates.extend([Path("/mnt"), Path.cwd()])
    for candidate in candidates:
        if (candidate / "artifacts/migration/fresh_db_receipt_invoice_line_replay_payload_v1.csv").exists():
            return candidate
    return Path.cwd()


def ensure_allowed_db() -> None:
    allowlist = {item.strip() for item in os.getenv("MIGRATION_REPLAY_DB_ALLOWLIST", "sc_migration_fresh").split(",") if item.strip()}
    if env.cr.dbname not in allowlist:  # noqa: F821
        raise RuntimeError({"db_name_not_allowed_for_replay": env.cr.dbname, "allowlist": sorted(allowlist)})  # noqa: F821


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return [dict(row) for row in csv.DictReader(handle)]


def write_json(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


LEGACY_RECEIPT_ID_RE = re.compile(r"legacy_receipt_id=([0-9a-fA-F]+)")


def request_legacy_id_from_ref(request_ref: str) -> str:
    if request_ref.startswith("legacy_receipt_sc_"):
        return request_ref.removeprefix("legacy_receipt_sc_")
    return ""


REPO_ROOT = repo_root()
ARTIFACT_ROOT = Path(os.getenv("MIGRATION_ARTIFACT_ROOT", str(REPO_ROOT / "artifacts/migration")))
INPUT_CSV = REPO_ROOT / "artifacts/migration/fresh_db_receipt_invoice_line_replay_payload_v1.csv"
INPUT_MANIFEST = REPO_ROOT / "artifacts/migration/fresh_db_receipt_invoice_line_replay_adapter_result_v1.json"
OUTPUT_JSON = ARTIFACT_ROOT / "fresh_db_receipt_invoice_line_replay_write_result_v1.json"

ensure_allowed_db()
adapter = json.loads(INPUT_MANIFEST.read_text(encoding="utf-8"))
rows = read_csv(INPUT_CSV)
expected_rows = int(adapter["expected_rows"])

Request = env["payment.request"].sudo()  # noqa: F821
Line = env["sc.receipt.invoice.line"].sudo()  # noqa: F821

existing_line_ids = {
    rec["legacy_invoice_line_id"]
    for rec in Line.search_read([("legacy_invoice_line_id", "!=", False)], ["legacy_invoice_line_id"])
    if rec.get("legacy_invoice_line_id")
}
request_anchor_map: dict[str, int] = {}
for rec in Request.search_read([("note", "ilike", "[migration:receipt_core]")], ["note"]):
    note = rec.get("note") or ""
    match = LEGACY_RECEIPT_ID_RE.search(note)
    if match:
        request_anchor_map[match.group(1)] = rec["id"]

created = 0
skipped = 0
buffer: list[dict[str, object]] = []
batch_size = 500
for row in rows:
    if row["legacy_invoice_line_id"] in existing_line_ids:
        skipped += 1
        continue
    request_id = request_anchor_map.get(request_legacy_id_from_ref(row["request_ref"]))
    if not request_id:
        raise RuntimeError({"missing_receipt_anchor": row["request_ref"], "external_id": row["external_id"]})
    vals = {
        "request_id": request_id,
        "sequence": int(row["sequence"] or 10),
        "legacy_invoice_line_id": row["legacy_invoice_line_id"],
        "legacy_receipt_id": row["legacy_receipt_id"],
        "legacy_invoice_id": row["legacy_invoice_id"] or False,
        "legacy_invoice_child_id": row["legacy_invoice_child_id"] or False,
        "legacy_pid": row["legacy_pid"] or False,
        "legacy_file_bill_id": row["legacy_file_bill_id"] or False,
        "invoice_no": row["invoice_no"] or False,
        "invoice_party_name": row["invoice_party_name"] or False,
        "invoice_issue_company": row["invoice_issue_company"] or False,
        "source_document_no": row["source_document_no"] or False,
        "source_table_name": row["source_table_name"] or False,
        "amount_source": row["amount_source"] or False,
        "invoice_amount": row["invoice_amount"],
        "current_receipt_amount": row["current_receipt_amount"] or 0.0,
        "invoiced_before_amount": row["invoiced_before_amount"] or 0.0,
        "note": row["note"] or False,
        "import_batch": "history_continuity_receipt_invoice_line_v1",
    }
    buffer.append(vals)
    existing_line_ids.add(row["legacy_invoice_line_id"])
    if len(buffer) >= batch_size:
        Line.create(buffer)
        created += len(buffer)
        buffer = []

if buffer:
    Line.create(buffer)
    created += len(buffer)

env.cr.commit()  # noqa: F821
status = "PASS" if created + skipped == expected_rows else "FAIL"
payload = {
    "status": status,
    "mode": "fresh_db_receipt_invoice_line_replay_write",
    "database": env.cr.dbname,  # noqa: F821
    "input_rows": len(rows),
    "created_rows": created,
    "skipped_existing": skipped,
    "db_writes": created,
    "decision": "receipt_invoice_line_replay_write_complete" if status == "PASS" else "STOP_REVIEW_REQUIRED",
}
write_json(OUTPUT_JSON, payload)
print("FRESH_DB_RECEIPT_INVOICE_LINE_REPLAY_WRITE=" + json.dumps(payload, ensure_ascii=False, sort_keys=True))
