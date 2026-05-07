#!/usr/bin/env python3
"""Read-only probe for full construction contract attachment replay coverage."""

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
        if (candidate / "tmp/raw/contract/contract.csv").exists():
            return candidate
    return Path.cwd()


REPO_ROOT = repo_root()
ARTIFACT_ROOT = Path(os.getenv("MIGRATION_ARTIFACT_ROOT", str(REPO_ROOT / "artifacts/migration")))
RAW_CSV = Path(os.getenv("CONSTRUCTION_CONTRACT_RAW_CSV", str(REPO_ROOT / "tmp/raw/contract/contract.csv")))
FILE_INDEX_CSV = Path(os.getenv("MIGRATION_FILE_INDEX_CSV", str(ARTIFACT_ROOT / "fresh_db_legacy_file_index_replay_payload_v1.csv")))
OUTPUT_JSON = ARTIFACT_ROOT / "fresh_db_construction_contract_attachment_probe_result_v1.json"
FULL_ATTACHMENT_MARKER = "[migration:construction_contract_attachment_full]"
VISIBLE_ATTACHMENT_MARKER = "[migration:construction_contract_visible_attachment]"
EXPECTED_VISIBLE_ROWS = int(os.getenv("CONSTRUCTION_CONTRACT_INCOME_VISIBLE_EXPECTED_ROWS", "1532"))


def clean(value: object) -> str:
    return "" if value is None else str(value).strip()


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return [dict(row) for row in csv.DictReader(handle)]


def write_json(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def is_legacy_income_visible(row: dict[str, str]) -> bool:
    return (
        clean(row.get("DEL")) != "1"
        and clean(row.get("DJZT")) in {"2", "1", ""}
        and bool(clean(row.get("HTBT")))
        and bool(clean(row.get("FBF")))
    )


Contract = env["construction.contract"].sudo()  # noqa: F821
Attachment = env["ir.attachment"].sudo()  # noqa: F821
ContractEvent = env["sc.contract.event"].sudo()  # noqa: F821

raw_rows = read_csv(RAW_CSV)
visible_rows = [row for row in raw_rows if clean(row.get("Id")) and is_legacy_income_visible(row)]
file_rows = read_csv(FILE_INDEX_CSV)

active_files_by_bill: dict[str, list[dict[str, str]]] = {}
for row in file_rows:
    bill_id = clean(row.get("bill_id"))
    if not bill_id or clean(row.get("active")) != "1" or not clean(row.get("file_name")):
        continue
    active_files_by_bill.setdefault(bill_id, []).append(row)

target_contract_ids = {clean(row.get("Id")) for row in visible_rows}
target_records = Contract.search([("legacy_contract_id", "in", list(target_contract_ids))])
expected_matched_contract_rows = 0
expected_attachment_rows = 0
expected_unmatched_contract_rows = 0
for row in visible_rows:
    files = active_files_by_bill.get(clean(row.get("f_FJ")), [])
    if files:
        expected_matched_contract_rows += 1
        expected_attachment_rows += len({clean(item.get("legacy_file_key")) or clean(item.get("legacy_file_id")) for item in files})
    else:
        expected_unmatched_contract_rows += 1

full_attachment_count = Attachment.search_count(
    [
        ("res_model", "=", "construction.contract"),
        ("description", "ilike", FULL_ATTACHMENT_MARKER),
    ]
)
visible_attachment_count = Attachment.search_count(
    [
        ("res_model", "=", "construction.contract"),
        ("description", "ilike", VISIBLE_ATTACHMENT_MARKER),
    ]
)
approval_event_count = ContractEvent.search_count(
    [
        ("legacy_fact_model", "=", "construction_contract_visible_surface"),
        ("legacy_fact_type", "=", "construction_contract_visible_approval"),
    ]
)

post_errors = []
if len(target_contract_ids) != EXPECTED_VISIBLE_ROWS:
    post_errors.append({"error": "raw_visible_rows_not_expected", "actual": len(target_contract_ids), "expected": EXPECTED_VISIBLE_ROWS})
if len(target_records) != EXPECTED_VISIBLE_ROWS:
    post_errors.append({"error": "target_contract_rows_not_expected", "actual": len(target_records), "expected": EXPECTED_VISIBLE_ROWS})
if full_attachment_count != expected_attachment_rows:
    post_errors.append({"error": "full_attachment_count_not_expected", "actual": full_attachment_count, "expected": expected_attachment_rows})
if visible_attachment_count != 0:
    post_errors.append({"error": "visible_surface_attachment_leftover", "actual": visible_attachment_count, "expected": 0})

status = "PASS" if not post_errors else "FAIL"
payload = {
    "status": status,
    "mode": "fresh_db_construction_contract_attachment_probe",
    "database": env.cr.dbname,  # noqa: F821
    "db_writes": 0,
    "legacy_source_table": "T_ProjectContract_Out",
    "legacy_file_join": "T_ProjectContract_Out.f_FJ = legacy_file_index.bill_id",
    "raw_visible_rows": len(target_contract_ids),
    "target_contract_rows": len(target_records),
    "expected_matched_contract_rows": expected_matched_contract_rows,
    "expected_unmatched_contract_rows": expected_unmatched_contract_rows,
    "expected_attachment_rows": expected_attachment_rows,
    "full_attachment_count": full_attachment_count,
    "visible_surface_attachment_count": visible_attachment_count,
    "approval_event_count": approval_event_count,
    "post_errors": post_errors,
    "decision": "construction_contract_attachment_verified" if status == "PASS" else "STOP_REVIEW_REQUIRED",
}
write_json(OUTPUT_JSON, payload)
print(
    "FRESH_DB_CONSTRUCTION_CONTRACT_ATTACHMENT_PROBE="
    + json.dumps(
        {
            "status": status,
            "raw_visible_rows": len(target_contract_ids),
            "target_contract_rows": len(target_records),
            "expected_matched_contract_rows": expected_matched_contract_rows,
            "expected_unmatched_contract_rows": expected_unmatched_contract_rows,
            "expected_attachment_rows": expected_attachment_rows,
            "full_attachment_count": full_attachment_count,
            "visible_surface_attachment_count": visible_attachment_count,
            "approval_event_count": approval_event_count,
            "db_writes": 0,
        },
        ensure_ascii=False,
        sort_keys=True,
    )
)
if status != "PASS":
    raise RuntimeError({"construction_contract_attachment_probe_failed": post_errors})
