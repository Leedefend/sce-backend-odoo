#!/usr/bin/env python3
"""Replay historical receipt parents needed by receipt invoice line facts."""

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
        if (candidate / "artifacts/migration/history_receipt_parent_recovery_payload_v1.csv").exists():
            return candidate
    return Path.cwd()


def ensure_allowed_db() -> None:
    allowlist = {item.strip() for item in os.getenv("MIGRATION_REPLAY_DB_ALLOWLIST", "sc_demo").split(",") if item.strip()}
    if env.cr.dbname not in allowlist:  # noqa: F821
        raise RuntimeError({"db_name_not_allowed_for_replay": env.cr.dbname, "allowlist": sorted(allowlist)})  # noqa: F821


def clean(value: object) -> str:
    return "" if value is None else str(value).strip()


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return [dict(row) for row in csv.DictReader(handle)]


def write_json(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


LEGACY_RECEIPT_ID_RE = re.compile(r"legacy_receipt_id=([0-9a-fA-F]+)")


def partner_legacy_id_from_ref(partner_ref: str) -> str:
    value = clean(partner_ref)
    prefixes = (
        "legacy_partner_sc_",
        "legacy_receipt_counterparty_sc_",
        "legacy_contract_counterparty_sc_",
    )
    for prefix in prefixes:
        if value.startswith(prefix):
            return value.removeprefix(prefix)
    return value


REPO_ROOT = repo_root()
ARTIFACT_ROOT = Path(os.getenv("MIGRATION_ARTIFACT_ROOT", str(REPO_ROOT / "artifacts/migration")))
INPUT_CSV = REPO_ROOT / "artifacts/migration/history_receipt_parent_recovery_payload_v1.csv"
INPUT_MANIFEST = REPO_ROOT / "artifacts/migration/history_receipt_parent_recovery_adapter_result_v1.json"
OUTPUT_JSON = ARTIFACT_ROOT / "history_receipt_parent_recovery_write_result_v1.json"

ensure_allowed_db()
adapter = json.loads(INPUT_MANIFEST.read_text(encoding="utf-8"))
rows = read_csv(INPUT_CSV)
expected_rows = int(adapter["payload_rows"])

Request = env["payment.request"].sudo()  # noqa: F821
Project = env["project.project"].sudo()  # noqa: F821
Partner = env["res.partner"].sudo()  # noqa: F821
Contract = env["construction.contract"].sudo()  # noqa: F821

project_map = {
    rec["legacy_project_id"]: rec["id"]
    for rec in Project.search_read([("legacy_project_id", "!=", False)], ["legacy_project_id"])
    if rec.get("legacy_project_id")
}
partner_map = {
    rec["legacy_partner_id"]: rec["id"]
    for rec in Partner.search_read([("legacy_partner_id", "!=", False)], ["legacy_partner_id"])
    if rec.get("legacy_partner_id")
}
contract_map = {
    rec["legacy_contract_id"]: rec["id"]
    for rec in Contract.search_read([("legacy_contract_id", "!=", False)], ["legacy_contract_id"])
    if rec.get("legacy_contract_id")
}
existing_receipts = {}
for rec in Request.search_read([("note", "ilike", "[migration:receipt_core]")], ["note"]):
    note = rec.get("note") or ""
    match = LEGACY_RECEIPT_ID_RE.search(note)
    if match:
        existing_receipts[match.group(1)] = rec["id"]

created = 0
skipped = 0
blocked: list[dict[str, object]] = []
buffer: list[dict[str, object]] = []
batch_size = 500
for row in rows:
    legacy_receipt_id = clean(row.get("legacy_receipt_id"))
    if legacy_receipt_id in existing_receipts:
        skipped += 1
        continue
    legacy_project_id = clean(row.get("project_ref")).removeprefix("legacy_project_sc_")
    legacy_partner_id = partner_legacy_id_from_ref(row.get("partner_ref"))
    legacy_contract_id = clean(row.get("legacy_contract_id"))
    project_id = project_map.get(legacy_project_id)
    partner_id = partner_map.get(legacy_partner_id)
    if not project_id or not partner_id:
        blocked.append(
            {
                "legacy_receipt_id": legacy_receipt_id,
                "legacy_project_id": legacy_project_id,
                "legacy_partner_id": legacy_partner_id,
                "legacy_contract_id": legacy_contract_id,
                "policy_action": clean(row.get("policy_action")),
                "reason": "missing_project_or_partner_anchor",
                "project_hit": bool(project_id),
                "partner_hit": bool(partner_id),
            }
        )
        continue
    buffer.append(
        {
            "type": clean(row.get("type")) or "receive",
            "project_id": project_id,
            "partner_id": partner_id,
            "amount": float(clean(row.get("amount")) or 0.0),
            "date_request": clean(row.get("date_request")) or False,
            "note": clean(row.get("note")) or False,
        }
    )
    existing_receipts[legacy_receipt_id] = -1
    if len(buffer) >= batch_size:
        Request.create(buffer)
        created += len(buffer)
        buffer = []

if buffer:
    Request.create(buffer)
    created += len(buffer)

env.cr.commit()  # noqa: F821
status = "PASS" if created + skipped + len(blocked) == expected_rows else "FAIL"
payload = {
    "status": status,
    "mode": "history_receipt_parent_recovery_write",
    "database": env.cr.dbname,  # noqa: F821
    "input_rows": len(rows),
    "created_rows": created,
    "skipped_existing": skipped,
    "blocked_rows": len(blocked),
    "db_writes": created,
    "blocked_samples": blocked[:20],
    "decision": "history_receipt_parent_recovery_complete" if status == "PASS" else "STOP_REVIEW_REQUIRED",
}
write_json(OUTPUT_JSON, payload)
print("HISTORY_RECEIPT_PARENT_RECOVERY_WRITE=" + json.dumps(payload, ensure_ascii=False, sort_keys=True))
