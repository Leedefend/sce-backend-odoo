#!/usr/bin/env python3
"""Read-only probe for legacy construction contract income ledger count alignment."""

from __future__ import annotations

import csv
import json
import os
from decimal import Decimal, InvalidOperation
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
OUTPUT_JSON = ARTIFACT_ROOT / "fresh_db_construction_contract_income_count_probe_result_v1.json"
EXPECTED_TARGET_ROWS = int(os.getenv("CONSTRUCTION_CONTRACT_INCOME_VISIBLE_EXPECTED_ROWS", "1532"))


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


def parse_amount(value: object) -> Decimal:
    text = clean(value).replace(",", "")
    if not text:
        return Decimal("0")
    try:
        return Decimal(text)
    except InvalidOperation:
        return Decimal("0")


def contract_amount(row: dict[str, str]) -> Decimal:
    for field in ("GCYSZJ", "D_SCBSJS_QYHTJ", "D_SCBSJS_JSJE", "f_HTJK", "YFK", "ZLBZJ"):
        amount = parse_amount(row.get(field))
        if amount:
            return amount
    return Decimal("0")


Contract = env["construction.contract"].sudo()  # noqa: F821
ContractEvent = env["sc.contract.event"].sudo()  # noqa: F821
raw_rows = read_csv(RAW_CSV)
legacy_visible_rows = [row for row in raw_rows if clean(row.get("Id")) and is_legacy_income_visible(row)]
legacy_visible_ids = {clean(row.get("Id")) for row in legacy_visible_rows}

action = env.ref("smart_construction_core.action_construction_contract_income", raise_if_not_found=False)  # noqa: F821
action_domain = action.domain if action else "[]"
action_count = Contract.search_count(eval(action_domain)) if action else None
legacy_visible_count = Contract.search_count(
    [
        ("type", "=", "out"),
        ("legacy_document_no", "ilike", "WBHTGL%"),
        ("legacy_income_surface_visible", "=", True),
    ]
)
legacy_visible_records = Contract.search(
    [
        ("type", "=", "out"),
        ("legacy_document_no", "ilike", "WBHTGL%"),
        ("legacy_income_surface_visible", "=", True),
    ]
)
legacy_raw_amount_sum = round(float(sum(contract_amount(row) for row in legacy_visible_rows)), 2)
legacy_visible_amount_sum = round(sum(legacy_visible_records.mapped("amount_untaxed")), 2)
legacy_amount_field_sum = round(sum(legacy_visible_records.mapped("legacy_contract_amount")), 2)
user_visible_amount_sum = round(sum(legacy_visible_records.mapped("visible_contract_amount")), 2)
amount_delta_count = len(legacy_visible_records.filtered(lambda rec: round(rec.legacy_contract_amount_delta or 0.0, 2) != 0.0))
amount_difference_event_count = ContractEvent.search_count(
    [
        ("legacy_fact_model", "=", "T_ProjectContract_Out"),
        ("legacy_fact_type", "=", "construction_contract_amount_reconciliation"),
        ("contract_id", "in", legacy_visible_records.ids),
    ]
)
raw_by_id = {clean(row.get("Id")): row for row in legacy_visible_rows}
positive_amount_without_line_count = sum(
    1 for rec in legacy_visible_records if not rec.line_ids and contract_amount(raw_by_id.get(rec.legacy_contract_id or "", {})) > 0
)
hidden_legacy_count = Contract.search_count(
    [
        ("legacy_document_no", "ilike", "WBHTGL%"),
        ("legacy_income_surface_visible", "=", False),
    ]
)
all_wbhtgl_count = Contract.search_count([("legacy_document_no", "ilike", "WBHTGL%")])

post_errors = []
if len(legacy_visible_ids) != EXPECTED_TARGET_ROWS:
    post_errors.append(
        {
            "error": "raw_legacy_visible_count_not_expected",
            "actual": len(legacy_visible_ids),
            "expected": EXPECTED_TARGET_ROWS,
        }
    )
