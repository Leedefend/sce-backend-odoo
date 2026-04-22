#!/usr/bin/env python3
from __future__ import annotations

import csv
import json
from collections import Counter, defaultdict
from pathlib import Path


INPUT_CSV = Path("artifacts/migration/partner_l4_nodb_refresh_rows_v1.csv")
OUTPUT_JSON = Path("artifacts/migration/partner_l4_remaining190_blocked_screen_result_v1.json")
OUTPUT_CSV = Path("artifacts/migration/partner_l4_remaining190_blocked_screen_rows_v1.csv")
SAMPLE_CSV = Path("artifacts/migration/partner_l4_remaining190_blocked_screen_samples_v1.csv")
EXPECTED_BLOCKED_ROWS = 190


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


def blockers(row: dict[str, str]) -> set[str]:
    return {clean(item) for item in clean(row.get("blockers")).split(";") if clean(item)}


def classify(row: dict[str, str]) -> str:
    current = blockers(row)
    if "unsafe_partner_name" in current:
        return "residual_unsafe_name_manual_screen"
    if "same_tax_multiple_names" in current and "non_primary_partner_source" in current:
        return "same_tax_company_supplier_conflict_screen"
    if "same_tax_multiple_names" in current:
        return "same_tax_company_duplicate_conflict_screen"
    if "missing_tax_number" in current and "non_primary_partner_source" in current:
        return "missing_tax_non_primary_screen"
    if "deduplicated_group_not_create_only" in current and "non_primary_partner_source" in current:
        return "non_primary_duplicate_group_screen"
    if "deduplicated_group_not_create_only" in current:
        return "company_duplicate_group_screen"
    return "manual_residual_screen"


def main() -> int:
    columns, rows = read_csv(INPUT_CSV)
    required = {
        "row_no",
        "legacy_partner_source",
        "legacy_partner_id",
        "partner_name",
        "tax_number",
        "dedup_key_type",
        "dedup_key",
        "sources",
        "source_row_count",
        "merge_strategy",
        "dry_run_action",
        "blockers",
    }
    missing_columns = sorted(required - set(columns))
    blocked_rows = [row for row in rows if clean(row.get("dry_run_action")) == "blocked"]
    output_rows: list[dict[str, object]] = []
    route_counts: Counter[str] = Counter()
    source_counts: Counter[str] = Counter()
    combo_counts: Counter[str] = Counter()
    samples: dict[str, list[dict[str, object]]] = defaultdict(list)
    for row in blocked_rows:
        route = classify(row)
        combo = ";".join(sorted(blockers(row)))
        route_counts[route] += 1
        source_counts[clean(row.get("legacy_partner_source"))] += 1
        combo_counts[combo] += 1
        output_row = {
            "row_no": clean(row.get("row_no")),
            "route": route,
            "blockers": clean(row.get("blockers")),
            "blocker_combo_sorted": combo,
            "legacy_partner_source": clean(row.get("legacy_partner_source")),
            "legacy_partner_id": clean(row.get("legacy_partner_id")),
            "partner_name": clean(row.get("partner_name")),
            "tax_number": clean(row.get("tax_number")),
            "dedup_key_type": clean(row.get("dedup_key_type")),
            "dedup_key": clean(row.get("dedup_key")),
            "sources": clean(row.get("sources")),
            "source_row_count": clean(row.get("source_row_count")),
            "merge_strategy": clean(row.get("merge_strategy")),
            "recommended_next_task": route,
        }
        output_rows.append(output_row)
        if len(samples[route]) < 20:
            samples[route].append(output_row)

    fieldnames = [
        "row_no",
        "route",
        "blockers",
        "blocker_combo_sorted",
        "legacy_partner_source",
        "legacy_partner_id",
        "partner_name",
        "tax_number",
        "dedup_key_type",
        "dedup_key",
        "sources",
        "source_row_count",
        "merge_strategy",
        "recommended_next_task",
    ]
    write_csv(OUTPUT_CSV, fieldnames, output_rows)
    write_csv(SAMPLE_CSV, fieldnames, [sample for route in sorted(samples) for sample in samples[route]])
    result = {
        "status": "PASS" if not missing_columns and len(output_rows) == EXPECTED_BLOCKED_ROWS else "FAIL",
        "mode": "partner_l4_remaining190_blocked_screen",
        "input": str(INPUT_CSV),
        "blocked_rows": len(output_rows),
        "expected_blocked_rows": EXPECTED_BLOCKED_ROWS,
        "missing_columns": missing_columns,
        "route_counts": dict(sorted(route_counts.items())),
        "source_counts": dict(sorted(source_counts.items())),
        "top_blocker_combos": dict(combo_counts.most_common(20)),
        "outputs": {"screen_rows": str(OUTPUT_CSV), "sample_rows": str(SAMPLE_CSV)},
        "next_gate": "Open same-tax conflict no-DB screen; no DB write is authorized.",
    }
    OUTPUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_JSON.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("PARTNER_REMAINING190_BLOCKED_SCREEN=" + json.dumps({
        "status": result["status"],
        "blocked_rows": result["blocked_rows"],
        "route_counts": result["route_counts"],
    }, ensure_ascii=False, sort_keys=True))
    return 0 if result["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
