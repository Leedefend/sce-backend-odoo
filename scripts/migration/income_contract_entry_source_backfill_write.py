#!/usr/bin/env python3
"""Backfill contract entry user/time from raw legacy contract CSV."""

from __future__ import annotations

import csv
import json
import os
from collections import Counter
from datetime import datetime
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
RAW_CSV = Path(os.getenv("CONSTRUCTION_CONTRACT_RAW_CSV", str(REPO_ROOT / "tmp/raw/contract/contract.csv")))
ARTIFACT_ROOT = Path(os.getenv("MIGRATION_ARTIFACT_ROOT", str(REPO_ROOT / "artifacts/migration/income_contract_entry_source_backfill_v1")))
MODE = os.getenv("MIGRATION_WRITE_MODE", "dry-run")
ALLOWLIST = {
    item.strip()
    for item in os.getenv("MIGRATION_REPLAY_DB_ALLOWLIST", "sc_demo,sc_prod_sim,sc_migration_fresh").split(",")
    if item.strip()
}
TECHNICAL_USERS = {"admin", "administrator", "odoobot", "system", "系统", "系统导入"}
CONTRACT_TYPES = {
    item.strip()
    for item in os.getenv("CONSTRUCTION_CONTRACT_ENTRY_TYPES", "out,in").split(",")
    if item.strip()
}


def clean(value: object) -> str:
    if value is None:
        return ""
    text = str(value).strip()
    return "" if text in {"False", "false", "None", "none", "NULL", "null"} else text


def normalize_user(value: object) -> str:
    text = clean(value)
    return "" if text.lower() in TECHNICAL_USERS or text in TECHNICAL_USERS else text


def parse_datetime(value: object) -> str:
    text = clean(value)
    if not text:
        return ""
    normalized = text.replace("T", " ")
    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M:%S.%f", "%m/%d/%Y %H:%M:%S", "%m/%d/%Y %H:%M:%S.%f"):
        try:
            return datetime.strptime(normalized[:26], fmt).strftime("%Y-%m-%d %H:%M:%S")
        except ValueError:
            continue
    return ""


def write_json(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def ensure_allowed() -> None:
    if MODE not in {"dry-run", "write"}:
        raise RuntimeError({"invalid_write_mode": MODE})
    if env.cr.dbname not in ALLOWLIST:  # noqa: F821
        raise RuntimeError({"db_name_not_allowed": env.cr.dbname, "allowlist": sorted(ALLOWLIST)})  # noqa: F821


def read_raw(path: Path) -> dict[str, dict[str, str]]:
    rows: dict[str, dict[str, str]] = {}
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        for row in csv.DictReader(handle):
            legacy_id = clean(row.get("Id"))
            if not legacy_id:
                continue
            rows[legacy_id] = {
                "entry_user_text": normalize_user(row.get("LRR")) or normalize_user(row.get("f_LRR")),
                "entry_time": parse_datetime(row.get("LRRQ")) or parse_datetime(row.get("f_LRSJ")),
                "entry_legacy_user_id": clean(row.get("LRRID")),
            }
    return rows


ensure_allowed()
raw_rows = read_raw(RAW_CSV)
Contract = env["construction.contract"].sudo().with_context(active_test=False)  # noqa: F821
contracts = Contract.search(
    [
        ("legacy_contract_id", "in", sorted(raw_rows)),
        ("type", "in", sorted(CONTRACT_TYPES)),
        "|",
        ("entry_user_text", "=", False),
        ("entry_time", "=", False),
    ]
)

updates: list[dict[str, object]] = []
field_update_counts: Counter[str] = Counter()
for contract in contracts:
    source = raw_rows.get(clean(contract.legacy_contract_id))
    if not source:
        continue
    values: dict[str, object] = {}
    if source["entry_user_text"] and not clean(contract.entry_user_text):
        values["entry_user_text"] = source["entry_user_text"]
    if source["entry_time"] and not contract.entry_time:
        values["entry_time"] = source["entry_time"]
    if not values:
        continue
    updates.append(
        {
            "contract_id": contract.id,
            "legacy_contract_id": contract.legacy_contract_id,
            "legacy_document_no": contract.legacy_document_no,
            "fields": sorted(values),
            "entry_legacy_user_id": source["entry_legacy_user_id"],
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
    "mode": "income_contract_entry_source_backfill",
    "database": env.cr.dbname,  # noqa: F821
    "write_mode": MODE,
    "raw_csv": str(RAW_CSV),
    "contract_types": sorted(CONTRACT_TYPES),
    "matched_contracts": len(contracts),
    "contracts_to_update": len(updates),
    "field_update_counts": dict(sorted(field_update_counts.items())),
}
output_root = ARTIFACT_ROOT / f"income_contract_entry_source_backfill_{env.cr.dbname}"  # noqa: F821
write_json(output_root / "summary.json", summary)
print("INCOME_CONTRACT_ENTRY_BACKFILL=" + json.dumps(summary, ensure_ascii=False, sort_keys=True))
