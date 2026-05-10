#!/usr/bin/env python3
"""Backfill supplier contract amounts from objective legacy amount evidence."""

from __future__ import annotations

import csv
import json
import os
from collections import Counter
from decimal import Decimal, InvalidOperation
from pathlib import Path


def repo_root() -> Path:
    env_root = os.getenv("MIGRATION_REPO_ROOT")
    if env_root:
        return Path(env_root)
    for candidate in (Path("/mnt"), Path.cwd()):
        if (candidate / "addons/smart_construction_core").exists():
            return candidate
    return Path.cwd()


REPO_ROOT = repo_root()
INPUT_CSV = Path(
    os.getenv(
        "SUPPLIER_CONTRACT_AMOUNT_SOURCE_CSV",
        str(REPO_ROOT / "artifacts/migration/supplier_contract_amount_source_v1/supplier_contract_amount_source_from_legacy_mssql_v1.csv"),
    )
)
ARTIFACT_ROOT = Path(os.getenv("MIGRATION_ARTIFACT_ROOT", str(REPO_ROOT / "artifacts/migration/supplier_contract_amount_backfill_v1")))
MODE = os.getenv("MIGRATION_WRITE_MODE", "dry-run")
ALLOWLIST = {
    item.strip()
    for item in os.getenv("MIGRATION_REPLAY_DB_ALLOWLIST", "sc_demo,sc_prod_sim,sc_migration_fresh").split(",")
    if item.strip()
}


def clean(value: object) -> str:
    if value is None:
        return ""
    text = str(value).strip()
    return "" if text in {"False", "false", "None", "none", "NULL", "null"} else text


def parse_amount(value: object) -> Decimal:
    text = clean(value).replace(",", "")
    if not text:
        return Decimal("0")
    try:
        return Decimal(text)
    except InvalidOperation:
        return Decimal("0")


def write_json(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def ensure_allowed() -> None:
    if MODE not in {"dry-run", "write"}:
        raise RuntimeError({"invalid_write_mode": MODE})
    if env.cr.dbname not in ALLOWLIST:  # noqa: F821
        raise RuntimeError({"db_name_not_allowed": env.cr.dbname, "allowlist": sorted(ALLOWLIST)})  # noqa: F821


def read_source(path: Path) -> dict[str, dict[str, str]]:
    rows: dict[str, dict[str, str]] = {}
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        for row in csv.DictReader(handle):
            legacy_contract_id = clean(row.get("legacy_contract_id"))
            amount = parse_amount(row.get("legacy_contract_amount"))
            if legacy_contract_id and amount:
                rows[legacy_contract_id] = {
                    "legacy_contract_amount": str(amount),
                    "legacy_contract_amount_source": clean(row.get("legacy_contract_amount_source")),
                }
    return rows


ensure_allowed()
source_rows = read_source(INPUT_CSV)
Contract = env["construction.contract"].sudo().with_context(active_test=False)  # noqa: F821
contracts = Contract.search([("legacy_contract_id", "in", sorted(source_rows)), ("type", "=", "in")])

field_update_counts: Counter[str] = Counter()
updates: list[dict[str, object]] = []
for contract in contracts:
    source = source_rows.get(clean(contract.legacy_contract_id))
    if not source:
        continue
    if contract.visible_contract_amount:
        continue
    values = {
        "legacy_contract_amount": float(source["legacy_contract_amount"]),
        "legacy_contract_amount_source": source["legacy_contract_amount_source"],
    }
    updates.append(
        {
            "contract_id": contract.id,
            "legacy_contract_id": contract.legacy_contract_id,
            "legacy_contract_no": contract.legacy_contract_no,
            "legacy_contract_amount": source["legacy_contract_amount"],
            "legacy_contract_amount_source": source["legacy_contract_amount_source"],
        }
    )
    for field in values:
        field_update_counts[field] += 1
    if MODE == "write":
        contract.write(values)

if MODE == "write":
    env.cr.commit()  # noqa: F821

summary = {
    "status": "PASS",
    "mode": "supplier_contract_amount_backfill",
    "database": env.cr.dbname,  # noqa: F821
    "write_mode": MODE,
    "input_csv": str(INPUT_CSV),
    "input_rows": len(source_rows),
    "matched_contracts": len(contracts),
    "contracts_to_update": len(updates),
    "field_update_counts": dict(sorted(field_update_counts.items())),
}
output_root = ARTIFACT_ROOT / f"supplier_contract_amount_backfill_{env.cr.dbname}"  # noqa: F821
write_json(output_root / "summary.json", summary)
print("SUPPLIER_CONTRACT_AMOUNT_BACKFILL=" + json.dumps(summary, ensure_ascii=False, sort_keys=True))
