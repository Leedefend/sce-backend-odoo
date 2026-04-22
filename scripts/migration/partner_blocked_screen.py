#!/usr/bin/env python3
from __future__ import annotations

import csv
import json
from collections import Counter, defaultdict
from pathlib import Path


INPUT_CSV = Path("artifacts/migration/partner_l4_nodb_refresh_rows_v1.csv")
OUTPUT_JSON = Path("artifacts/migration/partner_l4_blocked_screen_result_v1.json")
OUTPUT_CSV = Path("artifacts/migration/partner_l4_blocked_screen_rows_v1.csv")
SAMPLE_CSV = Path("artifacts/migration/partner_l4_blocked_screen_samples_v1.csv")
EXPECTED_DEDUPED_ROWS = 7172


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


def route_for(blockers: set[str]) -> str:
    if "same_tax_multiple_names" in blockers:
        return "manual_conflict_screen"
    if "deduplicated_group_not_create_only" in blockers:
        return "merge_identity_screen"
    if "non_primary_partner_source" in blockers:
        return "supplier_or_non_primary_screen"
    if "missing_tax_number" in blockers:
        return "missing_tax_screen"
    if "unsafe_partner_name" in blockers:
        return "unsafe_name_screen"
    return "blocked_misc_screen"


def main() -> int:
    columns, rows = read_csv(INPUT_CSV)
    required_columns = {
        "row_no",
        "legacy_partner_source",
        "legacy_partner_id",
        "partner_name",
        "tax_number",
        "sources",
        "source_row_count",
        "dry_run_action",
        "blockers",
    }
    missing_columns = sorted(required_columns - set(columns))
    blocked_rows = [row for row in rows if clean(row.get("dry_run_action")) == "blocked"]
    route_counts: Counter[str] = Counter()
    blocker_counts: Counter[str] = Counter()
    combo_counts: Counter[str] = Counter()
    route_samples: dict[str, list[dict[str, object]]] = defaultdict(list)
    screen_rows: list[dict[str, object]] = []
    for row in blocked_rows:
        blockers = {clean(item) for item in clean(row.get("blockers")).split(";") if clean(item)}
        route = route_for(blockers)
        route_counts[route] += 1
        combo = ";".join(clean(item) for item in clean(row.get("blockers")).split(";") if clean(item))
        combo_counts[combo] += 1
        for blocker in blockers:
            blocker_counts[blocker] += 1
        screen_row = {
            "row_no": clean(row.get("row_no")),
            "route": route,
            "blockers": combo,
            "legacy_partner_source": clean(row.get("legacy_partner_source")),
            "legacy_partner_id": clean(row.get("legacy_partner_id")),
            "partner_name": clean(row.get("partner_name")),
            "tax_number": clean(row.get("tax_number")),
            "sources": clean(row.get("sources")),
            "source_row_count": clean(row.get("source_row_count")),
            "recommended_next_task": route,
        }
        screen_rows.append(screen_row)
        if len(route_samples[route]) < 10:
            route_samples[route].append(screen_row)

    sample_rows = [sample for route in sorted(route_samples) for sample in route_samples[route]]
    fieldnames = [
        "row_no",
        "route",
        "blockers",
        "legacy_partner_source",
        "legacy_partner_id",
        "partner_name",
        "tax_number",
        "sources",
        "source_row_count",
        "recommended_next_task",
    ]
    write_csv(OUTPUT_CSV, fieldnames, screen_rows)
    write_csv(SAMPLE_CSV, fieldnames, sample_rows)

    route_priority = [
        "merge_identity_screen",
        "missing_tax_screen",
        "supplier_or_non_primary_screen",
        "unsafe_name_screen",
        "manual_conflict_screen",
        "blocked_misc_screen",
    ]
    result = {
        "status": "PASS" if not missing_columns and len(rows) == EXPECTED_DEDUPED_ROWS else "FAIL",
        "mode": "partner_l4_blocked_screen",
        "input": str(INPUT_CSV),
        "total_rows": len(rows),
        "blocked_rows": len(blocked_rows),
        "create_candidate_rows": sum(1 for row in rows if clean(row.get("dry_run_action")) == "create_candidate"),
        "skip_existing_validation_rows": sum(1 for row in rows if clean(row.get("dry_run_action")) == "skip_existing_validation"),
        "missing_columns": missing_columns,
        "blocker_counts": dict(sorted(blocker_counts.items())),
        "route_counts": dict(sorted(route_counts.items())),
        "top_blocker_combinations": [
            {"blockers": blockers, "rows": count}
            for blockers, count in combo_counts.most_common(20)
        ],
        "route_priority": route_priority,
        "outputs": {
            "screen_rows": str(OUTPUT_CSV),
            "sample_rows": str(SAMPLE_CSV),
        },
        "next_gate": "Open a dedicated route-specific no-DB screen before any merge/update or rule expansion write.",
    }
    OUTPUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_JSON.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("PARTNER_BLOCKED_SCREEN=" + json.dumps({
        "status": result["status"],
        "blocked_rows": result["blocked_rows"],
        "create_candidate_rows": result["create_candidate_rows"],
        "skip_existing_validation_rows": result["skip_existing_validation_rows"],
        "route_counts": result["route_counts"],
    }, ensure_ascii=False, sort_keys=True))
    return 0 if result["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
