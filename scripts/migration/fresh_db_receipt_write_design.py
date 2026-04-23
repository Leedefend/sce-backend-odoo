#!/usr/bin/env python3
"""Build a fresh DB write design for core receipt rows."""

from __future__ import annotations

import csv
import json
from collections import Counter
from datetime import datetime
from pathlib import Path


REPO_ROOT = Path.cwd()
CORE_PAYLOAD = REPO_ROOT / "artifacts/migration/fresh_db_receipt_core_payload_v1.csv"
PROJECT_ROLLBACK = REPO_ROOT / "artifacts/migration/fresh_db_project_anchor_replay_rollback_targets_v1.csv"
PARTNER_ROLLBACK = REPO_ROOT / "artifacts/migration/fresh_db_partner_l4_replay_rollback_targets_v1.csv"
CONTRACT_PARTNER_RESOLUTION = REPO_ROOT / "artifacts/migration/fresh_db_contract_partner_12_anchor_replay_resolution_v1.csv"
MISSING_PARTNER_RESOLUTION = REPO_ROOT / "artifacts/migration/fresh_db_contract_missing_partner_anchor_resolution_v1.csv"
CONTRACT_RETRY_ROLLBACK = REPO_ROOT / "artifacts/migration/fresh_db_contract_57_retry_rollback_targets_v1.csv"
CONTRACT_REMAINING_ROLLBACK = REPO_ROOT / "artifacts/migration/fresh_db_contract_remaining_rollback_targets_v1.csv"
OUTPUT_JSON = REPO_ROOT / "artifacts/migration/fresh_db_receipt_write_design_result_v1.json"
OUTPUT_CSV = REPO_ROOT / "artifacts/migration/fresh_db_receipt_write_design_payload_v1.csv"
OUTPUT_REPORT = REPO_ROOT / "docs/migration_alignment/fresh_db_receipt_write_design_report_v1.md"
EXPECTED_ROWS = 1683
SAFE_FIELDS = {
    "legacy_receipt_id",
    "target_model",
    "write_action",
    "type",
    "project_id",
    "contract_id",
    "partner_id",
    "amount",
    "date_request",
    "note",
}
OUTPUT_FIELDS = [
    "legacy_receipt_id",
    "target_model",
    "write_action",
    "type",
    "project_id",
    "contract_id",
    "partner_id",
    "amount",
    "date_request",
    "note",
    "legacy_contract_id",
    "legacy_project_id",
    "legacy_partner_id",
    "partner_name",
    "document_no",
]


def clean(value: object) -> str:
    return "" if value is None else str(value).strip()


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return [dict(row) for row in csv.DictReader(handle)]


