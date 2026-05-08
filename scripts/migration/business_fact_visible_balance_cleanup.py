#!/usr/bin/env python3
"""Classify legacy visible contract balance deltas without mutating facts."""

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


REPO_ROOT = repo_root()
ARTIFACT_ROOT = Path(
    os.getenv(
        "MIGRATION_ARTIFACT_ROOT",
        str(REPO_ROOT / "artifacts/migration/business_fact_data_cleanup"),
    )
)
OUTPUT_JSON = ARTIFACT_ROOT / "business_fact_visible_balance_cleanup_result_v1.json"
OUTPUT_CSV = ARTIFACT_ROOT / "business_fact_visible_balance_cleanup_rows_v1.csv"
OUTPUT_REPORT = ARTIFACT_ROOT / "business_fact_visible_balance_cleanup_report_v1.md"


def money(value: object) -> float:
    return round(float(value or 0.0), 2)


def close(left: object, right: object) -> bool:
    return abs(money(left) - money(right)) <= 0.01


def text(value: object) -> str:
    return "" if value is None else str(value).strip()


def classify(row: dict[str, object]) -> str:
    visible_unreceived = money(row["visible_unreceived_amount"])
    visible_received = money(row["visible_received_amount"])
    visible_invoice = money(row["visible_invoice_amount"])
    implied_received = money(row["implied_received_from_visible_balance"])
    platform_unreceived = money(row["platform_contract_unreceived_amount"])

    if visible_unreceived < 0 and visible_received <= 0 and visible_invoice <= 0:
        return "legacy_visible_negative_balance_without_transaction_fact"
    if visible_unreceived < 0:
        return "legacy_visible_over_receipt_or_manual_credit_balance"
    if visible_received <= 0 and visible_invoice <= 0 and not close(platform_unreceived, visible_unreceived):
        if implied_received > 0:
            return "legacy_visible_partial_or_closed_balance_without_transaction_fact"
        return "legacy_visible_manual_balance_delta_without_transaction_fact"
    return "legacy_visible_manual_balance_delta"


def write_json(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def write_csv(path: Path, rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fields = [
        "classification",
        "contract_id",
        "legacy_contract_id",
        "legacy_document_no",
        "name",
        "partner",
        "project",
        "visible_contract_amount",
        "visible_invoice_amount",
        "visible_received_amount",
        "visible_unreceived_amount",
        "visible_unreceived_rate",
        "platform_invoice_amount",
        "platform_received_amount",
        "platform_contract_unreceived_amount",
        "implied_received_from_visible_balance",
        "visible_vs_platform_unreceived_delta",
        "invoice_receipt_fact_matches",
    ]
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def write_report(payload: dict[str, object]) -> None:
    samples = payload["rows"][:20]
    text_body = f"""# Business Fact Visible Balance Cleanup v1

Status: {payload["status"]}

Task: `ITER-2026-05-07-BUSINESS-FACT-DATA-CLEANUP`

## Scope

Read-only classification for legacy construction-contract visible balance
differences. This does not create invoices, receipts, or negative correction
rows.

## Summary

```json
{json.dumps(payload["summary"], ensure_ascii=False, indent=2)}
```

## Samples

```json
{json.dumps(samples, ensure_ascii=False, indent=2)}
```

## Decision

`{payload["decision"]}`
"""
    OUTPUT_REPORT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_REPORT.write_text(text_body, encoding="utf-8")


Contract = env["construction.contract"].sudo()  # noqa: F821
Invoice = env["sc.invoice.registration"].sudo()  # noqa: F821
Receipt = env["sc.receipt.income"].sudo()  # noqa: F821

rows: list[dict[str, object]] = []
contracts = Contract.search([("visible_unreceived_rate", "!=", False), ("legacy_document_no", "!=", False)])
for contract in contracts:
    contract.invalidate_recordset(
        [
            "invoice_amount",
            "received_amount",
            "contract_unreceived_amount",
        ]
    )
    if close(contract.contract_unreceived_amount, contract.visible_unreceived_amount):
        continue

    invoice_rows = Invoice.search_count([("contract_id", "=", contract.id)])
    receipt_rows = Receipt.search_count([("contract_id", "=", contract.id)])
    implied_received = money(contract.visible_contract_amount) - money(contract.visible_unreceived_amount)
    row = {
        "contract_id": contract.id,
        "legacy_contract_id": contract.legacy_contract_id or "",
        "legacy_document_no": contract.legacy_document_no or "",
        "name": contract.name or "",
        "partner": contract.partner_id.display_name or "",
        "project": contract.project_id.display_name or "",
        "visible_contract_amount": money(contract.visible_contract_amount),
        "visible_invoice_amount": money(contract.visible_invoice_amount),
        "visible_received_amount": money(contract.visible_received_amount),
        "visible_unreceived_amount": money(contract.visible_unreceived_amount),
        "visible_unreceived_rate": contract.visible_unreceived_rate or "",
        "platform_invoice_amount": money(contract.invoice_amount),
        "platform_received_amount": money(contract.received_amount),
        "platform_contract_unreceived_amount": money(contract.contract_unreceived_amount),
        "implied_received_from_visible_balance": money(implied_received),
        "visible_vs_platform_unreceived_delta": money(
            money(contract.visible_unreceived_amount) - money(contract.contract_unreceived_amount)
        ),
        "invoice_rows": invoice_rows,
        "receipt_rows": receipt_rows,
        "invoice_receipt_fact_matches": close(contract.invoice_amount, contract.visible_invoice_amount)
        and close(contract.received_amount, contract.visible_received_amount),
    }
    row["classification"] = classify(row)
    rows.append(row)

classification_counts: dict[str, int] = {}
for row in rows:
    key = text(row["classification"])
    classification_counts[key] = classification_counts.get(key, 0) + 1

invoice_receipt_mismatches = [
    row for row in rows if not bool(row["invoice_receipt_fact_matches"])
]
summary = {
    "database": env.cr.dbname,  # noqa: F821
    "db_writes": 0,
    "visible_balance_observation_count": len(rows),
    "classification_counts": classification_counts,
    "invoice_receipt_mismatch_count": len(invoice_receipt_mismatches),
    "negative_visible_balance_count": sum(1 for row in rows if money(row["visible_unreceived_amount"]) < 0),
    "no_invoice_receipt_row_count": sum(
        1 for row in rows if int(row["invoice_rows"]) == 0 and int(row["receipt_rows"]) == 0
    ),
}

errors = []
if invoice_receipt_mismatches:
    errors.append(
        {
            "error": "invoice_receipt_fact_mismatch_in_visible_balance_cleanup",
            "actual": len(invoice_receipt_mismatches),
            "expected": 0,
        }
    )

status = "PASS" if not errors else "FAIL"
payload = {
    "status": status,
    "mode": "business_fact_visible_balance_cleanup",
    "summary": summary,
    "rows": rows,
    "errors": errors,
    "decision": "visible_balance_deltas_classified_as_legacy_surface_observations"
    if status == "PASS"
    else "STOP_REVIEW_REQUIRED",
}
write_json(OUTPUT_JSON, payload)
write_csv(OUTPUT_CSV, rows)
write_report(payload)
print(
    "BUSINESS_FACT_VISIBLE_BALANCE_CLEANUP="
    + json.dumps(
        {
            "status": status,
            "database": env.cr.dbname,  # noqa: F821
            "visible_balance_observations": len(rows),
            "classification_counts": classification_counts,
            "invoice_receipt_mismatches": len(invoice_receipt_mismatches),
            "db_writes": 0,
        },
        ensure_ascii=False,
        sort_keys=True,
    )
)
