#!/usr/bin/env python3
from __future__ import annotations

import csv
import json
from collections import Counter
from pathlib import Path


INPUT_CSV = Path("artifacts/migration/partner_l4_missing_tax_duplicate_group_dry_run_rows_v1.csv")
OUTPUT_JSON = Path("artifacts/migration/partner_l4_missing_tax_duplicate_group_write_design_result_v1.json")
OUTPUT_CSV = Path("artifacts/migration/partner_l4_missing_tax_duplicate_group_write_design_rows_v1.csv")
EXPECTED_ROWS = 175


def clean(value: object) -> str:
    return "" if value is None else str(value).strip()


def legacy_source_carrier(value: object) -> str:
    text = clean(value)
    return "company_supplier" if text == "company;supplier" else text


def read_csv(path: Path) -> tuple[list[str], list[dict[str, str]]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        return list(reader.fieldnames or []), [dict(row) for row in reader]


def write_csv(path: Path, fieldnames: list[str], rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def main() -> int:
    columns, rows = read_csv(INPUT_CSV)
    required_columns = {
        "row_no",
        "dry_run_decision",
        "legacy_partner_source",
        "legacy_partner_id",
        "partner_name",
        "tax_number",
        "dedup_key_type",
        "dedup_key",
        "sources",
        "source_row_count",
        "merge_strategy",
    }
    missing_columns = sorted(required_columns - set(columns))
    design_rows = []
    action_counts: Counter[str] = Counter()
    for row in rows:
        decision = clean(row.get("dry_run_decision"))
        action = "create_merged_partner_without_tax_number"
        if decision not in {
            "missing_tax_company_duplicate_group_review",
            "missing_tax_company_supplier_duplicate_group_review",
        }:
            action = "manual_review"
        action_counts[action] += 1
        legacy_source = legacy_source_carrier(row.get("legacy_partner_source"))
        design_rows.append({
            "write_design_id": f"partner_l4_missing_tax_duplicate_group_{len(design_rows) + 1:04d}",
            "proposed_action": action,
            "legacy_partner_source": legacy_source,
            "legacy_partner_id": clean(row.get("legacy_partner_id")),
            "partner_name": clean(row.get("partner_name")),
            "tax_number": "",
            "tax_number_policy": "allowed_blank_by_user_policy",
            "dedup_key_type": clean(row.get("dedup_key_type")),
            "dedup_key": clean(row.get("dedup_key")),
            "sources": clean(row.get("sources")),
            "source_row_count": clean(row.get("source_row_count")),
            "merge_strategy": clean(row.get("merge_strategy")),
            "customer_flag": "true",
            "supplier_flag": "true" if "supplier" in clean(row.get("sources")).split(";") else "false",
            "rollback_key_source": legacy_source,
            "rollback_key_legacy_id": clean(row.get("legacy_partner_id")),
            "source_dry_run_row_no": clean(row.get("row_no")),
            "db_write": "false",
        })

    fieldnames = [
        "write_design_id",
        "proposed_action",
        "legacy_partner_source",
        "legacy_partner_id",
        "partner_name",
        "tax_number",
        "tax_number_policy",
        "dedup_key_type",
        "dedup_key",
        "sources",
        "source_row_count",
        "merge_strategy",
        "customer_flag",
        "supplier_flag",
        "rollback_key_source",
        "rollback_key_legacy_id",
        "source_dry_run_row_no",
        "db_write",
    ]
    write_csv(OUTPUT_CSV, fieldnames, design_rows)
    result = {
        "status": "PASS" if not missing_columns and len(design_rows) == EXPECTED_ROWS and action_counts.get("manual_review", 0) == 0 else "FAIL",
        "mode": "partner_l4_missing_tax_duplicate_group_write_design",
        "input": str(INPUT_CSV),
        "write_design_rows": len(design_rows),
        "expected_rows": EXPECTED_ROWS,
        "missing_columns": missing_columns,
        "action_counts": dict(sorted(action_counts.items())),
        "outputs": {"write_design_rows": str(OUTPUT_CSV)},
        "next_gate": "STOP before high-risk DB write; explicit authorization is required.",
    }
    OUTPUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_JSON.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("PARTNER_MISSING_TAX_DUPLICATE_GROUP_WRITE_DESIGN=" + json.dumps({
        "status": result["status"],
        "write_design_rows": result["write_design_rows"],
        "action_counts": result["action_counts"],
    }, ensure_ascii=False, sort_keys=True))
    return 0 if result["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
