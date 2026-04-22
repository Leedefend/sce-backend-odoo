#!/usr/bin/env python3
from __future__ import annotations

import csv
import json
from collections import Counter
from pathlib import Path


INPUT_CSV = Path("artifacts/migration/partner_l4_remaining_missing_tax_merge_dry_run_rows_v1.csv")
OUTPUT_JSON = Path("artifacts/migration/partner_l4_remaining_missing_tax_company_supplier_write_design_result_v1.json")
OUTPUT_CSV = Path("artifacts/migration/partner_l4_remaining_missing_tax_company_supplier_write_design_rows_v1.csv")
SAMPLE_CSV = Path("artifacts/migration/partner_l4_remaining_missing_tax_company_supplier_write_design_samples_v1.csv")
EXPECTED_DESIGN_ROWS = 652


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
    required_columns = {
        "row_no",
        "evidence_grade",
        "legacy_partner_source",
        "legacy_partner_id",
        "partner_name",
        "tax_number",
        "sources",
        "source_row_count",
        "blockers",
    }
    missing_columns = sorted(required_columns - set(columns))
    design_source_rows = [
        row
        for row in rows
        if clean(row.get("evidence_grade")) == "missing_tax_company_supplier_pair_review"
    ]
    blocker_counts: Counter[str] = Counter()
    output_rows: list[dict[str, object]] = []

    for row in design_source_rows:
        design_blocker = ""
        if clean(row.get("sources")) != "company;supplier":
            design_blocker = "sources_not_company_supplier"
        elif clean(row.get("source_row_count")) != "2":
            design_blocker = "source_row_count_not_two"
        elif clean(row.get("tax_number")):
            design_blocker = "tax_number_present"
        if design_blocker:
            blocker_counts[design_blocker] += 1
        output_rows.append(
            {
                "row_no": clean(row.get("row_no")),
                "proposed_action": "create_company_supplier_partner_without_tax_number" if not design_blocker else "manual_evidence_review",
                "target_model": "res.partner",
                "target_company_type": "company",
                "target_customer_rank": "1",
                "target_supplier_rank": "1",
                "target_tax_number_policy": "leave_blank",
                "legacy_partner_source": "cooperat_company",
                "legacy_partner_id": clean(row.get("legacy_partner_id")),
                "legacy_partner_name": clean(row.get("partner_name")),
                "legacy_source_evidence": "partner_l4_remaining_missing_tax_company_supplier_write_design_v1",
                "future_rollback_key": "cooperat_company:" + clean(row.get("legacy_partner_id")),
                "design_blocker": design_blocker,
            }
        )

    fieldnames = [
        "row_no",
        "proposed_action",
        "target_model",
        "target_company_type",
        "target_customer_rank",
        "target_supplier_rank",
        "target_tax_number_policy",
        "legacy_partner_source",
        "legacy_partner_id",
        "legacy_partner_name",
        "legacy_source_evidence",
        "future_rollback_key",
        "design_blocker",
    ]
    write_csv(OUTPUT_CSV, fieldnames, output_rows)
    write_csv(SAMPLE_CSV, fieldnames, output_rows[:50])
    result = {
        "status": "PASS" if not missing_columns and len(output_rows) == EXPECTED_DESIGN_ROWS and not blocker_counts else "FAIL",
        "mode": "partner_l4_remaining_missing_tax_company_supplier_write_design",
        "input": str(INPUT_CSV),
        "write_design_rows": len(output_rows),
        "blocked_rows": sum(blocker_counts.values()),
        "missing_columns": missing_columns,
        "design_blocker_counts": dict(sorted(blocker_counts.items())),
        "proposed_action": "create_company_supplier_partner_without_tax_number",
        "allowed_future_fields": [
            "name",
            "company_type",
            "customer_rank",
            "supplier_rank",
            "legacy_partner_id",
            "legacy_partner_source",
            "legacy_partner_name",
            "legacy_source_evidence",
        ],
        "forbidden_actions": [
            "update_existing_partner",
            "unlink",
            "raw_sql",
            "acl_change",
            "tax_number_fabrication",
            "tax_number_backfill",
        ],
        "outputs": {
            "write_design_rows": str(OUTPUT_CSV),
            "sample_rows": str(SAMPLE_CSV),
        },
        "next_gate": "STOP before high-risk DB write; explicit authorization is required for the 652-row remaining missing-tax company/supplier bounded write.",
    }
    OUTPUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_JSON.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("PARTNER_REMAINING_MISSING_TAX_COMPANY_SUPPLIER_WRITE_DESIGN=" + json.dumps({
        "status": result["status"],
        "write_design_rows": result["write_design_rows"],
        "blocked_rows": result["blocked_rows"],
        "proposed_action": result["proposed_action"],
    }, ensure_ascii=False, sort_keys=True))
    return 0 if result["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
