#!/usr/bin/env python3
"""Replay actual outflow draft carriers into allowed replay databases."""

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
        if (candidate / "artifacts/migration/fresh_db_actual_outflow_replay_payload_v1.csv").exists():
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


def resolve_partner(partner_ref: str, partner_model):
    if not partner_ref:
        return None
    if partner_ref.startswith("legacy_partner_sc_"):
        legacy_partner_id = partner_ref.removeprefix("legacy_partner_sc_").replace("_", "-")
        partner = partner_model.search([("legacy_partner_id", "=", legacy_partner_id)], limit=1)
        if partner:
            return partner
    if partner_ref.startswith("legacy_receipt_counterparty_sc_"):
        legacy_partner_id = partner_ref.removeprefix("legacy_receipt_counterparty_sc_").replace("_", "-")
        partner = partner_model.search([("legacy_partner_source", "=", "receipt_counterparty"), ("legacy_partner_id", "=", legacy_partner_id)], limit=1)
        if partner:
            return partner
    if partner_ref.startswith("legacy_contract_counterparty_sc_"):
        legacy_partner_id = partner_ref.removeprefix("legacy_contract_counterparty_sc_").replace("_", "-")
        partner = partner_model.search([("legacy_partner_source", "=", "contract_counterparty"), ("legacy_partner_id", "=", legacy_partner_id)], limit=1)
        if partner:
            return partner
    return None


def legacy_request_id_from_ref(request_external_id: str) -> str:
    if request_external_id.startswith("legacy_outflow_sc_"):
        return request_external_id.removeprefix("legacy_outflow_sc_")
    return ""


LEGACY_OUTFLOW_ID_RE = re.compile(r"legacy_outflow_id=([0-9a-fA-F]+)")


REPO_ROOT = repo_root()
ARTIFACT_ROOT = Path(os.getenv("MIGRATION_ARTIFACT_ROOT", str(REPO_ROOT / "artifacts/migration")))
INPUT_CSV = REPO_ROOT / "artifacts/migration/fresh_db_actual_outflow_replay_payload_v1.csv"
INPUT_MANIFEST = REPO_ROOT / "artifacts/migration/fresh_db_actual_outflow_replay_adapter_result_v1.json"
OUTPUT_JSON = ARTIFACT_ROOT / "fresh_db_actual_outflow_replay_write_result_v1.json"

ensure_allowed_db()
adapter = json.loads(INPUT_MANIFEST.read_text(encoding="utf-8"))
rows = read_csv(INPUT_CSV)
expected_rows = int(adapter["expected_rows"])

Request = env["payment.request"].sudo()  # noqa: F821
Project = env["project.project"].sudo()  # noqa: F821
Partner = env["res.partner"].sudo()  # noqa: F821

project_ids = sorted(
    {
        row["project_ref"].removeprefix("legacy_project_sc_")
        for row in rows
        if row.get("project_ref", "").startswith("legacy_project_sc_")
    }
)
project_map = {
    rec["legacy_project_id"]: rec["id"]
    for rec in Project.search_read([("legacy_project_id", "in", project_ids)], ["legacy_project_id"])
}

partner_master_ids = sorted(
    {
        row["partner_ref"].removeprefix("legacy_partner_sc_").replace("_", "-")
        for row in rows
        if row.get("partner_ref", "").startswith("legacy_partner_sc_")
    }
)
receipt_partner_ids = sorted(
    {
        row["partner_ref"].removeprefix("legacy_receipt_counterparty_sc_").replace("_", "-")
        for row in rows
        if row.get("partner_ref", "").startswith("legacy_receipt_counterparty_sc_")
    }
)
contract_partner_ids = sorted(
    {
        row["partner_ref"].removeprefix("legacy_contract_counterparty_sc_").replace("_", "-")
        for row in rows
        if row.get("partner_ref", "").startswith("legacy_contract_counterparty_sc_")
    }
)
partner_map: dict[str, int] = {}
if partner_master_ids:
    for rec in Partner.search_read([("legacy_partner_id", "in", partner_master_ids)], ["legacy_partner_id"]):
        partner_map[f"legacy_partner_sc_{rec['legacy_partner_id']}"] = rec["id"]