def write_csv(path: Path, fieldnames: list[str], rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def write_json(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def parse_date(value: str) -> str:
    raw = clean(value)
    if not raw:
        return ""
    for fmt in ("%m/%d/%Y %H:%M:%S", "%m/%d/%Y", "%Y-%m-%d"):
        try:
            return datetime.strptime(raw, fmt).date().isoformat()
        except ValueError:
            continue
    return raw


def project_index() -> dict[str, int]:
    return {
        clean(row.get("legacy_project_id")): int(clean(row.get("id")))
        for row in read_csv(PROJECT_ROLLBACK)
        if clean(row.get("legacy_project_id")) and clean(row.get("id"))
    }


def contract_index() -> dict[str, int]:
    mapping: dict[str, int] = {}
    for path in (CONTRACT_RETRY_ROLLBACK, CONTRACT_REMAINING_ROLLBACK):
        for row in read_csv(path):
            legacy_id = clean(row.get("legacy_contract_id"))
            contract_id = clean(row.get("contract_id"))
            if legacy_id and contract_id:
                mapping[legacy_id] = int(contract_id)
    return mapping


def partner_indexes() -> tuple[dict[str, int], dict[str, int]]:
    by_legacy: dict[str, int] = {}
    by_name: dict[str, int] = {}
    for row in read_csv(PARTNER_ROLLBACK):
        partner_id = clean(row.get("id"))
        if not partner_id:
            continue
        legacy_id = clean(row.get("legacy_partner_id"))
        name = clean(row.get("name"))
        if legacy_id:
            by_legacy[legacy_id] = int(partner_id)
        if name:
            by_name[name] = int(partner_id)
    for path in (CONTRACT_PARTNER_RESOLUTION, MISSING_PARTNER_RESOLUTION):
        if not path.exists():
            continue
        for row in read_csv(path):
            name = clean(row.get("anchor_name"))
            partner_id = clean(row.get("partner_id"))
            if name and partner_id:
                by_name[name] = int(partner_id)
    return by_legacy, by_name


def write_report(payload: dict[str, object]) -> None:
    text = f"""# Fresh DB Receipt Write Design Report V1

Status: {payload["status"]}

Task: `ITER-2026-04-15-FRESH-DB-RECEIPT-WRITE-DESIGN`

## Scope

Convert the approved core receipt payload into target values for
`payment.request(type=receive)`. This batch performs no database writes.

## Result

- source rows: `{payload["source_rows"]}`
- design payload rows: `{payload["design_payload_rows"]}`
- missing project ids: `{payload["missing_project_id_count"]}`
- missing contract ids: `{payload["missing_contract_id_count"]}`
- missing partner ids: `{payload["missing_partner_id_count"]}`
- unsafe fields: `{payload["unsafe_field_count"]}`
- DB writes: `0`

## Decision

`{payload["decision"]}`

## Next

{payload["next_step"]}
"""
    OUTPUT_REPORT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_REPORT.write_text(text, encoding="utf-8")


rows = read_csv(CORE_PAYLOAD)
projects = project_index()
contracts = contract_index()
partner_by_legacy, partner_by_name = partner_indexes()
design_rows: list[dict[str, object]] = []
errors: list[dict[str, object]] = []
missing_projects: set[str] = set()
missing_contracts: set[str] = set()
missing_partners: set[str] = set()
unsafe_fields: Counter[str] = Counter()

for index, row in enumerate(rows, start=2):
    legacy_project_id = clean(row.get("legacy_project_id"))
    legacy_contract_id = clean(row.get("legacy_contract_id"))
    legacy_partner_id = clean(row.get("legacy_partner_id"))
    partner_name = clean(row.get("partner_name"))
    project_id = projects.get(legacy_project_id)
    contract_id = contracts.get(legacy_contract_id)
    partner_id = partner_by_legacy.get(legacy_partner_id) or partner_by_name.get(partner_name)

    if not project_id:
        missing_projects.add(legacy_project_id)
        errors.append({"line": index, "error": "missing_project_id", "legacy_project_id": legacy_project_id})
        continue
    if not contract_id:
        missing_contracts.add(legacy_contract_id)
        errors.append({"line": index, "error": "missing_contract_id", "legacy_contract_id": legacy_contract_id})
        continue
    if not partner_id:
        missing_partners.add(legacy_partner_id or partner_name)
        errors.append({"line": index, "error": "missing_partner_id", "legacy_partner_id": legacy_partner_id, "partner_name": partner_name})
        continue

    vals = {
        "legacy_receipt_id": clean(row.get("legacy_receipt_id")),
        "target_model": "payment.request",
        "write_action": "create",
        "type": "receive",
        "project_id": project_id,
        "contract_id": contract_id,
        "partner_id": partner_id,
        "amount": clean(row.get("amount")),
        "date_request": parse_date(clean(row.get("receipt_date"))),
        "note": clean(row.get("note")),
        "legacy_contract_id": legacy_contract_id,
        "legacy_project_id": legacy_project_id,
        "legacy_partner_id": legacy_partner_id,
        "partner_name": partner_name,
        "document_no": clean(row.get("document_no")),
    }
    unsafe = sorted(set(vals) - set(OUTPUT_FIELDS))
    for field in unsafe:
        unsafe_fields[field] += 1
    design_rows.append(vals)

if len(rows) != EXPECTED_ROWS:
    errors.append({"error": "unexpected_source_rows", "actual": len(rows), "expected": EXPECTED_ROWS})
if len(design_rows) != EXPECTED_ROWS:
    errors.append({"error": "design_payload_count_mismatch", "actual": len(design_rows), "expected": EXPECTED_ROWS})
duplicate_receipts = sorted(
    receipt_id for receipt_id, count in Counter(row["legacy_receipt_id"] for row in design_rows).items() if count > 1
)
if duplicate_receipts:
    errors.append({"error": "duplicate_design_receipt_ids", "ids": duplicate_receipts[:20]})

status = "PASS" if not errors and not unsafe_fields else "FAIL"
write_csv(OUTPUT_CSV, OUTPUT_FIELDS, design_rows)
payload = {
    "status": status,
    "mode": "fresh_db_receipt_write_design",
    "target_model": "payment.request",
    "target_type": "receive",
    "source_rows": len(rows),
    "design_payload_rows": len(design_rows),
    "missing_project_id_count": len(missing_projects),
    "missing_contract_id_count": len(missing_contracts),
    "missing_partner_id_count": len(missing_partners),
    "unsafe_field_count": sum(unsafe_fields.values()),
    "db_writes": 0,
    "errors": errors[:80],
    "decision": "receipt_write_design_ready" if status == "PASS" else "STOP_REVIEW_REQUIRED",
    "next_step": "open controlled receipt write batch for 1683 receive requests" if status == "PASS" else "screen missing target ids",
}
write_json(OUTPUT_JSON, payload)
write_report(payload)
print(
    "FRESH_DB_RECEIPT_WRITE_DESIGN="
    + json.dumps(
        {
            "status": status,
            "source_rows": len(rows),
            "design_payload_rows": len(design_rows),
            "missing_project_id_count": len(missing_projects),
            "missing_contract_id_count": len(missing_contracts),
            "missing_partner_id_count": len(missing_partners),
            "db_writes": 0,
        },
        ensure_ascii=False,
        sort_keys=True,
    )
)
if status != "PASS":
    raise SystemExit(1)
