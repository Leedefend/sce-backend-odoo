#!/usr/bin/env python3
from __future__ import annotations

import csv
import json
from collections import Counter
from pathlib import Path


INPUT_CSV = Path("artifacts/migration/partner_l4_nodb_refresh_rows_v1.csv")
OUTPUT_JSON = Path("artifacts/migration/partner_l4_same_tax_company_conflict_21_screen_result_v1.json")
OUTPUT_CSV = Path("artifacts/migration/partner_l4_same_tax_company_conflict_21_screen_rows_v1.csv")
OUTPUT_REPORT = Path("docs/migration_alignment/partner_l4_same_tax_company_conflict_21_screen_report_v1.md")
TASK_RESULT = Path("agent_ops/state/task_results/ITER-2026-04-14-PARTNER-L4-SAME-TAX-COMPANY-CONFLICT-21-SCREEN.json")
EXPECTED_ROWS = 21


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


def tax_quality(tax_number: str) -> str:
    compact = tax_number.replace(" ", "").upper()
    if not compact:
        return "missing_tax"
    if len(set(compact)) <= 2:
        return "placeholder_tax"
    if compact.endswith("0000000000"):
        return "placeholder_tax"
    return "usable_tax"


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
        and clean(row.get("blockers")) == "same_tax_multiple_names;deduplicated_group_not_create_only"
        and clean(row.get("legacy_partner_source")) == "cooperat_company"
    ]
    output_rows: list[dict[str, object]] = []
    decision_counts: Counter[str] = Counter()
    for row in candidate_rows:
        quality = tax_quality(clean(row.get("tax_number")))
        decision = "company_same_tax_canonical_write_review" if quality == "usable_tax" else "company_same_tax_manual_review"
        decision_counts[decision] += 1
        output_rows.append({
            "row_no": clean(row.get("row_no")),
            "decision": decision,
            "tax_quality": quality,
            "legacy_partner_source": clean(row.get("legacy_partner_source")),
            "legacy_partner_id": clean(row.get("legacy_partner_id")),
            "partner_name": clean(row.get("partner_name")),
            "tax_number": clean(row.get("tax_number")),
            "sources": clean(row.get("sources")),
            "source_row_count": clean(row.get("source_row_count")),
            "merge_strategy": clean(row.get("merge_strategy")),
            "blockers": clean(row.get("blockers")),
        })
    fieldnames = ["row_no", "decision", "tax_quality", "legacy_partner_source", "legacy_partner_id", "partner_name", "tax_number", "sources", "source_row_count", "merge_strategy", "blockers"]
    write_csv(OUTPUT_CSV, fieldnames, output_rows)
    status = "PASS" if not missing_columns and len(output_rows) == EXPECTED_ROWS else "FAIL"
    result = {
        "status": status,
        "mode": "partner_l4_same_tax_company_conflict_21_screen",
        "screen_rows": len(output_rows),
        "expected_rows": EXPECTED_ROWS,
        "missing_columns": missing_columns,
        "decision_counts": dict(sorted(decision_counts.items())),
        "outputs": {"screen_rows": str(OUTPUT_CSV)},
        "next_gate": "Open no-DB write design for company_same_tax_canonical_write_review rows.",
    }
    OUTPUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_JSON.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    OUTPUT_REPORT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_REPORT.write_text(
        "\n".join([
            "# Partner L4 same-tax company conflict 21 screen",
            "",
            f"- Status: {status}",
            f"- Screen rows: {len(output_rows)}",
            f"- Decision counts: `{dict(sorted(decision_counts.items()))}`",
            "- DB writes: 0",
            "",
        ]),
        encoding="utf-8",
    )
    TASK_RESULT.parent.mkdir(parents=True, exist_ok=True)
    TASK_RESULT.write_text(json.dumps({
        "task_id": "ITER-2026-04-14-PARTNER-L4-SAME-TAX-COMPANY-CONFLICT-21-SCREEN",
        "status": status,
        "completed_at": "2026-04-15T01:50:00+08:00",
        "result": {"mode": result["mode"], "screen_rows": len(output_rows), "expected_rows": EXPECTED_ROWS, "db_writes": 0, "decision_counts": result["decision_counts"]},
        "verification": {"validate_task": "pending", "py_compile": "pending", "screen_script": "pending", "json_result": "pending", "artifact_presence": "pending", "task_result_json": "pending", "verify_native_business_fact_static": "pending"},
        "risk": {"level": "low", "stop_condition_triggered": status != "PASS"},
        "next_step": "Open no-DB write design for canonical write-review rows.",
    }, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("PARTNER_SAME_TAX_COMPANY_CONFLICT_21_SCREEN=" + json.dumps({"status": status, "screen_rows": len(output_rows), "decision_counts": result["decision_counts"]}, ensure_ascii=False, sort_keys=True))
    return 0 if status == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
