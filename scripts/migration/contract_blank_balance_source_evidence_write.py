#!/usr/bin/env python3
"""Backfill source evidence for blank legacy receivable balance fields."""

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
BALANCE_GAP_CSV = Path(
    os.getenv(
        "CONTRACT_BALANCE_GAP_CSV",
        str(REPO_ROOT / "artifacts/business-fact-audit/sc_demo_after_zero_amount_source_evidence/contract_receivable_balance_missing_rows_v1.csv"),
    )
)
RAW_CONTRACT_CSV = Path(os.getenv("CONSTRUCTION_CONTRACT_RAW_CSV", str(REPO_ROOT / "tmp/raw/contract/contract.csv")))
ARTIFACT_ROOT = Path(
    os.getenv("MIGRATION_ARTIFACT_ROOT", str(REPO_ROOT / "artifacts/migration/contract_blank_balance_source_evidence_v1"))
)
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


def write_json(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def ensure_allowed() -> None:
    if MODE not in {"dry-run", "write"}:
        raise RuntimeError({"invalid_write_mode": MODE})
    if env.cr.dbname not in ALLOWLIST:  # noqa: F821
        raise RuntimeError({"db_name_not_allowed": env.cr.dbname, "allowlist": sorted(ALLOWLIST)})  # noqa: F821


def read_csv_rows(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def read_raw_contract_rows() -> dict[str, dict[str, str]]:
    rows: dict[str, dict[str, str]] = {}
    with RAW_CONTRACT_CSV.open("r", encoding="utf-8-sig", newline="") as handle:
        for row in csv.DictReader(handle):
            legacy_id = clean(row.get("Id"))
            if legacy_id:
                rows[legacy_id] = row
    return rows


def source_marker(raw_row: dict[str, str], fields: tuple[str, ...]) -> str:
    populated = [field for field in fields if clean(raw_row.get(field))]
    if populated:
        return "T_ProjectContract_Out.fields:" + ",".join(populated)
    return "T_ProjectContract_Out.blank_fields:" + ",".join(fields)


ensure_allowed()
gap_rows = read_csv_rows(BALANCE_GAP_CSV)
raw_rows = read_raw_contract_rows()
Contract = env["construction.contract"].sudo().with_context(active_test=False)  # noqa: F821

field_update_counts: Counter[str] = Counter()
source_counts: Counter[str] = Counter()
updates: list[dict[str, object]] = []
skipped: list[dict[str, object]] = []

for row in gap_rows:
    legacy_contract_id = clean(row.get("legacy_contract_id"))
    if not legacy_contract_id:
        skipped.append(
            {
                "contract_id": clean(row.get("contract_id")),
                "legacy_document_no": clean(row.get("legacy_document_no")),
                "legacy_contract_no": clean(row.get("legacy_contract_no")),
                "subject": clean(row.get("subject")),
                "reason": "legacy_contract_id_missing",
            }
        )
        continue
    contract = Contract.search([("legacy_contract_id", "=", legacy_contract_id), ("type", "=", "out")], limit=1)
    raw_row = raw_rows.get(legacy_contract_id)
    if not contract:
        skipped.append({"legacy_contract_id": legacy_contract_id, "reason": "runtime_contract_missing"})
        continue
    if raw_row is None:
        skipped.append({"legacy_contract_id": legacy_contract_id, "reason": "raw_contract_row_missing"})
        continue
    values: dict[str, object] = {}
    if "visible_invoice_amount_source" in contract._fields and not clean(contract.visible_invoice_amount_source):
        values["visible_invoice_amount_source"] = source_marker(raw_row, ("GCLJKPJE",))
    if "visible_received_amount_source" in contract._fields and not clean(contract.visible_received_amount_source):
        values["visible_received_amount_source"] = source_marker(raw_row, ("GCLJYSK_1", "GCLJYSK_2"))
    if "visible_unreceived_amount_source" in contract._fields and not clean(contract.visible_unreceived_amount_source):
        values["visible_unreceived_amount_source"] = source_marker(raw_row, ("GCQK",))
    if not values:
        skipped.append({"legacy_contract_id": legacy_contract_id, "reason": "source_evidence_already_present_or_fields_missing"})
        continue
    updates.append(
        {
            "contract_id": contract.id,
            "legacy_contract_id": legacy_contract_id,
            "legacy_document_no": contract.legacy_document_no,
            "fields": sorted(values),
            **values,
        }
    )
    for field, value in values.items():
        field_update_counts[field] += 1
        source_counts[str(value).split(":", 1)[0]] += 1
    if MODE == "write":
        contract.write(values)

if MODE == "write":
    env.cr.commit()  # noqa: F821

summary = {
    "status": "PASS",
    "mode": "contract_blank_balance_source_evidence",
    "database": env.cr.dbname,  # noqa: F821
    "write_mode": MODE,
    "balance_gap_csv": str(BALANCE_GAP_CSV),
    "raw_contract_csv": str(RAW_CONTRACT_CSV),
    "gap_rows": len(gap_rows),
    "contracts_to_update": len(updates),
    "skipped_rows": len(skipped),
    "field_update_counts": dict(sorted(field_update_counts.items())),
    "source_counts": dict(sorted(source_counts.items())),
}
output_root = ARTIFACT_ROOT / f"contract_blank_balance_source_evidence_{env.cr.dbname}"  # noqa: F821
write_json(output_root / "summary.json", summary)
write_json(output_root / "updates.json", {"rows": updates})
write_json(output_root / "skipped.json", {"rows": skipped})
print("CONTRACT_BLANK_BALANCE_SOURCE_EVIDENCE=" + json.dumps(summary, ensure_ascii=False, sort_keys=True))
