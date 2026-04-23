#!/usr/bin/env python3
from __future__ import annotations

import csv
import json
from collections import Counter
from pathlib import Path


INPUT_CSV = Path("artifacts/migration/partner_l4_nodb_refresh_rows_v1.csv")
OUTPUT_JSON = Path("artifacts/migration/partner_l4_company_duplicate_24_write_design_result_v1.json")
OUTPUT_CSV = Path("artifacts/migration/partner_l4_company_duplicate_24_write_design_rows_v1.csv")
OUTPUT_REPORT = Path("docs/migration_alignment/partner_l4_company_duplicate_24_write_design_report_v1.md")
TASK_RESULT = Path("agent_ops/state/task_results/ITER-2026-04-14-PARTNER-L4-COMPANY-DUPLICATE-24-WRITE-DESIGN.json")
EXPECTED_ROWS = 24
LEGACY_SOURCE = "cooperat_company"


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
        "legacy_partner_source",
        "legacy_partner_id",
        "partner_name",
        "tax_number",
        "sources",
        "source_row_count",
        "merge_strategy",
        "dry_run_action",
        "blockers",
    }
    missing_columns = sorted(required - set(columns))
    candidate_rows = [
        row for row in rows
        if clean(row.get("dry_run_action")) == "blocked"
        and clean(row.get("blockers")) == "deduplicated_group_not_create_only"
        and clean(row.get("legacy_partner_source")) == LEGACY_SOURCE
    ]
    design_rows: list[dict[str, object]] = []
    action_counts: Counter[str] = Counter()
    invalid_rows = []
    for row in candidate_rows:
        if clean(row.get("sources")) != "company" or not clean(row.get("tax_number")):
            action = "manual_review"
            invalid_rows.append(row)
        else:
            action = "create_company_partner_with_tax_number"
        action_counts[action] += 1
        design_rows.append({
            "write_design_id": f"partner_l4_company_duplicate_24_{len(design_rows) + 1:04d}",
            "proposed_action": action,
            "legacy_partner_source": LEGACY_SOURCE,
            "legacy_partner_id": clean(row.get("legacy_partner_id")),
            "partner_name": clean(row.get("partner_name")),
            "tax_number": clean(row.get("tax_number")),
            "sources": clean(row.get("sources")),
            "source_row_count": clean(row.get("source_row_count")),
            "merge_strategy": clean(row.get("merge_strategy")),
            "customer_flag": "true",
            "supplier_flag": "false",
            "rollback_key_source": LEGACY_SOURCE,
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
    status = "PASS" if not missing_columns and len(design_rows) == EXPECTED_ROWS and not invalid_rows else "FAIL"
    result = {
        "status": status,
        "mode": "partner_l4_company_duplicate_24_write_design",
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
            "# Partner L4 company duplicate 24 write design",
            "",
            f"- Status: {status}",
            f"- Write design rows: {len(design_rows)}",
            "- Proposed action: `create_company_partner_with_tax_number`",
            "- DB writes: 0",
            "",
        ]),
        encoding="utf-8",
    )
    TASK_RESULT.parent.mkdir(parents=True, exist_ok=True)
    TASK_RESULT.write_text(json.dumps({
        "task_id": "ITER-2026-04-14-PARTNER-L4-COMPANY-DUPLICATE-24-WRITE-DESIGN",
        "status": status,
        "completed_at": "2026-04-15T01:05:00+08:00",
        "result": {"mode": result["mode"], "write_design_rows": len(design_rows), "expected_rows": EXPECTED_ROWS, "db_writes": 0, "action_counts": result["action_counts"]},
        "verification": {"validate_task": "pending", "py_compile": "pending", "design_script": "pending", "json_result": "pending", "artifact_presence": "pending", "task_result_json": "pending", "verify_native_business_fact_static": "pending"},
        "risk": {"level": "low", "stop_condition_triggered": status != "PASS"},
        "next_step": "Execute a bounded create-only DB write with rollback targets.",
    }, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("PARTNER_COMPANY_DUPLICATE_24_WRITE_DESIGN=" + json.dumps({"status": status, "write_design_rows": len(design_rows), "action_counts": result["action_counts"]}, ensure_ascii=False, sort_keys=True))
    return 0 if status == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
