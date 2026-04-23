#!/usr/bin/env python3
from __future__ import annotations

import csv
import json
from collections import Counter, defaultdict
from pathlib import Path


INPUT_CSV = Path("artifacts/migration/partner_l4_blocked_screen_rows_v1.csv")
OUTPUT_JSON = Path("artifacts/migration/partner_l4_merge_identity_screen_result_v1.json")
OUTPUT_CSV = Path("artifacts/migration/partner_l4_merge_identity_screen_rows_v1.csv")
SAMPLE_CSV = Path("artifacts/migration/partner_l4_merge_identity_screen_samples_v1.csv")
EXPECTED_ROUTE_ROWS = 3048


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


def subroute_for(row: dict[str, str]) -> str:
    blockers = {clean(item) for item in clean(row.get("blockers")).split(";") if clean(item)}
    source_row_count = int(clean(row.get("source_row_count")) or "0")
    sources = clean(row.get("sources"))
    if source_row_count > 2:
        return "complex_multirow_merge_review"
    if "missing_tax_number" in blockers:
        return "missing_tax_merge_review"
    if "unsafe_partner_name" in blockers:
        return "unsafe_name_merge_review"
    if sources == "company;supplier":
        return "company_supplier_pair_merge_review"
    if sources == "company":
        return "company_duplicate_pair_merge_review"
    return "merge_identity_misc_review"


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
        "sources",
        "source_row_count",
    }
    missing_columns = sorted(required_columns - set(columns))
    merge_rows = [row for row in rows if clean(row.get("route")) == "merge_identity_screen"]
    subroute_counts: Counter[str] = Counter()
    blocker_counts: Counter[str] = Counter()
    source_counts: Counter[str] = Counter()
    source_row_count_counts: Counter[str] = Counter()
    subroute_samples: dict[str, list[dict[str, object]]] = defaultdict(list)
    output_rows: list[dict[str, object]] = []
    for row in merge_rows:
        blockers = [clean(item) for item in clean(row.get("blockers")).split(";") if clean(item)]
        subroute = subroute_for(row)
        subroute_counts[subroute] += 1
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
        "status": "PASS" if not missing_columns and len(merge_rows) == EXPECTED_ROUTE_ROWS else "FAIL",
        "mode": "partner_l4_merge_identity_screen",
        "input": str(INPUT_CSV),
        "merge_identity_rows": len(merge_rows),
        "missing_columns": missing_columns,
        "subroute_counts": dict(sorted(subroute_counts.items())),
        "blocker_counts": dict(sorted(blocker_counts.items())),
        "source_counts": dict(sorted(source_counts.items())),
        "source_row_count_counts": dict(sorted(source_row_count_counts.items())),
        "subroute_priority": [
            "company_supplier_pair_merge_review",
            "company_duplicate_pair_merge_review",
            "missing_tax_merge_review",
            "unsafe_name_merge_review",
            "complex_multirow_merge_review",
            "merge_identity_misc_review",
        ],
        "outputs": {
            "screen_rows": str(OUTPUT_CSV),
            "sample_rows": str(SAMPLE_CSV),
        },
        "next_gate": "Open company_supplier_pair_merge_review as a no-DB evidence screen before any merge/update write.",
    }
    OUTPUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_JSON.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("PARTNER_MERGE_IDENTITY_SCREEN=" + json.dumps({
        "status": result["status"],
        "merge_identity_rows": result["merge_identity_rows"],
        "subroute_counts": result["subroute_counts"],
    }, ensure_ascii=False, sort_keys=True))
    return 0 if result["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
