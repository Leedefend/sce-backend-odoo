#!/usr/bin/env python3
"""Build host-side evidence for expense contract subtype taxonomy."""

from __future__ import annotations

import csv
import json
import os
from collections import Counter
from pathlib import Path


ROOT_DIR = Path(os.getenv("ROOT_DIR", Path.cwd()))
ARTIFACT_ROOT = Path(os.getenv("MIGRATION_ARTIFACT_ROOT", ROOT_DIR / "artifacts/migration/business_fact_upgrade"))
OUTPUT_JSON = ARTIFACT_ROOT / "business_expense_contract_subtype_evidence_v1.json"
OUTPUT_REPORT = ARTIFACT_ROOT / "business_expense_contract_subtype_evidence_v1.md"

SUPPLIER_CONTRACT_CSV = ROOT_DIR / "artifacts/migration/fresh_db_supplier_contract_replay_payload_v1.csv"
SUPPLIER_LINE_CSV = ROOT_DIR / "artifacts/migration/fresh_db_supplier_contract_line_replay_payload_v1.csv"
SUPPLIER_PRICING_CSV = ROOT_DIR / "artifacts/migration/fresh_db_legacy_supplier_contract_pricing_replay_payload_v1.csv"
LEGACY_PURCHASE_CSV = ROOT_DIR / "artifacts/migration/fresh_db_legacy_purchase_contract_replay_payload_v1.csv"
SUPPLIER_ASSET_XML = ROOT_DIR / "migration_assets/20_business/supplier_contract/supplier_contract_header_v1.xml"


def read_csv(path: Path) -> tuple[list[str], list[dict[str, str]]]:
    if not path.exists():
        return [], []
    with path.open(newline="", encoding="utf-8-sig") as handle:
        reader = csv.DictReader(handle)
        return list(reader.fieldnames or []), list(reader)


def count_column(rows: list[dict[str, str]], column: str) -> dict[str, int]:
    return dict(Counter((row.get(column) or "").strip() for row in rows))


def keyword_count(rows: list[dict[str, str]], keywords: list[str]) -> int:
    count = 0
    for row in rows:
        text = " ".join(str(value or "") for value in row.values())
        if any(keyword in text for keyword in keywords):
            count += 1
    return count


supplier_fields, supplier_rows = read_csv(SUPPLIER_CONTRACT_CSV)
line_fields, line_rows = read_csv(SUPPLIER_LINE_CSV)
pricing_fields, pricing_rows = read_csv(SUPPLIER_PRICING_CSV)
purchase_fields, purchase_rows = read_csv(LEGACY_PURCHASE_CSV)

supplier_subject_counts = count_column(supplier_rows, "subject")
supplier_type_counts = count_column(supplier_rows, "type")
purchase_contract_type_counts = count_column(purchase_rows, "contract_type")
pricing_method_counts = count_column(pricing_rows, "pricing_method_text")

expected_supplier_subjects = {
    "材料合同",
    "正常合同",
    "劳务合同",
    "租赁合同",
    "分包合同",
    "其他合同",
    "补充合同",
}
actual_supplier_subjects = set(supplier_subject_counts)
unknown_subjects = sorted(actual_supplier_subjects - expected_supplier_subjects)
missing_expected_subjects = sorted(expected_supplier_subjects - actual_supplier_subjects)

decisions = [
    {
        "key": "expense_contract_subtypes_follow_supplier_contract_subject",
        "decision": "use_supplier_subject_as_authoritative_contract_subtype",
        "reason": "Supplier contract replay carries explicit subject values from the migration asset.",
    },
    {
        "key": "expense_is_not_supplier_contract_subtype",
        "decision": "keep_expense_reimbursement_and_deposit_in_expense_fact_lanes",
        "reason": "No supplier contract subject equals fee or reimbursement; expense/deposit facts already have separate carriers.",
    },
    {
        "key": "subcontract_and_rental_are_contract_subtypes_when_subject_matches",
        "decision": "expose_filtered_expense_contract_views_for_subcontract_and_rental",
        "reason": "The supplier contract subject distribution includes 分包合同 and 租赁合同.",
    },
    {
        "key": "pricing_method_is_not_contract_subtype",
        "decision": "keep_supplier_pricing_method_as_pricing_fact",
        "reason": "Pricing methods describe payment/pricing behavior, not contract family.",
    },
    {
        "key": "legacy_purchase_general_contracts_are_separate_general_expense_contract_facts",
        "decision": "keep_legacy_purchase_general_contract_fact_lane",
        "reason": "Legacy purchase/general payload has its own contract_type distribution.",
    },
]

