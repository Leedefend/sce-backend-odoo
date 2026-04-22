#!/usr/bin/env python3
from __future__ import annotations

import csv
import json
import re
from collections import defaultdict
from pathlib import Path


PAIR_CSV = Path("artifacts/migration/partner_l4_company_supplier_pair_screen_rows_v1.csv")
COMPANY_CSV = Path("tmp/raw/partner/company.csv")
SUPPLIER_CSV = Path("tmp/raw/partner/supplier.csv")
OUTPUT_JSON = Path("artifacts/migration/partner_l4_company_supplier_pair_merge_dry_run_result_v1.json")
OUTPUT_CSV = Path("artifacts/migration/partner_l4_company_supplier_pair_merge_dry_run_rows_v1.csv")
SAMPLE_CSV = Path("artifacts/migration/partner_l4_company_supplier_pair_merge_dry_run_samples_v1.csv")
EXPECTED_PAIR_ROWS = 1713


def clean(value: object) -> str:
    text = "" if value is None else str(value)
    text = text.replace("\u3000", " ").strip()
    return re.sub(r"\s+", " ", text)


def valid_tax(value: object) -> str:
    text = clean(value).upper()
    if not text or text in {"0", "1", "2", "3", "NULL", "NONE", "==请选择=="}:
        return ""
    return text if len(text) >= 8 else ""


def first_nonempty(*values: object) -> str:
    for value in values:
        text = clean(value)
        if text:
            return text
    return ""


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


def company_tax(row: dict[str, str]) -> str:
    return first_nonempty(valid_tax(row.get("SH")), valid_tax(row.get("TYSHXYDM")))


def supplier_tax(row: dict[str, str]) -> str:
    return first_nonempty(valid_tax(row.get("SH")), valid_tax(row.get("SHXYDM")), valid_tax(row.get("NSRSBH")), valid_tax(row.get("TISHXYDM")))


def main() -> int:
    pair_columns, pair_rows = read_csv(PAIR_CSV)
    company_columns, company_rows = read_csv(COMPANY_CSV)
    supplier_columns, supplier_rows = read_csv(SUPPLIER_CSV)
    required_pair_columns = {"evidence_grade", "partner_name", "tax_number", "sources", "source_row_count"}
    missing_columns = sorted(required_pair_columns - set(pair_columns))

    companies_by_tax: dict[str, list[dict[str, str]]] = defaultdict(list)
    suppliers_by_tax: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in company_rows:
        tax = company_tax(row)
        if tax:
            companies_by_tax[tax].append(row)
    for row in supplier_rows:
        tax = supplier_tax(row)
        if tax:
            suppliers_by_tax[tax].append(row)

    route_rows = [row for row in pair_rows if clean(row.get("evidence_grade")) == "deterministic_company_supplier_pair"]
    output_rows: list[dict[str, object]] = []
    blocker_counts: dict[str, int] = defaultdict(int)
    for row in route_rows:
        tax = clean(row.get("tax_number")).upper()
        companies = companies_by_tax.get(tax, [])
        suppliers = suppliers_by_tax.get(tax, [])
        blockers: list[str] = []
        if len(companies) != 1:
            blockers.append("company_tax_match_not_exactly_one")
        if len(suppliers) != 1:
            blockers.append("supplier_tax_match_not_exactly_one")
        if clean(row.get("sources")) != "company;supplier" or clean(row.get("source_row_count")) != "2":
            blockers.append("pair_shape_not_exact")
        company = companies[0] if len(companies) == 1 else {}
        supplier = suppliers[0] if len(suppliers) == 1 else {}
        for blocker in blockers:
            blocker_counts[blocker] += 1
        output_rows.append(
            {
                "row_no": clean(row.get("row_no")),
                "dry_run_action": "merge_dry_run_candidate" if not blockers else "blocked",
                "blockers": ";".join(blockers),
                "target_legacy_partner_source": "cooperat_company",
                "company_legacy_partner_id": clean(company.get("Id")),
                "supplier_legacy_partner_id": clean(supplier.get("ID")),
                "partner_name": clean(row.get("partner_name")),
                "company_name": clean(company.get("DWMC")),
                "supplier_name": clean(supplier.get("f_SupplierName")),
                "tax_number": tax,
                "target_customer_rank": 1,
                "target_supplier_rank": 1,
                "field_policy": "retain_company_identity_merge_supplier_flag",
                "rollback_key": "legacy_partner_source + company_legacy_partner_id",
            }
        )

    fieldnames = [
        "row_no",
        "dry_run_action",
        "blockers",
        "target_legacy_partner_source",
        "company_legacy_partner_id",
        "supplier_legacy_partner_id",
        "partner_name",
        "company_name",
        "supplier_name",
        "tax_number",
        "target_customer_rank",
        "target_supplier_rank",
        "field_policy",
        "rollback_key",
    ]
    write_csv(OUTPUT_CSV, fieldnames, output_rows)
    write_csv(SAMPLE_CSV, fieldnames, output_rows[:50])
    candidate_rows = [row for row in output_rows if row["dry_run_action"] == "merge_dry_run_candidate"]
    result = {
        "status": "PASS" if not missing_columns and len(route_rows) == EXPECTED_PAIR_ROWS else "FAIL",
        "mode": "partner_l4_company_supplier_pair_merge_dry_run",
        "inputs": {
            "pair_screen": str(PAIR_CSV),
            "company": str(COMPANY_CSV),
            "supplier": str(SUPPLIER_CSV),
        },
        "route_rows": len(route_rows),
        "merge_dry_run_candidate_rows": len(candidate_rows),
        "blocked_rows": len(output_rows) - len(candidate_rows),
        "missing_columns": missing_columns,
        "blocker_counts": dict(sorted(blocker_counts.items())),
        "outputs": {
            "dry_run_rows": str(OUTPUT_CSV),
            "sample_rows": str(SAMPLE_CSV),
        },
        "target_policy": "retain company/cooperat_company identity and set supplier_rank=1 with supplier legacy evidence",
        "next_gate": "Open a bounded write-design review before any merge/update write.",
    }
    OUTPUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_JSON.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("PARTNER_COMPANY_SUPPLIER_PAIR_MERGE_DRY_RUN=" + json.dumps({
        "status": result["status"],
        "route_rows": result["route_rows"],
        "merge_dry_run_candidate_rows": result["merge_dry_run_candidate_rows"],
        "blocked_rows": result["blocked_rows"],
        "blocker_counts": result["blocker_counts"],
    }, ensure_ascii=False, sort_keys=True))
    return 0 if result["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
