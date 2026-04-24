#!/usr/bin/env python3
"""Replay supplier contract summary lines into allowed replay databases."""

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
INPUT_CSV = REPO_ROOT / "artifacts/migration/fresh_db_supplier_contract_line_replay_payload_v1.csv"
INPUT_MANIFEST = REPO_ROOT / "artifacts/migration/fresh_db_supplier_contract_line_replay_adapter_result_v1.json"
OUTPUT_JSON = ARTIFACT_ROOT / "fresh_db_supplier_contract_line_replay_write_result_v1.json"

ensure_allowed_db()
adapter = json.loads(INPUT_MANIFEST.read_text(encoding="utf-8"))
rows = read_csv(INPUT_CSV)
expected_rows = int(adapter["expected_rows"])

Line = env["construction.contract.line"].sudo()  # noqa: F821
Contract = env["construction.contract"].sudo()  # noqa: F821
created = 0
skipped = 0
for row in rows:
    contract = Contract.search([("legacy_contract_id", "=", row["legacy_contract_id"])], limit=1)
    if not contract:
        raise RuntimeError({"missing_parent_supplier_contract": row["legacy_contract_id"], "external_id": row["external_id"]})
    existing = Line.search([("contract_id", "=", contract.id), ("note", "=", row["note"])], limit=1)
    if existing:
        skipped += 1
        continue
    Line.create(
        {
            "contract_id": contract.id,
            "sequence": int(float(row["sequence"] or 0)),
            "qty_contract": float(row["qty_contract"] or 0),
            "price_contract": float(row["price_contract"] or 0),
            "note": row["note"],
        }
    )
    created += 1

env.cr.commit()  # noqa: F821
status = "PASS" if created + skipped == expected_rows else "FAIL"
payload = {
    "status": status,
    "mode": "fresh_db_supplier_contract_line_replay_write",
    "database": env.cr.dbname,  # noqa: F821
    "input_rows": len(rows),
    "created_rows": created,
    "skipped_existing": skipped,
    "db_writes": created,
    "decision": "supplier_contract_line_replay_write_complete" if status == "PASS" else "STOP_REVIEW_REQUIRED",
}
write_json(OUTPUT_JSON, payload)
print("FRESH_DB_SUPPLIER_CONTRACT_LINE_REPLAY_WRITE=" + json.dumps(payload, ensure_ascii=False, sort_keys=True))
