#!/usr/bin/env python3
from __future__ import annotations

import csv
import json
from collections import Counter, defaultdict
from pathlib import Path


INPUT_CSV = Path("artifacts/migration/partner_l4_remaining365_blocked_screen_rows_v1.csv")
OUTPUT_JSON = Path("artifacts/migration/partner_l4_missing_tax_duplicate_group_dry_run_result_v1.json")
OUTPUT_CSV = Path("artifacts/migration/partner_l4_missing_tax_duplicate_group_dry_run_rows_v1.csv")
SAMPLE_CSV = Path("artifacts/migration/partner_l4_missing_tax_duplicate_group_dry_run_samples_v1.csv")
EXPECTED_ROUTE_ROWS = 175


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


def classify(row: dict[str, str]) -> tuple[str, str]:
    blockers = {clean(item) for item in clean(row.get("blockers")).split(";") if clean(item)}
    if "unsafe_partner_name" in blockers or "same_tax_multiple_names" in blockers:
        return ("blocked_conflict_residual", "unsafe_or_same_tax_conflict")
    if clean(row.get("sources")) == "company":
        return ("missing_tax_company_duplicate_group_review", "company_duplicate_exact_name_without_tax")
    if clean(row.get("sources")) == "company;supplier":
        return ("missing_tax_company_supplier_duplicate_group_review", "company_supplier_duplicate_exact_name_without_tax")
    return ("missing_tax_duplicate_manual_review", "unexpected_source_mix")


def main() -> int:
    columns, rows = read_csv(INPUT_CSV)
    required_columns = {
        "row_no",
        "route",
        "blockers",
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
    route_rows = [
        row for row in rows
        if clean(row.get("route")) == "missing_tax_duplicate_group_screen"
    ]

    output_rows: list[dict[str, object]] = []
    decision_counts: Counter[str] = Counter()
    reason_counts: Counter[str] = Counter()
    samples: dict[str, list[dict[str, object]]] = defaultdict(list)
    for row in route_rows:
        decision, reason = classify(row)
        decision_counts[decision] += 1
        reason_counts[reason] += 1
        output_row = {
            "row_no": clean(row.get("row_no")),
            "dry_run_decision": decision,
            "dry_run_reason": reason,
            "proposed_action": "create_merged_partner_without_tax_number" if decision.endswith("_review") else "manual_review",
            "legacy_partner_source": clean(row.get("legacy_partner_source")),
            "legacy_partner_id": clean(row.get("legacy_partner_id")),
            "partner_name": clean(row.get("partner_name")),
            "tax_number": clean(row.get("tax_number")),
            "dedup_key_type": clean(row.get("dedup_key_type")),
            "dedup_key": clean(row.get("dedup_key")),
            "sources": clean(row.get("sources")),
            "source_row_count": clean(row.get("source_row_count")),
            "merge_strategy": clean(row.get("merge_strategy")),
            "blockers": clean(row.get("blockers")),
            "recommended_next_task": decision,
        }
        output_rows.append(output_row)
        if len(samples[decision]) < 20:
            samples[decision].append(output_row)

    fieldnames = [
        "row_no",
        "dry_run_decision",
        "dry_run_reason",
        "proposed_action",
        "legacy_partner_source",
        "legacy_partner_id",
        "partner_name",
        "tax_number",
        "dedup_key_type",
        "dedup_key",
        "sources",
        "source_row_count",
        "merge_strategy",
        "blockers",
        "recommended_next_task",
    ]
    write_csv(OUTPUT_CSV, fieldnames, output_rows)
    write_csv(SAMPLE_CSV, fieldnames, [sample for decision in sorted(samples) for sample in samples[decision]])

    result = {
        "status": "PASS" if not missing_columns and len(output_rows) == EXPECTED_ROUTE_ROWS else "FAIL",
        "mode": "partner_l4_missing_tax_duplicate_group_dry_run",
        "input": str(INPUT_CSV),
        "route_rows": len(output_rows),
        "expected_route_rows": EXPECTED_ROUTE_ROWS,
        "missing_columns": missing_columns,
        "decision_counts": dict(sorted(decision_counts.items())),
        "reason_counts": dict(sorted(reason_counts.items())),
        "outputs": {
            "dry_run_rows": str(OUTPUT_CSV),
            "sample_rows": str(SAMPLE_CSV),
        },
        "next_gate": "Open no-DB write design for deterministic review rows; no DB write is authorized.",
    }
    OUTPUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_JSON.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("PARTNER_MISSING_TAX_DUPLICATE_GROUP_DRY_RUN=" + json.dumps({
        "status": result["status"],
        "route_rows": result["route_rows"],
        "decision_counts": result["decision_counts"],
    }, ensure_ascii=False, sort_keys=True))
    return 0 if result["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
