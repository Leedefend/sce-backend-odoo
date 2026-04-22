#!/usr/bin/env python3
"""Screen contract line readiness for phase 2 contract fact closure."""

from __future__ import annotations

import csv
import json
from collections import Counter
from decimal import Decimal, InvalidOperation
from pathlib import Path


REPO_ROOT = Path.cwd()
RAW_CONTRACT = REPO_ROOT / "tmp/raw/contract/contract.csv"
CONTRACT_RETRY_ROLLBACK = REPO_ROOT / "artifacts/migration/fresh_db_contract_57_retry_rollback_targets_v1.csv"
CONTRACT_REMAINING_ROLLBACK = REPO_ROOT / "artifacts/migration/fresh_db_contract_remaining_rollback_targets_v1.csv"
OUTPUT_JSON = REPO_ROOT / "artifacts/migration/contract_line_readiness_screen_result_v1.json"
OUTPUT_ROWS = REPO_ROOT / "artifacts/migration/contract_line_readiness_screen_rows_v1.csv"
OUTPUT_REPORT = REPO_ROOT / "docs/migration_alignment/contract_line_readiness_screen_report_v1.md"

ROW_FIELDS = [
    "legacy_contract_id",
    "bucket",
    "contract_replayed",
    "deleted_flag",
    "amount_source",
    "amount",
    "subject",
    "legacy_contract_no",
    "legacy_document_no",
    "line_source_type",
    "recommendation",
]
AMOUNT_FIELDS = [
    "GCYSZJ",
    "D_SCBSJS_QYHTJ",
    "D_SCBSJS_JSJE",
    "GCJSZJ",
    "CLHGCSBZGJJE",
    "ZYGCZGJJE",
    "ZLJE",
    "AQWMSGF",
    "NMGBZJ",
    "YFK",
    "ZLBZJ",
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


def best_amount(row: dict[str, str]) -> tuple[str, Decimal]:
    for field in AMOUNT_FIELDS:
        amount = parse_amount(row.get(field))
        if amount > 0:
            return field, amount
    return "", Decimal("0")


def contract_replay_index() -> set[str]:
    ids: set[str] = set()
    for path in (CONTRACT_RETRY_ROLLBACK, CONTRACT_REMAINING_ROLLBACK):
        if not path.exists():
            continue
        for row in read_csv(path):
            legacy_id = clean(row.get("legacy_contract_id"))
            if legacy_id:
                ids.add(legacy_id)
    return ids


def discover_line_sources() -> list[str]:
    candidates: list[str] = []
    for path in (REPO_ROOT / "tmp/raw").glob("**/*"):
        if not path.is_file() or path.name == ".gitkeep":
            continue
        lowered = path.as_posix().lower()
        if path == RAW_CONTRACT:
            continue
        if any(token in lowered for token in ("contract_line", "contractline", "line", "detail", "htmx", "mx")):
            candidates.append(str(path.relative_to(REPO_ROOT)))
    return sorted(candidates)


def write_report(payload: dict[str, object]) -> None:
    buckets = "\n".join(f"- {key}: `{value}`" for key, value in sorted(payload["bucket_counts"].items()))
    text = f"""# Contract Line Readiness Screen Report V1

Status: {payload["status"]}

Task: `ITER-2026-04-15-CONTRACT-LINE-READINESS-SCREEN`

## Scope

Read-only screen for contract line readiness. This batch does not write
`construction.contract.line` and does not touch receipt, payment, settlement,
ledger, or accounting facts.

## Source Discovery

- independent line source files: `{payload["independent_line_source_count"]}`
- raw contract rows: `{payload["raw_contract_rows"]}`
- fresh replayed contract headers: `{payload["fresh_contract_reference_count"]}`

## Buckets

{buckets}

## Recommendation

`{payload["write_go_no_go"]}`

{payload["recommendation_detail"]}
"""
    OUTPUT_REPORT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_REPORT.write_text(text, encoding="utf-8")


raw_rows = read_csv(RAW_CONTRACT)
fresh_contract_ids = contract_replay_index()
line_sources = discover_line_sources()
screen_rows: list[dict[str, object]] = []
bucket_counts: Counter[str] = Counter()

for row in raw_rows:
    legacy_contract_id = clean(row.get("Id"))
    contract_replayed = legacy_contract_id in fresh_contract_ids
    deleted = is_deleted(row.get("DEL"))
    amount_source, amount = best_amount(row)
    subject = clean(row.get("HTBT")) or clean(row.get("f_XMMC")) or clean(row.get("f_GCNR"))

    if deleted:
        bucket = "discard_deleted_contract"
        recommendation = "do_not_write_line"
    elif not contract_replayed:
        bucket = "blocked_contract_header_not_replayed"
        recommendation = "do_not_write_line"
    elif line_sources:
        bucket = "independent_line_source_available_needs_adapter"
        recommendation = "screen_independent_line_source_first"
    elif amount <= 0:
        bucket = "no_structured_line_source_zero_amount"
        recommendation = "do_not_write_line"
    elif not subject:
        bucket = "fallback_single_line_missing_subject"
        recommendation = "policy_required_before_write"
    else:
        bucket = "fallback_single_line_candidate"
        recommendation = "go_only_if_owner_accepts_one_line_per_contract_policy"

    bucket_counts[bucket] += 1
    screen_rows.append(
        {
            "legacy_contract_id": legacy_contract_id,
            "bucket": bucket,
            "contract_replayed": int(contract_replayed),
            "deleted_flag": clean(row.get("DEL")),
            "amount_source": amount_source,
            "amount": str(amount),
            "subject": subject,
            "legacy_contract_no": clean(row.get("HTBH")),
            "legacy_document_no": clean(row.get("DJBH")),
            "line_source_type": "independent" if line_sources else "header_amount_fallback_only",
            "recommendation": recommendation,
        }
    )

fresh_raw_overlap = sum(1 for row in raw_rows if clean(row.get("Id")) in fresh_contract_ids)
fallback_candidates = bucket_counts.get("fallback_single_line_candidate", 0)
if line_sources:
    write_go_no_go = "SCREEN_INDEPENDENT_LINE_SOURCE_FIRST"
    recommendation_detail = "Independent candidate files were found; do not write fallback lines before screening them."
elif fallback_candidates:
    write_go_no_go = "CONDITIONAL_GO_FOR_FALLBACK_SINGLE_LINE_POLICY"
    recommendation_detail = (
        "No independent line source was found. A degraded one-line-per-contract "
        "policy is possible for replayed contracts with positive header amount, "
        "but it must be explicitly accepted because it is not a structured BOQ "
        "line reconstruction."
    )
else:
    write_go_no_go = "NO_GO_NO_LINE_SOURCE"
    recommendation_detail = "No independent line source and no usable fallback amount population were found."

payload = {
    "status": "PASS",
    "mode": "contract_line_readiness_screen",
    "db_writes": 0,
    "raw_contract_rows": len(raw_rows),
    "fresh_contract_reference_count": len(fresh_contract_ids),
    "fresh_raw_overlap": fresh_raw_overlap,
    "independent_line_source_count": len(line_sources),
    "independent_line_sources": line_sources,
    "bucket_counts": dict(sorted(bucket_counts.items())),
    "fallback_single_line_candidates": fallback_candidates,
    "write_go_no_go": write_go_no_go,
    "recommendation_detail": recommendation_detail,
    "next_step": "open contract line policy screen for fallback single-line candidates" if fallback_candidates else "return to owner scheduling",
}
write_csv(OUTPUT_ROWS, ROW_FIELDS, screen_rows)
write_json(OUTPUT_JSON, payload)
write_report(payload)
print(
    "CONTRACT_LINE_READINESS_SCREEN="
    + json.dumps(
        {
            "status": payload["status"],
            "raw_contract_rows": len(raw_rows),
            "fresh_contract_reference_count": len(fresh_contract_ids),
            "fallback_single_line_candidates": fallback_candidates,
            "independent_line_source_count": len(line_sources),
            "write_go_no_go": write_go_no_go,
            "db_writes": 0,
        },
        ensure_ascii=False,
        sort_keys=True,
    )
)
