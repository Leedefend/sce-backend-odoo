#!/usr/bin/env python3
"""Replay receipt invoice attachment URL relations into allowed replay databases."""

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
        if (candidate / "artifacts/migration/fresh_db_receipt_invoice_attachment_replay_payload_v1.csv").exists():
            return candidate
    return Path.cwd()


def ensure_allowed_db() -> None:
    allowlist = {item.strip() for item in os.getenv("MIGRATION_REPLAY_DB_ALLOWLIST", "sc_demo").split(",") if item.strip()}
    if env.cr.dbname not in allowlist:  # noqa: F821
        raise RuntimeError({"db_name_not_allowed_for_replay": env.cr.dbname, "allowlist": sorted(allowlist)})  # noqa: F821


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return [dict(row) for row in csv.DictReader(handle)]


def write_json(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


LEGACY_FILE_ID_RE = re.compile(r"legacy_file_id=([0-9a-fA-F-]+)")


def extract_legacy_invoice_line_id(res_ref: str) -> str:
    value = (res_ref or "").strip()
    if value.startswith("legacy_receipt_invoice_line_sc_"):
        return value.removeprefix("legacy_receipt_invoice_line_sc_")
    return ""


REPO_ROOT = repo_root()
ARTIFACT_ROOT = Path(os.getenv("MIGRATION_ARTIFACT_ROOT", str(REPO_ROOT / "artifacts/migration")))
INPUT_CSV = REPO_ROOT / "artifacts/migration/fresh_db_receipt_invoice_attachment_replay_payload_v1.csv"
INPUT_MANIFEST = REPO_ROOT / "artifacts/migration/fresh_db_receipt_invoice_attachment_replay_adapter_result_v1.json"
OUTPUT_JSON = ARTIFACT_ROOT / "fresh_db_receipt_invoice_attachment_replay_write_result_v1.json"

ensure_allowed_db()
adapter = json.loads(INPUT_MANIFEST.read_text(encoding="utf-8"))
rows = read_csv(INPUT_CSV)
expected_rows = int(adapter["expected_rows"])

Attachment = env["ir.attachment"].sudo()  # noqa: F821
InvoiceLine = env["sc.receipt.invoice.line"].sudo()  # noqa: F821

line_map = {
    rec["legacy_invoice_line_id"]: rec["id"]
    for rec in InvoiceLine.search_read([("legacy_invoice_line_id", "!=", False)], ["legacy_invoice_line_id"])
    if rec.get("legacy_invoice_line_id")
}
existing_file_ids = set()
for rec in Attachment.search_read([("res_model", "=", "sc.receipt.invoice.line"), ("type", "=", "url")], ["description"]):
    description = rec.get("description") or ""
    match = LEGACY_FILE_ID_RE.search(description)
    if match:
        existing_file_ids.add(match.group(1))

created = 0
skipped = 0
buffer: list[dict[str, object]] = []
batch_size = 500
for row in rows:
    description = row["description"] or ""
    match = LEGACY_FILE_ID_RE.search(description)
    legacy_file_id = match.group(1) if match else ""
    if legacy_file_id and legacy_file_id in existing_file_ids:
        skipped += 1
        continue
    legacy_invoice_line_id = extract_legacy_invoice_line_id(row["res_ref"])
    res_id = line_map.get(legacy_invoice_line_id)
    if not res_id:
        raise RuntimeError({"missing_receipt_invoice_line_anchor": row["res_ref"], "external_id": row["external_id"]})
    vals = {
        "name": row["name"] or False,
        "type": row["type"] or "url",
        "url": row["url"] or False,
        "res_model": row["res_model"] or "sc.receipt.invoice.line",
        "res_id": res_id,
        "mimetype": row["mimetype"] or False,
        "description": description or False,
    }
    buffer.append(vals)
    if legacy_file_id:
        existing_file_ids.add(legacy_file_id)
    if len(buffer) >= batch_size:
        Attachment.create(buffer)
        created += len(buffer)
        buffer = []

if buffer:
    Attachment.create(buffer)
    created += len(buffer)

env.cr.commit()  # noqa: F821
status = "PASS" if created + skipped == expected_rows else "FAIL"
payload = {
    "status": status,
    "mode": "fresh_db_receipt_invoice_attachment_replay_write",
    "database": env.cr.dbname,  # noqa: F821
    "input_rows": len(rows),
    "created_rows": created,
    "skipped_existing": skipped,
    "db_writes": created,
    "decision": "receipt_invoice_attachment_replay_write_complete" if status == "PASS" else "STOP_REVIEW_REQUIRED",
}
write_json(OUTPUT_JSON, payload)
print("FRESH_DB_RECEIPT_INVOICE_ATTACHMENT_REPLAY_WRITE=" + json.dumps(payload, ensure_ascii=False, sort_keys=True))