if receipt_partner_ids:
    for rec in Partner.search_read(
        [("legacy_partner_source", "=", "receipt_counterparty"), ("legacy_partner_id", "in", receipt_partner_ids)],
        ["legacy_partner_id"],
    ):
        partner_map[f"legacy_receipt_counterparty_sc_{rec['legacy_partner_id'].replace('-', '_')}"] = rec["id"]
        partner_map[f"legacy_receipt_counterparty_sc_{rec['legacy_partner_id']}"] = rec["id"]
if contract_partner_ids:
    for rec in Partner.search_read(
        [("legacy_partner_source", "=", "contract_counterparty"), ("legacy_partner_id", "in", contract_partner_ids)],
        ["legacy_partner_id"],
    ):
        partner_map[f"legacy_contract_counterparty_sc_{rec['legacy_partner_id'].replace('-', '_')}"] = rec["id"]
        partner_map[f"legacy_contract_counterparty_sc_{rec['legacy_partner_id']}"] = rec["id"]

existing_actual_notes = {
    rec["note"]
    for rec in Request.search_read([("note", "ilike", "[migration:actual_outflow_core]")], ["note"])
    if rec.get("note")
}
request_anchor_map: dict[str, int] = {}
for rec in Request.search_read([("note", "ilike", "[migration:outflow_request_core]")], ["note"]):
    note = rec.get("note") or ""
    match = LEGACY_OUTFLOW_ID_RE.search(note)
    if match:
        request_anchor_map[match.group(1)] = rec["id"]

created = 0
skipped = 0
buffer: list[dict[str, object]] = []
batch_size = 500
for row in rows:
    if row["note"] in existing_actual_notes:
        skipped += 1
        continue
    project_id = project_map.get(row["project_ref"].removeprefix("legacy_project_sc_"))
    partner_id = partner_map.get(row.get("partner_ref", ""))
    request_anchor_id = None
    if row.get("request_external_id"):
        legacy_request_id = legacy_request_id_from_ref(row["request_external_id"])
        request_anchor_id = request_anchor_map.get(legacy_request_id)
    if not project_id:
        raise RuntimeError({"missing_project_anchor": row["project_ref"], "external_id": row["external_id"]})
    if not partner_id:
        raise RuntimeError({"missing_partner_anchor": row.get("partner_ref"), "external_id": row["external_id"]})
    if row.get("request_external_id") and not request_anchor_id:
        raise RuntimeError({"missing_request_anchor": row["request_external_id"], "external_id": row["external_id"]})
    vals = {
        "type": row["type"],
        "project_id": project_id,
        "partner_id": partner_id,
        "amount": row["amount"],
        "note": row["note"],
    }
    if row.get("date_request"):
        vals["date_request"] = row["date_request"]
    buffer.append(vals)
    existing_actual_notes.add(row["note"])
    if len(buffer) >= batch_size:
        Request.create(buffer)
        created += len(buffer)
        buffer = []

if buffer:
    Request.create(buffer)
    created += len(buffer)

env.cr.commit()  # noqa: F821
status = "PASS" if created + skipped == expected_rows else "FAIL"
payload = {
    "status": status,
    "mode": "fresh_db_actual_outflow_replay_write",
    "database": env.cr.dbname,  # noqa: F821
    "input_rows": len(rows),
    "created_rows": created,
    "skipped_existing": skipped,
    "db_writes": created,
    "decision": "actual_outflow_replay_write_complete" if status == "PASS" else "STOP_REVIEW_REQUIRED",
}
write_json(OUTPUT_JSON, payload)
print("FRESH_DB_ACTUAL_OUTFLOW_REPLAY_WRITE=" + json.dumps(payload, ensure_ascii=False, sort_keys=True))
