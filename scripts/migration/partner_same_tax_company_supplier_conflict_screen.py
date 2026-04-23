#!/usr/bin/env python3
from __future__ import annotations

import csv
import json
import re
from collections import Counter, defaultdict
from pathlib import Path


INPUT_CSV = Path("artifacts/migration/partner_l4_remaining190_blocked_screen_rows_v1.csv")
OUTPUT_JSON = Path("artifacts/migration/partner_l4_same_tax_company_supplier_conflict_screen_result_v1.json")
OUTPUT_CSV = Path("artifacts/migration/partner_l4_same_tax_company_supplier_conflict_screen_rows_v1.csv")
SAMPLE_CSV = Path("artifacts/migration/partner_l4_same_tax_company_supplier_conflict_screen_samples_v1.csv")
EXPECTED_ROUTE_ROWS = 111


def clean(value: object) -> str:
    return "" if value is None else str(value).strip()


def normalize_tax(value: object) -> str:
    return re.sub(r"[\s（）()\\-]+", "", clean(value).upper())


def tax_route(value: object) -> tuple[str, str]:
    raw = clean(value)
    tax = normalize_tax(raw)
    if re.fullmatch(r"1{8,}", tax):
        return ("placeholder_tax_split_by_name_screen", "placeholder_tax_ones")
    if raw != tax:
        return ("tax_normalization_screen", "tax_has_spacing_or_wrappers")
    if re.fullmatch(r"[0-9A-Z]{15,20}", tax):
        return ("same_tax_company_supplier_canonical_merge_review", "tax_format_usable")
    return ("same_tax_manual_conflict_screen", "tax_format_unusable")


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
    required = {
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
    missing_columns = sorted(required - set(columns))
    route_rows = [row for row in rows if clean(row.get("route")) == "same_tax_company_supplier_conflict_screen"]
    output_rows: list[dict[str, object]] = []
    route_counts: Counter[str] = Counter()
    reason_counts: Counter[str] = Counter()
    samples: dict[str, list[dict[str, object]]] = defaultdict(list)
    for row in route_rows:
        decision, reason = tax_route(row.get("tax_number"))
        route_counts[decision] += 1
        reason_counts[reason] += 1
        output_row = {
            "row_no": clean(row.get("row_no")),
            "decision": decision,
            "reason": reason,
            "legacy_partner_source": clean(row.get("legacy_partner_source")),
            "legacy_partner_id": clean(row.get("legacy_partner_id")),
            "partner_name": clean(row.get("partner_name")),
            "tax_number": clean(row.get("tax_number")),
            "normalized_tax_number": normalize_tax(row.get("tax_number")),
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
        "decision",
        "reason",
        "legacy_partner_source",
        "legacy_partner_id",
        "partner_name",
        "tax_number",
        "normalized_tax_number",
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
        "mode": "partner_l4_same_tax_company_supplier_conflict_screen",
        "input": str(INPUT_CSV),
        "route_rows": len(output_rows),
        "expected_route_rows": EXPECTED_ROUTE_ROWS,
        "missing_columns": missing_columns,
        "decision_counts": dict(sorted(route_counts.items())),
        "reason_counts": dict(sorted(reason_counts.items())),
        "outputs": {"screen_rows": str(OUTPUT_CSV), "sample_rows": str(SAMPLE_CSV)},
        "next_gate": "Open canonical merge no-DB design for usable-tax rows; placeholder tax rows require split-by-name handling.",
    }
    OUTPUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_JSON.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("PARTNER_SAME_TAX_COMPANY_SUPPLIER_CONFLICT_SCREEN=" + json.dumps({
        "status": result["status"],
        "route_rows": result["route_rows"],
        "decision_counts": result["decision_counts"],
    }, ensure_ascii=False, sort_keys=True))
    return 0 if result["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
