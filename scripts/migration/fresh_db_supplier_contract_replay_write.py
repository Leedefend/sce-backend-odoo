#!/usr/bin/env python3
"""Replay supplier contract headers into allowed replay databases."""

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


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return [dict(row) for row in csv.DictReader(handle)]


def write_json(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


REPO_ROOT = repo_root()
ARTIFACT_ROOT = Path(os.getenv("MIGRATION_ARTIFACT_ROOT", str(REPO_ROOT / "artifacts/migration")))
INPUT_CSV = REPO_ROOT / "artifacts/migration/fresh_db_supplier_contract_replay_payload_v1.csv"
INPUT_MANIFEST = REPO_ROOT / "artifacts/migration/fresh_db_supplier_contract_replay_adapter_result_v1.json"
OUTPUT_JSON = ARTIFACT_ROOT / "fresh_db_supplier_contract_replay_write_result_v1.json"

ensure_allowed_db()
adapter = json.loads(INPUT_MANIFEST.read_text(encoding="utf-8"))
rows = read_csv(INPUT_CSV)
expected_rows = int(adapter["expected_rows"])

Contract = env["construction.contract"].sudo()  # noqa: F821
Project = env["project.project"].sudo()  # noqa: F821
Partner = env["res.partner"].sudo()  # noqa: F821
created = 0
skipped = 0
fallback_partner_hits = 0
for row in rows:
    existing = Contract.search([("legacy_contract_id", "=", row["legacy_contract_id"])], limit=1)
    if existing:
        skipped += 1
        continue
    project = Project.search([("legacy_project_id", "=", row["legacy_project_id"])], limit=1)
    partner = Partner.search([("legacy_partner_id", "=", row["legacy_partner_id"])], limit=1)
    if not partner and row.get("legacy_counterparty_text"):
        partner = Partner.search([("name", "=", row["legacy_counterparty_text"])], limit=1)
        if partner:
            fallback_partner_hits += 1
    if not project:
        raise RuntimeError({"missing_project_anchor": row["legacy_project_id"], "external_id": row["external_id"]})
    if not partner:
        raise RuntimeError(
            {
                "missing_partner_anchor": row["legacy_partner_id"],
                "counterparty_text": row.get("legacy_counterparty_text"),
                "external_id": row["external_id"],
            }
        )
    vals = {
        "legacy_contract_id": row["legacy_contract_id"],
        "legacy_project_id": row["legacy_project_id"],
        "legacy_document_no": row["legacy_document_no"],
        "legacy_contract_no": row["legacy_contract_no"],
        "legacy_status": row["legacy_status"],
        "legacy_deleted_flag": row["legacy_deleted_flag"],
        "legacy_counterparty_text": row["legacy_counterparty_text"],
        "subject": row["subject"],
        "type": row["type"],
        "project_id": project.id,
        "partner_id": partner.id,
        "note": row["note"],
    }
    if row.get("date_contract"):
        vals["date_contract"] = row["date_contract"]
    Contract.create(vals)
    created += 1

env.cr.commit()  # noqa: F821
status = "PASS" if created + skipped == expected_rows else "FAIL"
payload = {
    "status": status,
    "mode": "fresh_db_supplier_contract_replay_write",
    "database": env.cr.dbname,  # noqa: F821
    "input_rows": len(rows),
    "created_rows": created,
    "skipped_existing": skipped,
    "fallback_partner_hits": fallback_partner_hits,
    "db_writes": created,
    "decision": "supplier_contract_replay_write_complete" if status == "PASS" else "STOP_REVIEW_REQUIRED",
}
write_json(OUTPUT_JSON, payload)
print("FRESH_DB_SUPPLIER_CONTRACT_REPLAY_WRITE=" + json.dumps(payload, ensure_ascii=False, sort_keys=True))
