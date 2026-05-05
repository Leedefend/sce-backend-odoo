"""Build a consolidated readiness report for SCBS mapping decisions."""

from __future__ import annotations

import csv
import json
import os
from pathlib import Path


def artifact_root() -> Path:
    env_root = os.getenv("MIGRATION_ARTIFACT_ROOT")
    candidates = [Path(env_root)] if env_root else []
    candidates.extend([Path.cwd() / "artifacts/migration", Path("/mnt/artifacts/migration"), Path("/tmp")])
    for candidate in candidates:
        if candidate.exists():
            return candidate
    return Path("artifacts/migration")


def read_json(path: Path) -> dict[str, object]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def write_json(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def md_table(rows: list[dict[str, object]], columns: list[str]) -> list[str]:
    lines = [
        "| " + " | ".join(columns) + " |",
        "| " + " | ".join("---" for _ in columns) + " |",
    ]
    for row in rows:
        lines.append("| " + " | ".join(str(row.get(column, "")) for column in columns) + " |")
    return lines


def fmt_amount(value: object) -> str:
    try:
        return f"{float(value):,.2f}"
    except Exception:
        return str(value or "")


def normalize_amount_columns(rows: list[dict[str, str]], amount_keys: tuple[str, ...] = ("fact_amount", "amount_total")) -> list[dict[str, object]]:
    normalized: list[dict[str, object]] = []
    for row in rows:
        item: dict[str, object] = dict(row)
        for key in amount_keys:
            if key in item:
                item[key] = fmt_amount(item[key])
        normalized.append(item)
    return normalized


def main() -> None:
    artifacts = artifact_root()
    result_json = artifacts / "scbs_mapping_decision_readiness_report_result_v1.json"
    report_md = artifacts / "scbs_mapping_decision_readiness_report_v1.md"

    reconciliation = read_json(artifacts / "scbs_fact_staging_reconciliation_result_v1.json")
    blocker = read_json(artifacts / "scbs_fact_staging_blocker_report_result_v1.json")
    workbook = read_json(artifacts / "scbs_mapping_decision_workbook_result_v1.json")
    validate = read_json(artifacts / "scbs_mapping_decision_validate_result_v1.json")
    batch_validate = read_json(artifacts / "scbs_mapping_decision_batch_validate_result_v1.json")

    action_summary = normalize_amount_columns(read_csv(artifacts / "scbs_mapping_decision_action_summary_v1.csv"))
    batch_summary = normalize_amount_columns(read_csv(artifacts / "scbs_mapping_decision_batch_validate_summary_v1.csv"))
    projection_simulation = normalize_amount_columns(read_csv(artifacts / "scbs_mapping_decision_projection_simulation_v1.csv"), ("amount_total",))

    total = dict(reconciliation.get("total") or {})
    blocker_totals = dict(blocker.get("totals") or {})
    status_counts = dict(batch_validate.get("status_counts") or {})
    validate_counts = dict(validate.get("counts") or {})

    lines: list[str] = [
        "# SCBS Mapping Decision Readiness",
        "",
        f"Database: `{reconciliation.get('database') or validate.get('database') or ''}`",
        "",
        "## Current Fact Gate",
        "",
    ]
    lines.extend(
        md_table(
            [
                {
                    "staged_rows": total.get("row_count", ""),
                    "staged_amount": fmt_amount(total.get("amount_total", "")),
                    "blocked_rows": total.get("blocked", ""),
                    "staging_ready": total.get("staging_ready", ""),
                    "conflict": total.get("conflict", ""),
                    "projection_ready": total.get("projection_ready", ""),
                }
            ],
            ["staged_rows", "staged_amount", "blocked_rows", "staging_ready", "conflict", "projection_ready"],
        )
    )
    lines.extend(
        [
            "",
            "## Remaining Gap",
            "",
            f"- Missing-map technical blockage: `{blocker_totals.get('blocked_rows', 0)}` rows.",
            f"- Conflict review queue: `{blocker_totals.get('conflict_rows', total.get('conflict', 0))}` rows, amount `{fmt_amount(blocker_totals.get('conflict_amount', 0))}`.",
            f"- Mapping review workbook rows: `{workbook.get('review_rows', '')}`.",
            f"- Validation baseline: `{validate_counts}`.",
            f"- Batch status baseline: `{status_counts}`.",
            "",
            "## Action Summary",
            "",
        ]
    )
    lines.extend(md_table(action_summary, ["dimension", "suggested_action", "mapping_rows", "fact_rows", "fact_amount", "with_target"]))
    lines.extend(["", "## Batch Status", ""])
    lines.extend(md_table(batch_summary, ["suggested_action", "batch_status", "row_count", "decided_rows", "blank_rows", "error_rows", "fact_rows", "fact_amount"]))
    lines.extend(["", "## Projection Simulation", ""])
    lines.extend(md_table(projection_simulation, ["simulated_gate", "rows", "amount_total"]))
    lines.extend(
        [
            "",
            "## Execution Order",
            "",
            "1. Fill `01_manual_partner_required` using partner target candidates.",
            "2. Fill `02_review_non_counterparty_label` with business treatment: confirm, ignore, or keep conflict.",
            "3. Fill `03_choose_target_partner` using partner target candidates.",
            "4. Fill test/non-real batches as ignore or conflict.",
            "5. Fill business entity and project batches using consolidation and target candidate reports.",
            "6. Fill normal partner batch.",
            "7. Run batch validation until target batches are `READY` or intentionally `PARTIAL`.",
            "8. Run per-batch validate, dry-run apply, write apply, then rerun staging reconciliation.",
            "",
            "## Current Conclusion",
            "",
            "The technical staging and missing-map gates are closed. The upgrade is waiting on business mapping decisions before any formal projection can be opened.",
            "",
        ]
    )
    report_md.write_text("\n".join(lines), encoding="utf-8")
    payload = {
        "status": "PASS",
        "report_md": str(report_md),
        "staged_rows": total.get("row_count"),
        "blocked_rows": total.get("blocked"),
        "conflict_rows": total.get("conflict"),
        "projection_ready": total.get("projection_ready"),
        "workbook_review_rows": workbook.get("review_rows"),
        "batch_status_counts": status_counts,
    }
    write_json(result_json, payload)
    print("SCBS_MAPPING_DECISION_READINESS_REPORT=" + json.dumps(payload, ensure_ascii=False, sort_keys=True))


main()
