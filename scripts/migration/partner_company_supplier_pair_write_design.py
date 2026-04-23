#!/usr/bin/env python3
from __future__ import annotations

import csv
import json
from pathlib import Path


DRY_RUN_CSV = Path("artifacts/migration/partner_l4_company_supplier_pair_merge_dry_run_rows_v1.csv")
OUTPUT_JSON = Path("artifacts/migration/partner_l4_company_supplier_pair_write_design_result_v1.json")
OUTPUT_CSV = Path("artifacts/migration/partner_l4_company_supplier_pair_write_design_rows_v1.csv")
EXPECTED_CANDIDATES = 1713


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


def main() -> int:
    columns, rows = read_csv(DRY_RUN_CSV)
    required_columns = {
        "dry_run_action",
        "company_legacy_partner_id",
        "supplier_legacy_partner_id",
        "partner_name",
        "tax_number",
        "target_customer_rank",
        "target_supplier_rank",
        "field_policy",
    }
    missing_columns = sorted(required_columns - set(columns))
    candidates = [row for row in rows if clean(row.get("dry_run_action")) == "merge_dry_run_candidate"]
    design_rows = []
    blockers = []
    for row in candidates:
        row_blockers = []
        if not clean(row.get("company_legacy_partner_id")):
            row_blockers.append("missing_company_legacy_partner_id")
        if not clean(row.get("supplier_legacy_partner_id")):
            row_blockers.append("missing_supplier_legacy_partner_id")
        if not clean(row.get("tax_number")):
            row_blockers.append("missing_tax_number")
        if clean(row.get("target_customer_rank")) != "1" or clean(row.get("target_supplier_rank")) != "1":
            row_blockers.append("target_rank_not_both_one")
        blockers.extend(row_blockers)
        design_rows.append(
            {
                "write_action": "create_merged_partner" if not row_blockers else "blocked",
                "blockers": ";".join(row_blockers),
                "legacy_partner_source": "cooperat_company",
                "legacy_partner_id": clean(row.get("company_legacy_partner_id")),
                "partner_name": clean(row.get("partner_name")),
                "legacy_credit_code": clean(row.get("tax_number")),
                "legacy_tax_no": clean(row.get("tax_number")),
                "customer_rank": 1,
                "supplier_rank": 1,
                "supplier_legacy_partner_id": clean(row.get("supplier_legacy_partner_id")),
                "legacy_source_evidence": "company_supplier_pair_merge_dry_run",
                "rollback_key": "legacy_partner_source + legacy_partner_id",
            }
        )
    fieldnames = [
        "write_action",
        "blockers",
        "legacy_partner_source",
        "legacy_partner_id",
        "partner_name",
        "legacy_credit_code",
        "legacy_tax_no",
        "customer_rank",
        "supplier_rank",
        "supplier_legacy_partner_id",
        "legacy_source_evidence",
        "rollback_key",
    ]
    write_csv(OUTPUT_CSV, fieldnames, design_rows)
    blocked_rows = [row for row in design_rows if row["write_action"] == "blocked"]
    result = {
        "status": "PASS" if not missing_columns and len(candidates) == EXPECTED_CANDIDATES and not blocked_rows else "FAIL",
        "mode": "partner_l4_company_supplier_pair_write_design",
        "input": str(DRY_RUN_CSV),
        "candidate_rows": len(candidates),
        "write_design_rows": len(design_rows),
        "blocked_rows": len(blocked_rows),
        "missing_columns": missing_columns,
        "blockers": sorted(set(blockers)),
        "write_policy": {
            "action": "create_merged_partner",
            "allowed_fields": [
                "name",
                "company_type",
                "customer_rank",
                "supplier_rank",
                "legacy_partner_id",
                "legacy_partner_source",
                "legacy_partner_name",
                "legacy_credit_code",
                "legacy_tax_no",
                "legacy_source_evidence",
            ],
            "forbidden_actions": ["update_existing_partner", "unlink", "raw_sql", "acl_change"],
            "rollback_key": "legacy_partner_source + legacy_partner_id",
        },
        "outputs": {
            "write_design_rows": str(OUTPUT_CSV),
        },
        "next_gate": "High-risk bounded create write requires explicit authorization and immediate readonly post-write review.",
    }
    OUTPUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_JSON.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("PARTNER_COMPANY_SUPPLIER_PAIR_WRITE_DESIGN=" + json.dumps({
        "status": result["status"],
        "candidate_rows": result["candidate_rows"],
        "blocked_rows": result["blocked_rows"],
        "action": result["write_policy"]["action"],
    }, ensure_ascii=False, sort_keys=True))
    return 0 if result["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
