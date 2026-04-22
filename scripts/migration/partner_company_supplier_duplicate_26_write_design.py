#!/usr/bin/env python3
from __future__ import annotations

import csv
import json
from collections import Counter
from pathlib import Path


INPUT_CSV = Path("artifacts/migration/partner_l4_remaining88_blocked_screen_rows_v1.csv")
OUTPUT_JSON = Path("artifacts/migration/partner_l4_company_supplier_duplicate_26_write_design_result_v1.json")
OUTPUT_CSV = Path("artifacts/migration/partner_l4_company_supplier_duplicate_26_write_design_rows_v1.csv")
OUTPUT_REPORT = Path("docs/migration_alignment/partner_l4_company_supplier_duplicate_26_write_design_report_v1.md")
TASK_RESULT = Path("agent_ops/state/task_results/ITER-2026-04-14-PARTNER-L4-COMPANY-SUPPLIER-DUPLICATE-26-WRITE-DESIGN.json")
EXPECTED_ROWS = 26


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
    columns, rows = read_csv(INPUT_CSV)
    required = {
        "row_no",
        "route",
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
    candidate_rows = [
        row for row in rows
        if clean(row.get("route")) == "company_supplier_duplicate_group_screen"
    ]
    design_rows: list[dict[str, object]] = []
    action_counts: Counter[str] = Counter()
    invalid_rows: list[dict[str, str]] = []
    for row in candidate_rows:
        tax_number = clean(row.get("tax_number"))
        source = clean(row.get("legacy_partner_source"))
        sources = clean(row.get("sources"))
        if source != "company_supplier" or "company" not in sources.split(";") or "supplier" not in sources.split(";") or not tax_number:
            invalid_rows.append(row)
            action = "manual_review"
        else:
            action = "create_company_supplier_partner_with_tax_number"
        action_counts[action] += 1
        design_rows.append({
            "write_design_id": f"partner_l4_company_supplier_duplicate_26_{len(design_rows) + 1:04d}",
            "proposed_action": action,
            "legacy_partner_source": "company_supplier" if source == "company_supplier" else source,
            "legacy_partner_id": clean(row.get("legacy_partner_id")),
            "partner_name": clean(row.get("partner_name")),
            "tax_number": tax_number,
            "dedup_key_type": clean(row.get("dedup_key_type")),
            "dedup_key": clean(row.get("dedup_key")),
            "sources": sources,
            "source_row_count": clean(row.get("source_row_count")),
            "merge_strategy": clean(row.get("merge_strategy")),
            "customer_flag": "true",
            "supplier_flag": "true",
            "rollback_key_source": "company_supplier" if source == "company_supplier" else source,
            "rollback_key_legacy_id": clean(row.get("legacy_partner_id")),
            "source_screen_row_no": clean(row.get("row_no")),
            "db_write": "false",
        })

    fieldnames = [
        "write_design_id",
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
        "customer_flag",
        "supplier_flag",
        "rollback_key_source",
        "rollback_key_legacy_id",
        "source_screen_row_no",
        "db_write",
    ]
    write_csv(OUTPUT_CSV, fieldnames, design_rows)
    status = (
        "PASS"
        if not missing_columns
        and len(design_rows) == EXPECTED_ROWS
        and action_counts.get("manual_review", 0) == 0
        else "FAIL"
    )
    result = {
        "status": status,
        "mode": "partner_l4_company_supplier_duplicate_26_write_design",
        "input": str(INPUT_CSV),
        "write_design_rows": len(design_rows),
        "expected_rows": EXPECTED_ROWS,
        "missing_columns": missing_columns,
        "invalid_rows": len(invalid_rows),
        "action_counts": dict(sorted(action_counts.items())),
        "outputs": {"write_design_rows": str(OUTPUT_CSV)},
        "next_gate": "Bounded create-only DB write with rollback targets.",
    }
    OUTPUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_JSON.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    OUTPUT_REPORT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_REPORT.write_text(
        "\n".join([
            "# Partner L4 company/supplier duplicate 26 write design",
            "",
            f"- Status: {status}",
            f"- Input: `{INPUT_CSV}`",
            f"- Write design rows: {len(design_rows)}",
            "- Proposed action: `create_company_supplier_partner_with_tax_number`",
            "- DB writes: 0",
            "- Risk: low; design-only evidence for next bounded create-only write.",
            "",
        ]),
        encoding="utf-8",
    )
    TASK_RESULT.parent.mkdir(parents=True, exist_ok=True)
    TASK_RESULT.write_text(json.dumps({
        "task_id": "ITER-2026-04-14-PARTNER-L4-COMPANY-SUPPLIER-DUPLICATE-26-WRITE-DESIGN",
        "status": status,
        "completed_at": "2026-04-15T00:25:00+08:00",
        "result": {
            "mode": result["mode"],
            "write_design_rows": len(design_rows),
            "expected_rows": EXPECTED_ROWS,
            "db_writes": 0,
            "action_counts": result["action_counts"],
        },
        "verification": {
            "validate_task": "pending",
            "py_compile": "pending",
            "design_script": "pending",
            "json_result": "pending",
            "artifact_presence": "pending",
            "task_result_json": "pending",
            "verify_native_business_fact_static": "pending",
        },
        "risk": {
            "level": "low",
            "stop_condition_triggered": status != "PASS",
        },
        "next_step": "Execute a bounded create-only DB write with rollback targets.",
    }, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("PARTNER_COMPANY_SUPPLIER_DUPLICATE_26_WRITE_DESIGN=" + json.dumps({
        "status": status,
        "write_design_rows": len(design_rows),
        "action_counts": result["action_counts"],
    }, ensure_ascii=False, sort_keys=True))
    return 0 if status == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
