#!/usr/bin/env python3
from __future__ import annotations

import csv
import json
from collections import Counter
from pathlib import Path


INPUT_CSV = Path("artifacts/migration/partner_l4_same_tax_company_supplier_conflict_screen_rows_v1.csv")
OUTPUT_JSON = Path("artifacts/migration/partner_l4_same_tax_company_supplier_canonical_write_design_result_v1.json")
OUTPUT_CSV = Path("artifacts/migration/partner_l4_same_tax_company_supplier_canonical_write_design_rows_v1.csv")
EXPECTED_ROWS = 102


def clean(value: object) -> str:
    return "" if value is None else str(value).strip()


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
    required = {
        "row_no",
        "decision",
        "legacy_partner_source",
        "legacy_partner_id",
        "partner_name",
        "tax_number",
        "normalized_tax_number",
        "dedup_key_type",
        "dedup_key",
        "sources",
        "source_row_count",
        "merge_strategy",
    }
    missing_columns = sorted(required - set(columns))
    candidate_rows = [
        row for row in rows
        if clean(row.get("decision")) == "same_tax_company_supplier_canonical_merge_review"
    ]
    design_rows = []
    action_counts: Counter[str] = Counter()
    for row in candidate_rows:
        action = "create_company_supplier_partner_with_canonical_tax_number"
        action_counts[action] += 1
        design_rows.append({
            "write_design_id": f"partner_l4_same_tax_company_supplier_canonical_{len(design_rows) + 1:04d}",
            "proposed_action": action,
            "legacy_partner_source": "company_supplier",
            "legacy_partner_id": clean(row.get("legacy_partner_id")),
            "partner_name": clean(row.get("partner_name")),
            "legacy_credit_code": clean(row.get("normalized_tax_number")),
            "legacy_tax_no": clean(row.get("tax_number")),
            "dedup_key_type": clean(row.get("dedup_key_type")),
            "dedup_key": clean(row.get("dedup_key")),
            "sources": clean(row.get("sources")),
            "source_row_count": clean(row.get("source_row_count")),
            "merge_strategy": clean(row.get("merge_strategy")),
            "customer_flag": "true",
            "supplier_flag": "true",
            "rollback_key_source": "company_supplier",
            "rollback_key_legacy_id": clean(row.get("legacy_partner_id")),
            "source_screen_row_no": clean(row.get("row_no")),
            "db_write": "false",
        })

    fieldnames = [
        "write_design_id",
        "proposed_action",
        "legacy_partner_source",
        "legacy_partner_id",
        "partner_name",
        "legacy_credit_code",
        "legacy_tax_no",
        "dedup_key_type",
        "dedup_key",
        "sources",
        "source_row_count",
        "merge_strategy",
        "customer_flag",
        "supplier_flag",
        "rollback_key_source",
        "rollback_key_legacy_id",
        "source_screen_row_no",
        "db_write",
    ]
    write_csv(OUTPUT_CSV, fieldnames, design_rows)
    result = {
        "status": "PASS" if not missing_columns and len(design_rows) == EXPECTED_ROWS else "FAIL",
        "mode": "partner_l4_same_tax_company_supplier_canonical_write_design",
        "input": str(INPUT_CSV),
        "write_design_rows": len(design_rows),
        "expected_rows": EXPECTED_ROWS,
        "missing_columns": missing_columns,
        "action_counts": dict(sorted(action_counts.items())),
        "outputs": {"write_design_rows": str(OUTPUT_CSV)},
        "next_gate": "High-risk DB write requires bounded create-only execution with rollback targets.",
    }
    OUTPUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_JSON.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("PARTNER_SAME_TAX_COMPANY_SUPPLIER_CANONICAL_WRITE_DESIGN=" + json.dumps({
        "status": result["status"],
        "write_design_rows": result["write_design_rows"],
        "action_counts": result["action_counts"],
    }, ensure_ascii=False, sort_keys=True))
    return 0 if result["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
