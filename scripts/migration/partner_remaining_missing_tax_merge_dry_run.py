#!/usr/bin/env python3
from __future__ import annotations

import csv
import json
from collections import Counter
from pathlib import Path


INPUT_CSV = Path("artifacts/migration/partner_l4_remaining_missing_tax_screen_rows_v1.csv")
OUTPUT_JSON = Path("artifacts/migration/partner_l4_remaining_missing_tax_merge_dry_run_result_v1.json")
OUTPUT_CSV = Path("artifacts/migration/partner_l4_remaining_missing_tax_merge_dry_run_rows_v1.csv")
SAMPLE_CSV = Path("artifacts/migration/partner_l4_remaining_missing_tax_merge_dry_run_samples_v1.csv")
EXPECTED_ROUTE_ROWS = 827


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
        clean(row.get("blockers")) == "missing_tax_number;deduplicated_group_not_create_only;non_primary_partner_source"
        and clean(row.get("sources")) == "company;supplier"
        and clean(row.get("source_row_count")) == "2"
        and not clean(row.get("tax_number"))
    ):
        return "missing_tax_company_supplier_pair_review"
    if clean(row.get("blockers")) == "missing_tax_number;deduplicated_group_not_create_only":
        return "missing_tax_company_duplicate_review"
    return "missing_tax_complex_merge_review"


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
    route_rows = [row for row in rows if clean(row.get("subroute")) == "remaining_missing_tax_merge_identity_review"]
    grade_counts: Counter[str] = Counter()
    output_rows: list[dict[str, object]] = []
    for row in route_rows:
        grade = evidence_grade(row)
        grade_counts[grade] += 1
        output_rows.append(
            {
                "row_no": clean(row.get("row_no")),
                "evidence_grade": grade,
                "legacy_partner_source": clean(row.get("legacy_partner_source")),
                "legacy_partner_id": clean(row.get("legacy_partner_id")),
                "partner_name": clean(row.get("partner_name")),
                "tax_number": clean(row.get("tax_number")),
                "sources": clean(row.get("sources")),
                "source_row_count": clean(row.get("source_row_count")),
                "blockers": clean(row.get("blockers")),
                "recommended_next_task": grade,
            }
        )

    fieldnames = [
        "row_no",
        "evidence_grade",
        "legacy_partner_source",
        "legacy_partner_id",
        "partner_name",
        "tax_number",
        "sources",
        "source_row_count",
        "blockers",
        "recommended_next_task",
    ]
    write_csv(OUTPUT_CSV, fieldnames, output_rows)
    write_csv(SAMPLE_CSV, fieldnames, output_rows[:50])

    result = {
        "status": "PASS" if not missing_columns and len(route_rows) == EXPECTED_ROUTE_ROWS else "FAIL",
        "mode": "partner_l4_remaining_missing_tax_merge_dry_run",
        "input": str(INPUT_CSV),
        "route_rows": len(route_rows),
        "missing_columns": missing_columns,
        "evidence_grade_counts": dict(sorted(grade_counts.items())),
        "outputs": {
            "dry_run_rows": str(OUTPUT_CSV),
            "sample_rows": str(SAMPLE_CSV),
        },
        "next_gate": "Open a no-DB design for missing_tax_company_supplier_pair_review before any write.",
    }
    OUTPUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_JSON.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("PARTNER_REMAINING_MISSING_TAX_MERGE_DRY_RUN=" + json.dumps({
        "status": result["status"],
        "route_rows": result["route_rows"],
        "evidence_grade_counts": result["evidence_grade_counts"],
    }, ensure_ascii=False, sort_keys=True))
    return 0 if result["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
