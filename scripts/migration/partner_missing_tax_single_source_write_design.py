#!/usr/bin/env python3
from __future__ import annotations

import csv
import json
from collections import Counter
from pathlib import Path


INPUT_CSV = Path("artifacts/migration/partner_l4_missing_tax_single_source_dry_run_rows_v1.csv")
OUTPUT_JSON = Path("artifacts/migration/partner_l4_missing_tax_single_source_write_design_result_v1.json")
OUTPUT_CSV = Path("artifacts/migration/partner_l4_missing_tax_single_source_write_design_rows_v1.csv")
SAMPLE_CSV = Path("artifacts/migration/partner_l4_missing_tax_single_source_write_design_samples_v1.csv")
EXPECTED_DESIGN_ROWS = 1554


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
        "proposed_action",
        "legacy_partner_source",
        "legacy_partner_id",
        "partner_name",
        "tax_number",
        "sources",
        "source_row_count",
        "blockers",
        "future_rollback_key",
    }
    missing_columns = sorted(required_columns - set(columns))
    grade_counts: Counter[str] = Counter()
    action_counts: Counter[str] = Counter()
    blocked_rows = 0
    output_rows: list[dict[str, object]] = []

    for row in rows:
        grade = clean(row.get("evidence_grade"))
        original_action = clean(row.get("proposed_action"))
        is_designable = (
            grade == "single_source_company_missing_tax_only"
            and original_action == "create_company_partner_without_tax_number_review"
            and clean(row.get("legacy_partner_source")) == "cooperat_company"
            and clean(row.get("sources")) == "company"
            and clean(row.get("source_row_count")) == "1"
            and clean(row.get("blockers")) == "missing_tax_number"
            and not clean(row.get("tax_number"))
        )
        proposed_action = "create_company_partner_without_tax_number" if is_designable else "manual_evidence_review"
        if not is_designable:
            blocked_rows += 1
        grade_counts[grade] += 1
        action_counts[proposed_action] += 1
        output_rows.append(
            {
                "row_no": clean(row.get("row_no")),
                "proposed_action": proposed_action,
                "target_model": "res.partner",
                "target_company_type": "company",
                "target_customer_rank": "1",
                "target_supplier_rank": "0",
                "target_tax_number_policy": "leave_blank",
                "legacy_partner_source": clean(row.get("legacy_partner_source")),
                "legacy_partner_id": clean(row.get("legacy_partner_id")),
                "legacy_partner_name": clean(row.get("partner_name")),
                "legacy_source_evidence": "partner_l4_missing_tax_single_source_dry_run_v1",
                "future_rollback_key": clean(row.get("future_rollback_key")),
                "design_blocker": "" if is_designable else "evidence_mismatch",
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

    design_rows = action_counts["create_company_partner_without_tax_number"]
    result = {
        "status": "PASS" if not missing_columns and len(rows) == EXPECTED_DESIGN_ROWS and blocked_rows == 0 else "FAIL",
        "mode": "partner_l4_missing_tax_single_source_write_design",
        "input": str(INPUT_CSV),
        "input_rows": len(rows),
        "write_design_rows": design_rows,
        "blocked_rows": blocked_rows,
        "missing_columns": missing_columns,
        "evidence_grade_counts": dict(sorted(grade_counts.items())),
        "proposed_action_counts": dict(sorted(action_counts.items())),
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
        "next_gate": "STOP before high-risk DB write; explicit authorization is required for the 1554-row missing-tax bounded write.",
    }
    OUTPUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_JSON.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("PARTNER_MISSING_TAX_SINGLE_SOURCE_WRITE_DESIGN=" + json.dumps({
        "status": result["status"],
        "input_rows": result["input_rows"],
        "write_design_rows": result["write_design_rows"],
        "blocked_rows": result["blocked_rows"],
    }, ensure_ascii=False, sort_keys=True))
    return 0 if result["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
