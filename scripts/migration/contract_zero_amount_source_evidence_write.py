#!/usr/bin/env python3
"""Backfill objective zero-amount source evidence for legacy contracts."""

from __future__ import annotations

import csv
import json
import os
from collections import Counter
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
GAP_CSV = Path(
    os.getenv(
        "CONTRACT_AMOUNT_GAP_CSV",
        str(REPO_ROOT / "artifacts/business-fact-audit/sc_demo_after_raw_contract_entry_all_types/contract_amount_missing_rows_v1.csv"),
    )
)
RAW_CONTRACT_CSV = Path(os.getenv("CONSTRUCTION_CONTRACT_RAW_CSV", str(REPO_ROOT / "tmp/raw/contract/contract.csv")))
ARTIFACT_ROOT = Path(
    os.getenv("MIGRATION_ARTIFACT_ROOT", str(REPO_ROOT / "artifacts/migration/contract_zero_amount_source_evidence_v1"))
)
MODE = os.getenv("MIGRATION_WRITE_MODE", "dry-run")
ALLOWLIST = {
    item.strip()
    for item in os.getenv("MIGRATION_REPLAY_DB_ALLOWLIST", "sc_demo,sc_prod_sim,sc_migration_fresh").split(",")
    if item.strip()
}
RAW_AMOUNT_FIELDS = ("GCYSZJ", "D_SCBSJS_QYHTJ", "D_SCBSJS_JSJE", "f_HTJK", "YFK", "ZLBZJ")


def clean(value: object) -> str:
    if value is None:
        return ""
    text = str(value).strip()
    return "" if text in {"False", "false", "None", "none", "NULL", "null"} else text


def write_json(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def ensure_allowed() -> None:
    if MODE not in {"dry-run", "write"}:
        raise RuntimeError({"invalid_write_mode": MODE})
    if env.cr.dbname not in ALLOWLIST:  # noqa: F821
        raise RuntimeError({"db_name_not_allowed": env.cr.dbname, "allowlist": sorted(ALLOWLIST)})  # noqa: F821


def read_gap_rows() -> list[dict[str, str]]:
    with GAP_CSV.open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def read_raw_contract_rows() -> dict[str, dict[str, str]]:
    if not RAW_CONTRACT_CSV.is_file():
        return {}
    rows: dict[str, dict[str, str]] = {}
    with RAW_CONTRACT_CSV.open("r", encoding="utf-8-sig", newline="") as handle:
        for row in csv.DictReader(handle):
            legacy_id = clean(row.get("Id"))
            if legacy_id:
                rows[legacy_id] = row
    return rows


def raw_zero_source(raw_row: dict[str, str]) -> str:
    observed = [field for field in RAW_AMOUNT_FIELDS if clean(raw_row.get(field))]
    if observed:
        return "T_ProjectContract_Out.zero_amount_fields:" + ",".join(observed)
    return "T_ProjectContract_Out.blank_amount_fields:" + ",".join(RAW_AMOUNT_FIELDS)


ensure_allowed()
gap_rows = read_gap_rows()
raw_contract_rows = read_raw_contract_rows()
Contract = env["construction.contract"].sudo().with_context(active_test=False)  # noqa: F821

field_update_counts: Counter[str] = Counter()
source_counts: Counter[str] = Counter()
updates: list[dict[str, object]] = []
skipped: list[dict[str, object]] = []

for row in gap_rows:
    legacy_contract_id = clean(row.get("legacy_contract_id"))
    contract_type = clean(row.get("type"))
    if not legacy_contract_id:
        continue
    contract = Contract.search([("legacy_contract_id", "=", legacy_contract_id), ("type", "=", contract_type)], limit=1)
    if not contract:
        skipped.append({"legacy_contract_id": legacy_contract_id, "reason": "runtime_contract_missing"})
        continue
    if clean(contract.legacy_contract_amount_source):
        skipped.append({"legacy_contract_id": legacy_contract_id, "reason": "amount_source_already_present"})
        continue
    source = ""
    if contract_type == "out":
        raw_row = raw_contract_rows.get(legacy_contract_id)
        if raw_row is not None:
            source = raw_zero_source(raw_row)
    elif contract_type == "in":
        if raw_contract_rows.get(legacy_contract_id) is not None:
            source = raw_zero_source(raw_contract_rows[legacy_contract_id])
        else:
            source = "T_GYSHT_INFO.zero_amount_fields:ZJE,ZJE_NO,ZSE,GLYHTJE"
    if not source:
        skipped.append({"legacy_contract_id": legacy_contract_id, "reason": "source_evidence_missing"})
        continue
    values = {
        "legacy_contract_amount": 0.0,
        "legacy_contract_amount_source": source,
    }
    updates.append(
        {
            "contract_id": contract.id,
            "legacy_contract_id": legacy_contract_id,
            "type": contract_type,
            "legacy_document_no": contract.legacy_document_no,
            "legacy_contract_no": contract.legacy_contract_no,
            "legacy_contract_amount_source": source,
        }
    )
    source_counts[source.split(":", 1)[0]] += 1
    for field in values:
        field_update_counts[field] += 1
    if MODE == "write":
        contract.write(values)

if MODE == "write":
    env.cr.commit()  # noqa: F821

summary = {
    "status": "PASS",
    "mode": "contract_zero_amount_source_evidence",
    "database": env.cr.dbname,  # noqa: F821
    "write_mode": MODE,
    "gap_csv": str(GAP_CSV),
    "raw_contract_csv": str(RAW_CONTRACT_CSV),
    "gap_rows": len(gap_rows),
    "contracts_to_update": len(updates),
    "skipped_rows": len(skipped),
    "source_counts": dict(sorted(source_counts.items())),
    "field_update_counts": dict(sorted(field_update_counts.items())),
}
output_root = ARTIFACT_ROOT / f"contract_zero_amount_source_evidence_{env.cr.dbname}"  # noqa: F821
write_json(output_root / "summary.json", summary)
write_json(output_root / "updates.json", {"rows": updates})
write_json(output_root / "skipped.json", {"rows": skipped})
print("CONTRACT_ZERO_AMOUNT_SOURCE_EVIDENCE=" + json.dumps(summary, ensure_ascii=False, sort_keys=True))
