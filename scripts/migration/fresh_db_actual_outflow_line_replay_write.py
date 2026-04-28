#!/usr/bin/env python3
"""Replay actual-outflow child line facts into allowed replay databases."""

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
        if (candidate / "artifacts/migration/fresh_db_actual_outflow_line_replay_payload_v1.csv").exists():
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


LEGACY_ACTUAL_OUTFLOW_ID_RE = re.compile(r"legacy_actual_outflow_id=([0-9a-fA-F]+)")

REPO_ROOT = repo_root()
ARTIFACT_ROOT = Path(os.getenv("MIGRATION_ARTIFACT_ROOT", str(REPO_ROOT / "artifacts/migration")))
INPUT_CSV = REPO_ROOT / "artifacts/migration/fresh_db_actual_outflow_line_replay_payload_v1.csv"
INPUT_MANIFEST = REPO_ROOT / "artifacts/migration/fresh_db_actual_outflow_line_replay_adapter_result_v1.json"
OUTPUT_JSON = ARTIFACT_ROOT / "fresh_db_actual_outflow_line_replay_write_result_v1.json"

ensure_allowed_db()
adapter = json.loads(INPUT_MANIFEST.read_text(encoding="utf-8"))
rows = read_csv(INPUT_CSV)
expected_rows = int(adapter["expected_rows"])

Request = env["payment.request"].sudo()  # noqa: F821
Line = env["payment.request.line"].sudo()  # noqa: F821
Contract = env["construction.contract"].sudo()  # noqa: F821

existing_line_ids = {
    rec["legacy_line_id"]
    for rec in Line.search_read([("legacy_line_id", "ilike", "actual_outflow_line:%")], ["legacy_line_id"])
    if rec.get("legacy_line_id")
}

actual_outflow_map: dict[str, int] = {}
for rec in Request.search_read([("note", "ilike", "[migration:actual_outflow_core]")], ["note"]):
    note = rec.get("note") or ""
    match = LEGACY_ACTUAL_OUTFLOW_ID_RE.search(note)
    if match:
        actual_outflow_map[match.group(1)] = rec["id"]

contract_ids = sorted({row["legacy_supplier_contract_id"] for row in rows if row.get("legacy_supplier_contract_id")})
contract_map = {
    rec["legacy_contract_id"]: rec["id"]
    for rec in Contract.search_read([("legacy_contract_id", "in", contract_ids)], ["legacy_contract_id"])
}

created = 0
skipped = 0
blocked: list[dict[str, str]] = []
buffer: list[dict[str, object]] = []
batch_size = 500
for index, row in enumerate(rows, start=1):
    legacy_line_id = row["legacy_line_id"]
    if legacy_line_id in existing_line_ids:
        skipped += 1
        continue
    request_id = actual_outflow_map.get(row["parent_actual_outflow_id"])
    if not request_id:
        blocked.append(
            {
                "line": str(index),
                "reason": "missing_actual_outflow_anchor",
                "legacy_line_id": legacy_line_id,
                "parent_actual_outflow_id": row["parent_actual_outflow_id"],
            }
        )
        continue
    vals = {
        "request_id": request_id,
        "sequence": index,
        "legacy_line_id": legacy_line_id,
        "legacy_parent_id": row["legacy_parent_id"],
        "legacy_supplier_contract_id": row["legacy_supplier_contract_id"] or False,
        "source_document_no": row["source_document_no"] or False,
        "source_line_type": row["source_line_type"] or "actual_outflow_line",
        "source_counterparty_text": row["source_counterparty_text"] or False,
        "source_contract_no": row["source_contract_no"] or False,
        "amount": row["amount"] or 0.0,
        "paid_before_amount": row["paid_before_amount"] or 0.0,
        "remaining_amount": row["remaining_amount"] or 0.0,
        "current_pay_amount": row["actual_pay_amount"] or row["current_pay_amount"] or 0.0,
        "note": row["note"] or False,
        "import_batch": "history_continuity_actual_outflow_line_v1",
    }
    contract_id = contract_map.get(row.get("legacy_supplier_contract_id") or "")
    if contract_id:
        vals["contract_id"] = contract_id
    buffer.append(vals)
    existing_line_ids.add(legacy_line_id)
    if len(buffer) >= batch_size:
        Line.create(buffer)
        created += len(buffer)
        buffer = []

if buffer:
    Line.create(buffer)
    created += len(buffer)

env.cr.commit()  # noqa: F821
status = "PASS" if created + skipped + len(blocked) == expected_rows else "FAIL"
payload = {
    "status": status,
    "mode": "fresh_db_actual_outflow_line_replay_write",
    "database": env.cr.dbname,  # noqa: F821
    "input_rows": len(rows),
    "created_rows": created,
    "skipped_existing": skipped,
    "blocked_rows": len(blocked),
    "blocked_samples": blocked[:50],
    "db_writes": created,
    "decision": "actual_outflow_line_replay_write_complete" if status == "PASS" else "STOP_REVIEW_REQUIRED",
}
write_json(OUTPUT_JSON, payload)
print("FRESH_DB_ACTUAL_OUTFLOW_LINE_REPLAY_WRITE=" + json.dumps(payload, ensure_ascii=False, sort_keys=True))
