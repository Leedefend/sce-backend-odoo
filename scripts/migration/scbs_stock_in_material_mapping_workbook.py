#!/usr/bin/env python3
"""Build review workbooks for SCBS stock-in material catalog mapping."""

from __future__ import annotations

import csv
import json
from pathlib import Path


ARTIFACT_ROOT = Path("artifacts/migration")
COVERAGE_CSV = ARTIFACT_ROOT / "scbs_stock_in_material_catalog_coverage_v1.csv"
OUTPUT_CSV = ARTIFACT_ROOT / "scbs_stock_in_material_mapping_workbook_v1.csv"
SPLIT_PREFIX = "scbs_stock_in_material_mapping"
OUTPUT_JSON = ARTIFACT_ROOT / "scbs_stock_in_material_mapping_workbook_result_v1.json"
OUTPUT_MD = ARTIFACT_ROOT / "scbs_stock_in_material_mapping_workbook_v1.md"


def suggested_action(row: dict[str, str]) -> str:
    state = row["coverage_state"]
    if state == "catalog_candidate_exact_text":
        return "confirm_exact_text_catalog_or_create_new"
    if state == "catalog_candidate_name_spec":
        return "review_name_spec_catalog_or_create_new"
    if state == "missing_legacy_material_id":
        return "manual_material_identity_required"
    return "create_or_map_material_catalog"


def review_priority(row: dict[str, str]) -> int:
    state = row["coverage_state"]
    amount = float(row["amount"] or 0)
    if state == "missing_legacy_material_id":
        return 1
    if state == "catalog_candidate_exact_text" and amount >= 100000:
        return 2
    if state == "catalog_candidate_name_spec" and amount >= 100000:
        return 3
    if state == "catalog_missing" and amount >= 100000:
        return 4
    if state.startswith("catalog_candidate"):
        return 5
    return 6


def normalize_review_row(row: dict[str, str]) -> dict[str, str]:
    return {
        "review_priority": str(review_priority(row)),
        "suggested_action": suggested_action(row),
        "decision": "",
        "decision_note": "",
        "target_material_catalog_id": row.get("target_material_catalog_id", ""),
        "accepted_material_catalog_id": "",
        "coverage_state": row["coverage_state"],
        "legacy_material_id": row["legacy_material_id"],
        "material_name": row["material_name"],
        "spec_model": row["spec_model"],
        "uom_text": row["uom_text"],
        "line_rows": row["line_rows"],
        "header_rows": row["header_rows"],
        "qty": row["qty"],
        "amount": row["amount"],
        "exact_text_catalog_id": row.get("exact_text_catalog_id", ""),
        "exact_text_match_count": row.get("exact_text_match_count", "0"),
        "name_spec_catalog_id": row.get("name_spec_catalog_id", ""),
        "name_spec_match_count": row.get("name_spec_match_count", "0"),
    }


def write_csv(path: Path, rows: list[dict[str, str]], fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    if not COVERAGE_CSV.exists():
        raise RuntimeError({"missing_coverage_csv": str(COVERAGE_CSV)})
    with COVERAGE_CSV.open(encoding="utf-8") as f:
        rows = [normalize_review_row(row) for row in csv.DictReader(f)]
    rows.sort(key=lambda row: (int(row["review_priority"]), -float(row["amount"] or 0), row["material_name"]))
    fields = list(rows[0].keys()) if rows else []
    write_csv(OUTPUT_CSV, rows, fields)

    split_specs = {
        "01_manual_material_identity_required": lambda row: row["suggested_action"] == "manual_material_identity_required",
        "02_confirm_exact_text_catalog_or_create_new": lambda row: row["suggested_action"] == "confirm_exact_text_catalog_or_create_new",
        "03_review_name_spec_catalog_or_create_new": lambda row: row["suggested_action"] == "review_name_spec_catalog_or_create_new",
        "04_create_or_map_material_catalog_high_amount": lambda row: row["suggested_action"] == "create_or_map_material_catalog" and float(row["amount"] or 0) >= 100000,
        "05_create_or_map_material_catalog_remaining": lambda row: row["suggested_action"] == "create_or_map_material_catalog" and float(row["amount"] or 0) < 100000,
    }
    split_outputs = {}
    for name, predicate in split_specs.items():
        split_rows = [row for row in rows if predicate(row)]
        path = ARTIFACT_ROOT / f"{SPLIT_PREFIX}_{name}_v1.csv"
        write_csv(path, split_rows, fields)
        split_outputs[name] = {"path": str(path), "rows": len(split_rows), "amount": round(sum(float(r["amount"] or 0) for r in split_rows), 2)}

    by_action: dict[str, dict[str, object]] = {}
    for row in rows:
        action = row["suggested_action"]
        bucket = by_action.setdefault(action, {"rows": 0, "amount": 0.0})
        bucket["rows"] = int(bucket["rows"]) + 1
        bucket["amount"] = float(bucket["amount"]) + float(row["amount"] or 0)
    for bucket in by_action.values():
        bucket["amount"] = round(float(bucket["amount"]), 2)

    result = {
        "status": "PASS",
        "source": str(COVERAGE_CSV),
        "output": str(OUTPUT_CSV),
        "rows": len(rows),
        "amount": round(sum(float(row["amount"] or 0) for row in rows), 2),
        "by_action": by_action,
        "split_outputs": split_outputs,
        "business_policy": "material_catalog_mapping_without_product_promotion",
    }
    OUTPUT_JSON.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    OUTPUT_MD.write_text(
        "\n".join(
            [
                "# SCBS Stock-In Material Mapping Workbook",
                "",
                "## Policy",
                "",
                "Use `sc.material.catalog` as the material management dimension. Do not promote SCBS materials into product templates/products for this acceptance path.",
                "",
                "## Summary",
                "",
                f"- review rows: {len(rows)}",
                f"- amount: {result['amount']}",
                "",
                "## By Action",
                "",
                "| Action | Rows | Amount |",
                "| --- | ---: | ---: |",
                *[
                    f"| {action} | {payload['rows']} | {payload['amount']} |"
                    for action, payload in sorted(by_action.items())
                ],
                "",
                "## Split Workbooks",
                "",
                "| Batch | Rows | Amount | Path |",
                "| --- | ---: | ---: | --- |",
                *[
                    f"| {name} | {payload['rows']} | {payload['amount']} | `{payload['path']}` |"
                    for name, payload in split_outputs.items()
                ],
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    print("SCBS_STOCK_IN_MATERIAL_MAPPING_WORKBOOK=" + json.dumps(result, ensure_ascii=False, sort_keys=True))


if __name__ == "__main__":
    main()
