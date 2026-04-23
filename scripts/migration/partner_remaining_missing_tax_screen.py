#!/usr/bin/env python3
from __future__ import annotations

import csv
import json
from collections import Counter, defaultdict
from pathlib import Path


INPUT_CSV = Path("artifacts/migration/partner_l4_nodb_refresh_rows_v1.csv")
OUTPUT_JSON = Path("artifacts/migration/partner_l4_remaining_missing_tax_screen_result_v1.json")
OUTPUT_CSV = Path("artifacts/migration/partner_l4_remaining_missing_tax_screen_rows_v1.csv")
SAMPLE_CSV = Path("artifacts/migration/partner_l4_remaining_missing_tax_screen_samples_v1.csv")
EXPECTED_MISSING_TAX_ROWS = 1760


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


def blockers_for(row: dict[str, str]) -> set[str]:
    return {clean(item) for item in clean(row.get("blockers")).split(";") if clean(item)}


def subroute_for(row: dict[str, str]) -> str:
    blockers = blockers_for(row)
    if "same_tax_multiple_names" in blockers:
        return "remaining_missing_tax_conflict_review"
    if "deduplicated_group_not_create_only" in blockers:
        if "unsafe_partner_name" in blockers:
            return "remaining_missing_tax_unsafe_merge_identity_review"
        return "remaining_missing_tax_merge_identity_review"
    if "non_primary_partner_source" in blockers:
        return "remaining_missing_tax_non_primary_review"
    if "unsafe_partner_name" in blockers:
        return "remaining_missing_tax_unsafe_name_review"
    return "remaining_missing_tax_misc_review"


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
    missing_tax_rows = [
        row
        for row in rows
        if clean(row.get("dry_run_action")) == "blocked"
        and "missing_tax_number" in blockers_for(row)
    ]
    subroute_counts: Counter[str] = Counter()
    blocker_counts: Counter[str] = Counter()
    combo_counts: Counter[str] = Counter()
    source_counts: Counter[str] = Counter()
    source_row_count_counts: Counter[str] = Counter()
    subroute_samples: dict[str, list[dict[str, object]]] = defaultdict(list)
    output_rows: list[dict[str, object]] = []

    for row in missing_tax_rows:
        blockers = [clean(item) for item in clean(row.get("blockers")).split(";") if clean(item)]
        subroute = subroute_for(row)
        subroute_counts[subroute] += 1
        combo_counts[";".join(blockers)] += 1
        source_counts[clean(row.get("sources"))] += 1
        source_row_count_counts[clean(row.get("source_row_count"))] += 1
        for blocker in blockers:
            blocker_counts[blocker] += 1
        output_row = {
            "row_no": clean(row.get("row_no")),
            "subroute": subroute,
            "blockers": ";".join(blockers),
            "legacy_partner_source": clean(row.get("legacy_partner_source")),
            "legacy_partner_id": clean(row.get("legacy_partner_id")),
            "partner_name": clean(row.get("partner_name")),
            "tax_number": clean(row.get("tax_number")),
            "sources": clean(row.get("sources")),
            "source_row_count": clean(row.get("source_row_count")),
            "recommended_next_task": subroute,
        }
        output_rows.append(output_row)
        if len(subroute_samples[subroute]) < 10:
            subroute_samples[subroute].append(output_row)

    fieldnames = [
        "row_no",
        "subroute",
        "blockers",
        "legacy_partner_source",
        "legacy_partner_id",
        "partner_name",
        "tax_number",
        "sources",
        "source_row_count",
        "recommended_next_task",
    ]
    sample_rows = [sample for subroute in sorted(subroute_samples) for sample in subroute_samples[subroute]]
    write_csv(OUTPUT_CSV, fieldnames, output_rows)
    write_csv(SAMPLE_CSV, fieldnames, sample_rows)

    result = {
        "status": "PASS" if not missing_columns and len(missing_tax_rows) == EXPECTED_MISSING_TAX_ROWS else "FAIL",
        "mode": "partner_l4_remaining_missing_tax_screen",
        "input": str(INPUT_CSV),
        "total_rows": len(rows),
        "remaining_missing_tax_rows": len(missing_tax_rows),
        "missing_columns": missing_columns,
        "subroute_counts": dict(sorted(subroute_counts.items())),
        "blocker_counts": dict(sorted(blocker_counts.items())),
        "source_counts": dict(sorted(source_counts.items())),
        "source_row_count_counts": dict(sorted(source_row_count_counts.items())),
        "top_blocker_combinations": [
            {"blockers": blockers, "rows": count}
            for blockers, count in combo_counts.most_common(20)
        ],
        "subroute_priority": [
            "remaining_missing_tax_merge_identity_review",
            "remaining_missing_tax_unsafe_name_review",
            "remaining_missing_tax_unsafe_merge_identity_review",
            "remaining_missing_tax_non_primary_review",
            "remaining_missing_tax_conflict_review",
            "remaining_missing_tax_misc_review",
        ],
        "outputs": {
            "screen_rows": str(OUTPUT_CSV),
            "sample_rows": str(SAMPLE_CSV),
        },
        "next_gate": "Open a no-DB dry-run for remaining_missing_tax_merge_identity_review before any write design.",
    }
    OUTPUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_JSON.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("PARTNER_REMAINING_MISSING_TAX_SCREEN=" + json.dumps({
        "status": result["status"],
        "remaining_missing_tax_rows": result["remaining_missing_tax_rows"],
        "subroute_counts": result["subroute_counts"],
    }, ensure_ascii=False, sort_keys=True))
    return 0 if result["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
