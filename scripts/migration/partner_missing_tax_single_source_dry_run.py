#!/usr/bin/env python3
from __future__ import annotations

import csv
import json
from collections import Counter
from pathlib import Path


INPUT_CSV = Path("artifacts/migration/partner_l4_missing_tax_screen_rows_v1.csv")
OUTPUT_JSON = Path("artifacts/migration/partner_l4_missing_tax_single_source_dry_run_result_v1.json")
OUTPUT_CSV = Path("artifacts/migration/partner_l4_missing_tax_single_source_dry_run_rows_v1.csv")
SAMPLE_CSV = Path("artifacts/migration/partner_l4_missing_tax_single_source_dry_run_samples_v1.csv")
EXPECTED_CANDIDATE_ROWS = 1554


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


def evidence_grade(row: dict[str, str]) -> str:
    if (
        clean(row.get("subroute")) == "missing_tax_single_source_create_review"
        and clean(row.get("blockers")) == "missing_tax_number"
        and clean(row.get("legacy_partner_source")) == "cooperat_company"
        and clean(row.get("sources")) == "company"
        and clean(row.get("source_row_count")) == "1"
        and not clean(row.get("tax_number"))
    ):
        return "single_source_company_missing_tax_only"
    return "blocked_by_evidence_mismatch"


def main() -> int:
    columns, rows = read_csv(INPUT_CSV)
    required_columns = {
        "row_no",
        "subroute",
        "blockers",
        "legacy_partner_source",
        "legacy_partner_id",
        "partner_name",
        "tax_number",
        "sources",
        "source_row_count",
    }
    missing_columns = sorted(required_columns - set(columns))
    route_rows = [
        row
        for row in rows
        if clean(row.get("subroute")) == "missing_tax_single_source_create_review"
    ]
    grade_counts: Counter[str] = Counter()
    source_counts: Counter[str] = Counter()
    output_rows: list[dict[str, object]] = []

    for row in route_rows:
        grade = evidence_grade(row)
        grade_counts[grade] += 1
        source_counts[clean(row.get("sources"))] += 1
        proposed_action = (
            "create_company_partner_without_tax_number_review"
            if grade == "single_source_company_missing_tax_only"
            else "manual_evidence_review"
        )
        output_rows.append(
            {
                "row_no": clean(row.get("row_no")),
                "evidence_grade": grade,
                "proposed_action": proposed_action,
                "legacy_partner_source": clean(row.get("legacy_partner_source")),
                "legacy_partner_id": clean(row.get("legacy_partner_id")),
                "partner_name": clean(row.get("partner_name")),
                "tax_number": clean(row.get("tax_number")),
                "sources": clean(row.get("sources")),
                "source_row_count": clean(row.get("source_row_count")),
                "blockers": clean(row.get("blockers")),
                "future_rollback_key": clean(row.get("legacy_partner_source")) + ":" + clean(row.get("legacy_partner_id")),
            }
        )

    fieldnames = [
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
    ]
    write_csv(OUTPUT_CSV, fieldnames, output_rows)
    write_csv(SAMPLE_CSV, fieldnames, output_rows[:50])

    candidate_rows = grade_counts["single_source_company_missing_tax_only"]
    blocked_rows = sum(count for grade, count in grade_counts.items() if grade != "single_source_company_missing_tax_only")
    result = {
        "status": "PASS" if not missing_columns and len(route_rows) == EXPECTED_CANDIDATE_ROWS and blocked_rows == 0 else "FAIL",
        "mode": "partner_l4_missing_tax_single_source_dry_run",
        "input": str(INPUT_CSV),
        "route_rows": len(route_rows),
        "candidate_rows": candidate_rows,
        "blocked_rows": blocked_rows,
        "missing_columns": missing_columns,
        "evidence_grade_counts": dict(sorted(grade_counts.items())),
        "source_counts": dict(sorted(source_counts.items())),
        "proposed_action": "create_company_partner_without_tax_number_review",
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
        ],
        "outputs": {
            "dry_run_rows": str(OUTPUT_CSV),
            "sample_rows": str(SAMPLE_CSV),
        },
        "next_gate": "Open a no-DB write-design task before any missing-tax bounded write is considered.",
    }
    OUTPUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_JSON.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("PARTNER_MISSING_TAX_SINGLE_SOURCE_DRY_RUN=" + json.dumps({
        "status": result["status"],
        "route_rows": result["route_rows"],
        "candidate_rows": result["candidate_rows"],
        "blocked_rows": result["blocked_rows"],
        "proposed_action": result["proposed_action"],
    }, ensure_ascii=False, sort_keys=True))
    return 0 if result["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
