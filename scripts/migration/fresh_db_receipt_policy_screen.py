#!/usr/bin/env python3
"""Apply approved policy to receipt readiness output."""

from __future__ import annotations

import csv
import json
from collections import Counter
from pathlib import Path


REPO_ROOT = Path.cwd()
RAW_CSV = REPO_ROOT / "tmp/raw/receipt/receipt.csv"
SCREEN_CSV = REPO_ROOT / "artifacts/migration/fresh_db_receipt_readiness_screen_rows_v1.csv"
OUTPUT_JSON = REPO_ROOT / "artifacts/migration/fresh_db_receipt_policy_screen_result_v1.json"
CORE_PAYLOAD = REPO_ROOT / "artifacts/migration/fresh_db_receipt_core_payload_v1.csv"
EXCLUDED_ROWS = REPO_ROOT / "artifacts/migration/fresh_db_receipt_excluded_policy_rows_v1.csv"
OUTPUT_REPORT = REPO_ROOT / "docs/migration_alignment/fresh_db_receipt_policy_screen_report_v1.md"
EXPECTED_SOURCE_ROWS = 7412
EXPECTED_CORE_ROWS = 1683
CORE_FIELDS = [
    "legacy_receipt_id",
    "legacy_contract_id",
    "legacy_project_id",
    "legacy_partner_id",
    "partner_name",
    "amount",
    "receipt_date",
    "document_no",
    "legacy_status",
    "legacy_income_category",
    "legacy_payment_method",
    "legacy_bank_account",
    "note",
]
EXCLUDED_FIELDS = [
    "legacy_receipt_id",
    "bucket",
    "policy_action",
    "amount",
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


def write_report(payload: dict[str, object]) -> None:
    lines = "\n".join(f"- {key}: `{value}`" for key, value in sorted(payload["excluded_counts"].items()))
    text = f"""# Fresh DB Receipt Policy Screen Report V1

Status: {payload["status"]}

Task: `ITER-2026-04-15-FRESH-DB-RECEIPT-POLICY-SCREEN`

## Scope

Apply the approved policy to receipt readiness output. This batch creates
payload/evidence files only and performs no database writes.

## Core Payload

- core payload rows: `{payload["core_payload_rows"]}`
- DB writes: `0`

## Excluded Rows

{lines}

## Decision

`{payload["decision"]}`

## Next

{payload["next_step"]}
"""
    OUTPUT_REPORT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_REPORT.write_text(text, encoding="utf-8")


raw_rows = {clean(row.get("Id")): row for row in read_csv(RAW_CSV)}
screen_rows = read_csv(SCREEN_CSV)
core_rows: list[dict[str, object]] = []
excluded_rows: list[dict[str, object]] = []
excluded_counts: Counter[str] = Counter()
errors: list[dict[str, object]] = []

for row in screen_rows:
    legacy_receipt_id = clean(row.get("legacy_receipt_id"))
    raw = raw_rows.get(legacy_receipt_id)
    if not raw:
        errors.append({"legacy_receipt_id": legacy_receipt_id, "error": "raw_row_missing"})
        continue

    bucket = clean(row.get("bucket"))
    if bucket == "core_candidate_ready":
        core_rows.append(
            {
                "legacy_receipt_id": legacy_receipt_id,
                "legacy_contract_id": clean(row.get("legacy_contract_id")),
                "legacy_project_id": clean(row.get("legacy_project_id")),
                "legacy_partner_id": clean(row.get("legacy_partner_id")),
                "partner_name": clean(row.get("partner_name")),
                "amount": clean(row.get("amount")),
                "receipt_date": clean(row.get("receipt_date")),
                "document_no": clean(row.get("document_no")),
                "legacy_status": clean(row.get("status")),
                "legacy_income_category": clean(raw.get("f_SRLBName")),
                "legacy_payment_method": clean(raw.get("FKFSMC")),
                "legacy_bank_account": clean(raw.get("SKZH")),
                "note": clean(raw.get("f_BZ")) or clean(raw.get("BT")) or clean(raw.get("FP")),
            }
        )
        continue

    if bucket == "discard_deleted":
        action = "discard_deleted"
    elif bucket == "auxiliary_or_discard_zero_amount":
        action = "exclude_from_core_zero_amount"
    elif bucket == "blocked_missing_contract_link":
        action = "exclude_from_core_missing_contract_link"
    elif bucket == "blocked_contract_not_replayed":
        action = "hold_blocked_contract_not_replayed"
    elif bucket == "blocked_partner_not_replayed":
        action = "hold_blocked_partner_not_replayed"
    elif bucket == "blocked_project_not_replayed":
        action = "hold_blocked_project_not_replayed"
    elif bucket == "core_candidate_missing_optional_date":
        action = "hold_policy_missing_optional_date"
    else:
        action = "hold_unknown_bucket"

    excluded_counts[action] += 1
    excluded_rows.append(
        {
            "legacy_receipt_id": legacy_receipt_id,
            "bucket": bucket,
            "policy_action": action,
            "amount": clean(row.get("amount")),
            "legacy_contract_id": clean(row.get("legacy_contract_id")),
            "legacy_project_id": clean(row.get("legacy_project_id")),
            "legacy_partner_id": clean(row.get("legacy_partner_id")),
            "partner_name": clean(row.get("partner_name")),
            "document_no": clean(row.get("document_no")),
        }
    )

if len(screen_rows) != EXPECTED_SOURCE_ROWS:
    errors.append({"error": "unexpected_screen_rows", "actual": len(screen_rows), "expected": EXPECTED_SOURCE_ROWS})
if len(core_rows) != EXPECTED_CORE_ROWS:
    errors.append({"error": "core_payload_count_mismatch", "actual": len(core_rows), "expected": EXPECTED_CORE_ROWS})
duplicate_receipts = sorted(
    receipt_id for receipt_id, count in Counter(row["legacy_receipt_id"] for row in core_rows).items() if count > 1
)
if duplicate_receipts:
    errors.append({"error": "duplicate_core_payload_receipt_ids", "ids": duplicate_receipts[:20]})

status = "PASS" if not errors else "FAIL"
write_csv(CORE_PAYLOAD, CORE_FIELDS, core_rows)
write_csv(EXCLUDED_ROWS, EXCLUDED_FIELDS, excluded_rows)
payload = {
    "status": status,
    "mode": "fresh_db_receipt_policy_screen",
    "source_rows": len(screen_rows),
    "core_payload_rows": len(core_rows),
    "excluded_rows": len(excluded_rows),
    "excluded_counts": dict(sorted(excluded_counts.items())),
    "db_writes": 0,
    "errors": errors,
    "decision": "receipt_core_payload_ready" if status == "PASS" else "STOP_REVIEW_REQUIRED",
    "next_step": "open receipt write design for core payload",
}
write_json(OUTPUT_JSON, payload)
write_report(payload)
print(
    "FRESH_DB_RECEIPT_POLICY_SCREEN="
    + json.dumps(
        {
            "status": status,
            "core_payload_rows": len(core_rows),
            "excluded_rows": len(excluded_rows),
            "db_writes": 0,
        },
        ensure_ascii=False,
        sort_keys=True,
    )
)
if status != "PASS":
    raise SystemExit(1)
