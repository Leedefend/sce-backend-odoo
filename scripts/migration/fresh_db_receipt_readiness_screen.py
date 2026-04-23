#!/usr/bin/env python3
"""Screen legacy receipt rows for fresh DB replay readiness."""

from __future__ import annotations

import csv
import json
from collections import Counter
from decimal import Decimal, InvalidOperation
from pathlib import Path


REPO_ROOT = Path.cwd()
RAW_CSV = REPO_ROOT / "tmp/raw/receipt/receipt.csv"
PARTNER_ROLLBACK = REPO_ROOT / "artifacts/migration/fresh_db_partner_l4_replay_rollback_targets_v1.csv"
MISSING_PARTNER_RESOLUTION = REPO_ROOT / "artifacts/migration/fresh_db_contract_missing_partner_anchor_resolution_v1.csv"
CONTRACT_PARTNER_RESOLUTION = REPO_ROOT / "artifacts/migration/fresh_db_contract_partner_12_anchor_replay_resolution_v1.csv"
CONTRACT_RETRY_ROLLBACK = REPO_ROOT / "artifacts/migration/fresh_db_contract_57_retry_rollback_targets_v1.csv"
CONTRACT_REMAINING_ROLLBACK = REPO_ROOT / "artifacts/migration/fresh_db_contract_remaining_rollback_targets_v1.csv"
PROJECT_ROLLBACK = REPO_ROOT / "artifacts/migration/fresh_db_project_anchor_replay_rollback_targets_v1.csv"
OUTPUT_JSON = REPO_ROOT / "artifacts/migration/fresh_db_receipt_readiness_screen_result_v1.json"
OUTPUT_ROWS = REPO_ROOT / "artifacts/migration/fresh_db_receipt_readiness_screen_rows_v1.csv"
OUTPUT_REPORT = REPO_ROOT / "docs/migration_alignment/fresh_db_receipt_readiness_screen_report_v1.md"
EXPECTED_ROWS = 7412
ROW_FIELDS = [
    "legacy_receipt_id",
    "bucket",
    "amount",
    "receipt_date",
    "legacy_contract_id",
    "contract_replayed",
    "legacy_project_id",
    "project_replayed",
    "legacy_partner_id",
    "partner_replayed",
    "partner_name",
    "deleted_flag",
    "status",
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


def parse_amount(value: object) -> Decimal:
    try:
        return Decimal(clean(value) or "0")
    except InvalidOperation:
        return Decimal("0")


def is_deleted(value: object) -> bool:
    normalized = clean(value).lower()
    return bool(normalized) and normalized not in {"0", "false", "no", "n", "否"}


def first_nonempty(row: dict[str, str], fields: list[str]) -> str:
    for field in fields:
        value = clean(row.get(field))
        if value:
            return value
    return ""


def contract_ids() -> set[str]:
    ids: set[str] = set()
    for path in (CONTRACT_RETRY_ROLLBACK, CONTRACT_REMAINING_ROLLBACK):
        if not path.exists():
            continue
        for row in read_csv(path):
            legacy_id = clean(row.get("legacy_contract_id"))
            if legacy_id:
                ids.add(legacy_id)
    return ids


def project_ids() -> set[str]:
    return {
        clean(row.get("legacy_project_id"))
        for row in read_csv(PROJECT_ROLLBACK)
        if clean(row.get("legacy_project_id"))
    }


def partner_indexes() -> tuple[set[str], set[str]]:
    legacy_ids = {
        clean(row.get("legacy_partner_id"))
        for row in read_csv(PARTNER_ROLLBACK)
        if clean(row.get("legacy_partner_id"))
    }
    names = {clean(row.get("name")) for row in read_csv(PARTNER_ROLLBACK) if clean(row.get("name"))}
    for path in (MISSING_PARTNER_RESOLUTION, CONTRACT_PARTNER_RESOLUTION):
        if not path.exists():
            continue
        for row in read_csv(path):
            name = clean(row.get("anchor_name"))
            if name:
                names.add(name)
    return legacy_ids, names


def write_report(payload: dict[str, object]) -> None:
    counts = payload["bucket_counts"]
    lines = "\n".join(f"- {key}: `{value}`" for key, value in sorted(counts.items()))
    text = f"""# Fresh DB Receipt Readiness Screen Report V1

Status: {payload["status"]}

Task: `ITER-2026-04-15-FRESH-DB-RECEIPT-READINESS-SCREEN`

## Scope

Classify legacy receipt rows for replay readiness. This batch performs no
database reads or writes and does not create payment, settlement, or accounting
facts.

## Counts

- source rows: `{payload["source_rows"]}`
- DB writes: `0`

## Buckets

{lines}

## Decision

`{payload["decision"]}`

## Next

{payload["next_step"]}
"""
    OUTPUT_REPORT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_REPORT.write_text(text, encoding="utf-8")


rows = read_csv(RAW_CSV)
contracts = contract_ids()
projects = project_ids()
partner_legacy_ids, partner_names = partner_indexes()
screen_rows: list[dict[str, object]] = []
bucket_counts: Counter[str] = Counter()

for row in rows:
    amount = parse_amount(row.get("f_JE"))
    legacy_contract_id = first_nonempty(row, ["SGHTID", "GLHTID", "HTID"])
    legacy_project_id = first_nonempty(row, ["XMID", "LYXMID", "TSXMID"])
    legacy_partner_id = clean(row.get("WLDWID"))
    partner_name = clean(row.get("WLDWMC"))
    receipt_date = first_nonempty(row, ["f_RQ", "LRSJ", "f_LRSJ"])
    deleted = is_deleted(row.get("DEL"))
    contract_ready = bool(legacy_contract_id and legacy_contract_id in contracts)
    project_ready = bool(legacy_project_id and legacy_project_id in projects)
    partner_ready = bool(
        (legacy_partner_id and legacy_partner_id in partner_legacy_ids)
        or (partner_name and partner_name in partner_names)
    )

    if deleted:
        bucket = "discard_deleted"
    elif amount <= 0:
        bucket = "auxiliary_or_discard_zero_amount"
    elif not legacy_contract_id:
        bucket = "blocked_missing_contract_link"
    elif not contract_ready:
        bucket = "blocked_contract_not_replayed"
    elif not legacy_partner_id and not partner_name:
        bucket = "blocked_missing_partner_reference"
    elif not partner_ready:
        bucket = "blocked_partner_not_replayed"
    elif legacy_project_id and not project_ready:
        bucket = "blocked_project_not_replayed"
    elif not receipt_date:
        bucket = "core_candidate_missing_optional_date"
    else:
        bucket = "core_candidate_ready"

    bucket_counts[bucket] += 1
    screen_rows.append(
        {
            "legacy_receipt_id": clean(row.get("Id")),
            "bucket": bucket,
            "amount": str(amount),
            "receipt_date": receipt_date,
            "legacy_contract_id": legacy_contract_id,
            "contract_replayed": int(contract_ready),
            "legacy_project_id": legacy_project_id,
            "project_replayed": int(project_ready),
            "legacy_partner_id": legacy_partner_id,
            "partner_replayed": int(partner_ready),
            "partner_name": partner_name,
            "deleted_flag": clean(row.get("DEL")),
            "status": clean(row.get("DJZT")),
            "document_no": clean(row.get("DJBH")),
        }
    )

status = "PASS" if len(rows) == EXPECTED_ROWS and len(screen_rows) == len(rows) else "FAIL"
payload = {
    "status": status,
    "mode": "fresh_db_receipt_readiness_screen",
    "source_rows": len(rows),
    "expected_source_rows": EXPECTED_ROWS,
    "screen_rows": len(screen_rows),
    "contract_reference_count": len(contracts),
    "project_reference_count": len(projects),
    "partner_legacy_reference_count": len(partner_legacy_ids),
    "bucket_counts": dict(sorted(bucket_counts.items())),
    "db_writes": 0,
    "decision": "receipt_readiness_screen_complete" if status == "PASS" else "STOP_REVIEW_REQUIRED",
    "next_step": "open dedicated receipt policy screen for core candidates and blocker handling",
}
write_csv(OUTPUT_ROWS, ROW_FIELDS, screen_rows)
write_json(OUTPUT_JSON, payload)
write_report(payload)
print(
    "FRESH_DB_RECEIPT_READINESS_SCREEN="
    + json.dumps(
        {
            "status": status,
            "source_rows": len(rows),
            "core_candidate_ready": bucket_counts.get("core_candidate_ready", 0),
            "blocked_contract_not_replayed": bucket_counts.get("blocked_contract_not_replayed", 0),
            "blocked_partner_not_replayed": bucket_counts.get("blocked_partner_not_replayed", 0),
            "db_writes": 0,
        },
        ensure_ascii=False,
        sort_keys=True,
    )
)
if status != "PASS":
    raise SystemExit(1)