errors = []
if not supplier_rows:
    errors.append({"error": "missing_supplier_contract_payload", "path": str(SUPPLIER_CONTRACT_CSV)})
if not SUPPLIER_ASSET_XML.exists():
    errors.append({"error": "missing_supplier_contract_asset_xml", "path": str(SUPPLIER_ASSET_XML)})
if unknown_subjects:
    errors.append({"error": "unknown_supplier_subjects", "values": unknown_subjects})
if missing_expected_subjects:
    errors.append({"error": "missing_expected_supplier_subjects", "values": missing_expected_subjects})

status = "PASS" if not errors else "FAIL"
payload = {
    "status": status,
    "mode": "business_expense_contract_subtype_evidence",
    "summary": {
        "supplier_contract_payload": {
            "path": str(SUPPLIER_CONTRACT_CSV),
            "row_count": len(supplier_rows),
            "fields": supplier_fields,
            "subject_counts": supplier_subject_counts,
            "type_counts": supplier_type_counts,
            "subject_is_contract_subtype": True,
            "asset_xml_path": str(SUPPLIER_ASSET_XML),
        },
        "supplier_contract_line_payload": {
            "path": str(SUPPLIER_LINE_CSV),
            "row_count": len(line_rows),
            "fields": line_fields,
            "contract_subtype_fields": [],
        },
        "supplier_pricing_payload": {
            "path": str(SUPPLIER_PRICING_CSV),
            "row_count": len(pricing_rows),
            "fields": pricing_fields,
            "pricing_method_counts": pricing_method_counts,
            "contract_subtype": False,
        },
        "legacy_purchase_general_contract_payload": {
            "path": str(LEGACY_PURCHASE_CSV),
            "row_count": len(purchase_rows),
            "fields": purchase_fields,
            "contract_type_counts": purchase_contract_type_counts,
            "expense_service_candidate_keyword_count": keyword_count(
                purchase_rows,
                ["服务", "咨询", "培训", "软件", "法律", "税务", "审计", "认证", "资质", "证书", "费用"],
            ),
        },
        "recommended_user_facing_expense_contract_subjects": [
            "材料合同",
            "正常合同",
            "劳务合同",
            "租赁合同",
            "分包合同",
            "其他合同",
            "补充合同",
        ],
    },
    "decisions": decisions,
    "errors": errors,
    "decision": "expense_contract_subtype_evidence_ready" if status == "PASS" else "STOP_REVIEW_REQUIRED",
}

OUTPUT_JSON.parent.mkdir(parents=True, exist_ok=True)
OUTPUT_JSON.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

report = f"""# Business Expense Contract Subtype Evidence v1

Status: {status}

## Supplier Contract Subjects

```json
{json.dumps(supplier_subject_counts, ensure_ascii=False, indent=2)}
```

## Legacy Purchase / General Contract Types

```json
{json.dumps(purchase_contract_type_counts, ensure_ascii=False, indent=2)}
```

## Decisions

```json
{json.dumps(decisions, ensure_ascii=False, indent=2)}
```

## Errors

```json
{json.dumps(errors, ensure_ascii=False, indent=2)}
```

## Decision

`{payload["decision"]}`
"""
OUTPUT_REPORT.write_text(report, encoding="utf-8")

print(
    "BUSINESS_EXPENSE_CONTRACT_SUBTYPE_EVIDENCE="
    + json.dumps(
        {
            "status": status,
            "supplier_contracts": len(supplier_rows),
            "supplier_subject_counts": supplier_subject_counts,
            "legacy_purchase_contracts": len(purchase_rows),
            "artifact_root": str(ARTIFACT_ROOT),
        },
        ensure_ascii=False,
        sort_keys=True,
    )
)
