#!/usr/bin/env python3
from __future__ import annotations

import csv
import json
from collections import Counter, defaultdict
from pathlib import Path


INPUT_CSV = Path("artifacts/migration/partner_l4_remaining_blocked_screen_rows_v1.csv")
OUTPUT_JSON = Path("artifacts/migration/partner_l4_remaining_unsafe_name_screen_result_v1.json")
OUTPUT_CSV = Path("artifacts/migration/partner_l4_remaining_unsafe_name_screen_rows_v1.csv")
SAMPLE_CSV = Path("artifacts/migration/partner_l4_remaining_unsafe_name_screen_samples_v1.csv")
EXPECTED_ROUTE_ROWS = 1111


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


def subroute_for(blockers: set[str]) -> str:
    if "same_tax_multiple_names" in blockers:
        return "unsafe_name_conflict_review"
    if "deduplicated_group_not_create_only" in blockers and "missing_tax_number" in blockers:
        return "unsafe_name_missing_tax_merge_review"
    if "missing_tax_number" in blockers:
        return "unsafe_name_missing_tax_single_review"
    if "deduplicated_group_not_create_only" in blockers:
        return "unsafe_name_merge_review"
    return "unsafe_name_single_review"


def main() -> int:
    columns, rows = read_csv(INPUT_CSV)
    required_columns = {"row_no", "route", "blockers", "legacy_partner_source", "legacy_partner_id", "partner_name", "tax_number", "sources", "source_row_count"}
    missing_columns = sorted(required_columns - set(columns))
    route_rows = [row for row in rows if clean(row.get("route")) == "remaining_unsafe_name_screen"]
    subroute_counts: Counter[str] = Counter()
    combo_counts: Counter[str] = Counter()
    samples: dict[str, list[dict[str, object]]] = defaultdict(list)
    output_rows: list[dict[str, object]] = []
    for row in route_rows:
        blockers = {clean(item) for item in clean(row.get("blockers")).split(";") if clean(item)}
        subroute = subroute_for(blockers)
        subroute_counts[subroute] += 1
        combo_counts[clean(row.get("blockers"))] += 1
        output_row = {
            "row_no": clean(row.get("row_no")),
            "subroute": subroute,
            "blockers": clean(row.get("blockers")),
            "legacy_partner_source": clean(row.get("legacy_partner_source")),
            "legacy_partner_id": clean(row.get("legacy_partner_id")),
            "partner_name": clean(row.get("partner_name")),
            "tax_number": clean(row.get("tax_number")),
            "sources": clean(row.get("sources")),
            "source_row_count": clean(row.get("source_row_count")),
            "recommended_next_task": subroute,
        }
        output_rows.append(output_row)
        if len(samples[subroute]) < 10:
            samples[subroute].append(output_row)

    fieldnames = ["row_no", "subroute", "blockers", "legacy_partner_source", "legacy_partner_id", "partner_name", "tax_number", "sources", "source_row_count", "recommended_next_task"]
    write_csv(OUTPUT_CSV, fieldnames, output_rows)
    write_csv(SAMPLE_CSV, fieldnames, [sample for subroute in sorted(samples) for sample in samples[subroute]])
    result = {
        "status": "PASS" if not missing_columns and len(route_rows) == EXPECTED_ROUTE_ROWS else "FAIL",
        "mode": "partner_l4_remaining_unsafe_name_screen",
        "input": str(INPUT_CSV),
        "route_rows": len(route_rows),
        "missing_columns": missing_columns,
        "subroute_counts": dict(sorted(subroute_counts.items())),
        "top_blocker_combinations": [{"blockers": blockers, "rows": count} for blockers, count in combo_counts.most_common(20)],
        "outputs": {"screen_rows": str(OUTPUT_CSV), "sample_rows": str(SAMPLE_CSV)},
        "next_gate": "Unsafe-name routes require manual/name-normalization policy before any write design.",
    }
    OUTPUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_JSON.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("PARTNER_REMAINING_UNSAFE_NAME_SCREEN=" + json.dumps({"status": result["status"], "route_rows": result["route_rows"], "subroute_counts": result["subroute_counts"]}, ensure_ascii=False, sort_keys=True))
    return 0 if result["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