if legacy_visible_count != EXPECTED_TARGET_ROWS:
    post_errors.append(
        {
            "error": "db_legacy_visible_count_not_expected",
            "actual": legacy_visible_count,
            "expected": EXPECTED_TARGET_ROWS,
        }
    )
if action_count != EXPECTED_TARGET_ROWS:
    post_errors.append(
        {
            "error": "income_action_count_not_expected",
            "actual": action_count,
            "expected": EXPECTED_TARGET_ROWS,
        }
    )
if positive_amount_without_line_count:
    post_errors.append(
        {
            "error": "positive_legacy_amount_without_contract_line",
            "actual": positive_amount_without_line_count,
            "expected": 0,
        }
    )
if legacy_amount_field_sum != legacy_raw_amount_sum:
    post_errors.append(
        {
            "error": "legacy_contract_amount_field_sum_not_expected",
            "actual": legacy_amount_field_sum,
            "expected": legacy_raw_amount_sum,
        }
    )
if user_visible_amount_sum != legacy_raw_amount_sum:
    post_errors.append(
        {
            "error": "visible_contract_amount_sum_not_expected",
            "actual": user_visible_amount_sum,
            "expected": legacy_raw_amount_sum,
        }
    )
if amount_difference_event_count != amount_delta_count:
    post_errors.append(
        {
            "error": "amount_difference_event_count_not_expected",
            "actual": amount_difference_event_count,
            "expected": amount_delta_count,
        }
    )

status = "PASS" if not post_errors else "FAIL"
payload = {
    "status": status,
    "mode": "fresh_db_construction_contract_income_count_probe",
    "database": env.cr.dbname,  # noqa: F821
    "db_writes": 0,
    "legacy_source_table": "T_ProjectContract_Out",
    "legacy_visible_filter": "DEL<>1 AND DJZT IN ('2','1','') AND HTBT<>'' AND FBF<>''",
    "raw_legacy_visible_rows": len(legacy_visible_ids),
    "legacy_income_visible_rows": legacy_visible_count,
    "income_action_visible_rows": action_count,
    "raw_legacy_amount_sum": legacy_raw_amount_sum,
    "legacy_contract_amount_field_sum": legacy_amount_field_sum,
    "user_visible_contract_amount_sum": user_visible_amount_sum,
    "income_action_amount_sum": legacy_visible_amount_sum,
    "income_action_amount_sum_delta": round(legacy_visible_amount_sum - legacy_raw_amount_sum, 2),
    "platform_contract_amount_sum": legacy_visible_amount_sum,
    "platform_contract_amount_sum_delta": round(legacy_visible_amount_sum - legacy_raw_amount_sum, 2),
    "amount_delta_contract_count": amount_delta_count,
    "amount_difference_event_count": amount_difference_event_count,
    "positive_amount_without_line_count": positive_amount_without_line_count,
    "hidden_legacy_wbhtgl_rows": hidden_legacy_count,
    "all_legacy_wbhtgl_rows": all_wbhtgl_count,
    "post_errors": post_errors,
    "decision": "income_contract_ledger_count_verified" if status == "PASS" else "STOP_REVIEW_REQUIRED",
}
write_json(OUTPUT_JSON, payload)
print(
    "FRESH_DB_CONSTRUCTION_CONTRACT_INCOME_COUNT_PROBE="
    + json.dumps(
        {
            "status": status,
            "raw_legacy_visible_rows": len(legacy_visible_ids),
            "legacy_income_visible_rows": legacy_visible_count,
            "income_action_visible_rows": action_count,
            "income_action_amount_sum": legacy_visible_amount_sum,
            "user_visible_contract_amount_sum": user_visible_amount_sum,
            "amount_difference_event_count": amount_difference_event_count,
            "positive_amount_without_line_count": positive_amount_without_line_count,
            "db_writes": 0,
        },
        ensure_ascii=False,
        sort_keys=True,
    )
)
if status != "PASS":
    raise RuntimeError({"income_count_probe_failed": post_errors})
