#!/usr/bin/env python3
"""Read-only postcheck for upgraded business fact replay surfaces."""

from __future__ import annotations

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
ARTIFACT_ROOT = Path(os.getenv("MIGRATION_ARTIFACT_ROOT", str(REPO_ROOT / "artifacts/migration")))
OUTPUT_JSON = ARTIFACT_ROOT / "fresh_db_business_fact_replay_postcheck_result_v1.json"
OUTPUT_REPORT = ARTIFACT_ROOT / "fresh_db_business_fact_replay_postcheck_report_v1.md"
EXPECTED_PROJECT_ROWS = int(os.getenv("BUSINESS_FACT_EXPECTED_PROJECT_ROWS", "798"))
EXPECTED_CONTRACT_TOTAL = int(os.getenv("BUSINESS_FACT_EXPECTED_CONTRACT_TOTAL", "6850"))
EXPECTED_INCOME_CONTRACTS = int(os.getenv("BUSINESS_FACT_EXPECTED_INCOME_CONTRACTS", "1541"))
EXPECTED_EXPENSE_CONTRACTS = int(os.getenv("BUSINESS_FACT_EXPECTED_EXPENSE_CONTRACTS", "5309"))
EXPECTED_CONTRACT_LINES = int(os.getenv("BUSINESS_FACT_EXPECTED_CONTRACT_LINES", "6566"))
EXPECTED_GENERAL_CONTRACTS = int(os.getenv("BUSINESS_FACT_EXPECTED_GENERAL_CONTRACTS", "41"))
EXPECTED_PURCHASE_FACTS = int(os.getenv("BUSINESS_FACT_EXPECTED_PURCHASE_FACTS", "49"))
EXPECTED_VISIBLE_INVOICE_FACTS = int(os.getenv("BUSINESS_FACT_EXPECTED_VISIBLE_INVOICE_FACTS", "6"))
EXPECTED_VISIBLE_RECEIPT_FACTS = int(os.getenv("BUSINESS_FACT_EXPECTED_VISIBLE_RECEIPT_FACTS", "5"))


def clean(value: object) -> str:
    return "" if value is None else str(value).strip()


def write_json(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def write_report(payload: dict[str, object]) -> None:
    text = f"""# Business Fact Replay Postcheck Report v1

Status: {payload["status"]}

Task: `ITER-2026-05-07-BUSINESS-FACT-UPGRADE-REPLAY`

## Scope

Read-only verification for business facts replayed after project master anchors.

## Counts

```json
{json.dumps(payload["counts"], ensure_ascii=False, indent=2)}
```

## Contract Split Integrity

```json
{json.dumps(payload["contract_split_integrity"], ensure_ascii=False, indent=2)}
```

## Visible Business Facts

```json
{json.dumps(payload["visible_business_fact_reconciliation"], ensure_ascii=False, indent=2)}
```

## Decision

`{payload["decision"]}`
"""
    OUTPUT_REPORT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_REPORT.write_text(text, encoding="utf-8")


def model_exists(model_name: str) -> bool:
    return model_name in env  # noqa: F821


def count(model_name: str, domain=None, *, active_test=False) -> int | None:
    if not model_exists(model_name):
        return None
    return int(env[model_name].sudo().with_context(active_test=active_test).search_count(domain or []))  # noqa: F821


def scalar(sql: str, params=None) -> object:
    env.cr.execute(sql, params or [])  # noqa: F821
    row = env.cr.fetchone()  # noqa: F821
    return row[0] if row else None


def money(value: object) -> float:
    return round(float(value or 0.0), 2)


def close(left: object, right: object) -> bool:
    return abs(money(left) - money(right)) <= 0.01


counts = {
    "project.project.legacy": count("project.project", [("legacy_project_id", "!=", False)]),
    "construction.contract.total": count("construction.contract", []),
    "construction.contract.legacy": count("construction.contract", [("legacy_contract_id", "!=", False)]),
    "construction.contract.income_base": count("construction.contract", [("type", "=", "out")]),
    "construction.contract.expense_base": count("construction.contract", [("type", "=", "in")]),
    "construction.contract.income_wrapper": count("construction.contract.income", []),
    "construction.contract.expense_wrapper": count("construction.contract.expense", []),
    "construction.contract.line": count("construction.contract.line", []),
    "sc.legacy.purchase.contract.fact": count("sc.legacy.purchase.contract.fact", []),
    "sc.general.contract.legacy": count("sc.general.contract", [("source_origin", "=", "legacy")]),
    "sc.invoice.registration.visible_contract_fact": count(
        "sc.invoice.registration",
        [("legacy_source_model", "=", "construction_contract_visible_surface")],
    ),
    "sc.receipt.income.visible_contract_fact": count(
        "sc.receipt.income",
        [("legacy_source_model", "=", "construction_contract_visible_surface")],
    ),
}

contract_split_integrity = {
    "income_wrapper_missing": int(
        scalar(
            """
            SELECT COUNT(*)
              FROM construction_contract c
              LEFT JOIN construction_contract_income i ON i.contract_id = c.id
             WHERE c.type = 'out'
               AND i.id IS NULL
            """
        )
        or 0
    ),
    "expense_wrapper_missing": int(
        scalar(
            """
            SELECT COUNT(*)
              FROM construction_contract c
              LEFT JOIN construction_contract_expense e ON e.contract_id = c.id
             WHERE c.type = 'in'
               AND e.id IS NULL
            """
        )
        or 0
    ),
    "income_wrapper_wrong_type": int(
        scalar(
            """
            SELECT COUNT(*)
              FROM construction_contract_income i
              JOIN construction_contract c ON c.id = i.contract_id
             WHERE c.type != 'out'
            """
        )
        or 0
    ),
    "expense_wrapper_wrong_type": int(
        scalar(
            """
            SELECT COUNT(*)
              FROM construction_contract_expense e
              JOIN construction_contract c ON c.id = e.contract_id
             WHERE c.type != 'in'
            """
        )
        or 0
    ),
    "income_wrapper_duplicates": int(
        scalar(
            """
            SELECT COUNT(*)
              FROM (
                    SELECT contract_id
                      FROM construction_contract_income
                     GROUP BY contract_id
                    HAVING COUNT(*) > 1
                   ) duplicated
            """
        )
        or 0
    ),
    "expense_wrapper_duplicates": int(
        scalar(
            """
            SELECT COUNT(*)
              FROM (
                    SELECT contract_id
                      FROM construction_contract_expense
                     GROUP BY contract_id
                    HAVING COUNT(*) > 1
                   ) duplicated
            """
        )
        or 0
    ),
}

visible_fact_mismatches: list[dict[str, object]] = []
visible_balance_observations: list[dict[str, object]] = []
visible_contract_count = 0
if model_exists("construction.contract"):
    contracts = env["construction.contract"].sudo().search(  # noqa: F821
        [("visible_unreceived_rate", "!=", False), ("legacy_document_no", "!=", False)]
    )
    visible_contract_count = len(contracts)
    for contract in contracts:
        contract.invalidate_recordset(["invoice_amount", "received_amount", "contract_unreceived_amount"])
        mismatches = {}
        if not close(contract.invoice_amount, contract.visible_invoice_amount):
            mismatches["invoice_amount"] = {
                "actual": money(contract.invoice_amount),
                "expected": money(contract.visible_invoice_amount),
            }
        if not close(contract.received_amount, contract.visible_received_amount):
            mismatches["received_amount"] = {
                "actual": money(contract.received_amount),
                "expected": money(contract.visible_received_amount),
            }
        if not close(contract.contract_unreceived_amount, contract.visible_unreceived_amount):
            visible_balance_observations.append(
                {
                    "contract_id": contract.id,
                    "legacy_contract_id": contract.legacy_contract_id or "",
                    "legacy_document_no": contract.legacy_document_no or "",
                    "platform_unreceived": money(contract.contract_unreceived_amount),
                    "visible_unreceived": money(contract.visible_unreceived_amount),
                }
            )
        if mismatches:
            visible_fact_mismatches.append(
                {
                    "contract_id": contract.id,
                    "legacy_contract_id": contract.legacy_contract_id or "",
                    "legacy_document_no": contract.legacy_document_no or "",
                    "mismatches": mismatches,
                }
            )

visible_business_fact_reconciliation = {
    "visible_contracts_with_balance_surface": visible_contract_count,
    "invoice_receipt_mismatch_count": len(visible_fact_mismatches),
    "invoice_receipt_mismatch_samples": visible_fact_mismatches[:20],
    "visible_balance_observation_count": len(visible_balance_observations),
    "visible_balance_observation_samples": visible_balance_observations[:20],
}

expected_counts = {
    "project.project.legacy": EXPECTED_PROJECT_ROWS,
    "construction.contract.total": EXPECTED_CONTRACT_TOTAL,
    "construction.contract.legacy": EXPECTED_CONTRACT_TOTAL,
    "construction.contract.income_base": EXPECTED_INCOME_CONTRACTS,
    "construction.contract.expense_base": EXPECTED_EXPENSE_CONTRACTS,
    "construction.contract.income_wrapper": EXPECTED_INCOME_CONTRACTS,
    "construction.contract.expense_wrapper": EXPECTED_EXPENSE_CONTRACTS,
    "construction.contract.line": EXPECTED_CONTRACT_LINES,
    "sc.legacy.purchase.contract.fact": EXPECTED_PURCHASE_FACTS,
    "sc.general.contract.legacy": EXPECTED_GENERAL_CONTRACTS,
    "sc.invoice.registration.visible_contract_fact": EXPECTED_VISIBLE_INVOICE_FACTS,
    "sc.receipt.income.visible_contract_fact": EXPECTED_VISIBLE_RECEIPT_FACTS,
}

errors: list[dict[str, object]] = []
for key, expected in expected_counts.items():
    actual = counts.get(key)
    if actual != expected:
        errors.append({"error": "unexpected_count", "key": key, "actual": actual, "expected": expected})
for key, actual in contract_split_integrity.items():
    if actual:
        errors.append({"error": "contract_split_integrity_failed", "key": key, "actual": actual, "expected": 0})
if visible_business_fact_reconciliation["invoice_receipt_mismatch_count"]:
    errors.append(
        {
            "error": "visible_business_fact_reconciliation_failed",
            "actual": visible_business_fact_reconciliation["invoice_receipt_mismatch_count"],
            "expected": 0,
        }
    )

status = "PASS" if not errors else "FAIL"
payload = {
    "status": status,
    "mode": "fresh_db_business_fact_replay_postcheck",
    "database": env.cr.dbname,  # noqa: F821
    "db_writes": 0,
    "counts": counts,
    "expected_counts": expected_counts,
    "contract_split_integrity": contract_split_integrity,
    "visible_business_fact_reconciliation": visible_business_fact_reconciliation,
    "errors": errors,
    "decision": "business_fact_replay_acceptance_passed" if status == "PASS" else "STOP_REVIEW_REQUIRED",
}
write_json(OUTPUT_JSON, payload)
write_report(payload)
print(
    "FRESH_DB_BUSINESS_FACT_REPLAY_POSTCHECK="
    + json.dumps(
        {
            "status": status,
            "database": env.cr.dbname,  # noqa: F821
            "contract_total": counts["construction.contract.total"],
            "income_contracts": counts["construction.contract.income_wrapper"],
            "expense_contracts": counts["construction.contract.expense_wrapper"],
            "contract_lines": counts["construction.contract.line"],
            "visible_fact_mismatches": visible_business_fact_reconciliation["invoice_receipt_mismatch_count"],
            "visible_balance_observations": visible_business_fact_reconciliation["visible_balance_observation_count"],
            "db_writes": 0,
        },
        ensure_ascii=False,
        sort_keys=True,
    )
)
