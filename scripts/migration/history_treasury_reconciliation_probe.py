#!/usr/bin/env python3
"""Read-only probe for historical treasury, fund daily, and financing surfaces."""

from __future__ import annotations

import json
import os
from pathlib import Path


def repo_root() -> Path:
    env_root = os.getenv("MIGRATION_REPO_ROOT")
    candidates = []
    if env_root:
        candidates.append(Path(env_root))
    candidates.extend([Path("/mnt"), Path.cwd()])
    for candidate in candidates:
        if (candidate / "addons/smart_construction_core/__manifest__.py").exists():
            return candidate
    return Path.cwd()


def resolve_artifact_root() -> Path:
    env_root = os.getenv("MIGRATION_ARTIFACT_ROOT")
    candidates = []
    if env_root:
        candidates.append(Path(env_root))
    candidates.append(repo_root() / "artifacts/migration")
    candidates.append(Path(f"/tmp/history_continuity/{env.cr.dbname}/adhoc"))  # noqa: F821
    for candidate in candidates:
        try:
            candidate.mkdir(parents=True, exist_ok=True)
            probe = candidate / ".write_probe"
            probe.write_text("ok\n", encoding="utf-8")
            probe.unlink()
            return candidate
        except Exception:
            continue
    return Path(f"/tmp/history_continuity/{env.cr.dbname}/adhoc")  # noqa: F821


def write_json(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def write_report(path: Path, payload: dict[str, object]) -> None:
    lines = [
        "# History Treasury Reconciliation Probe v1",
        "",
        f"Status: {payload['status']}",
        "",
        "## Decision",
        "",
        f"`{payload['decision']}`",
        "",
        "## Counts",
        "",
        "```json",
        json.dumps(payload["counts"], ensure_ascii=False, indent=2),
        "```",
        "",
        "## Gaps",
        "",
        "```json",
        json.dumps(payload["gaps"], ensure_ascii=False, indent=2),
        "```",
    ]
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def table_exists(table_name: str) -> bool:
    env.cr.execute("SELECT to_regclass(%s)", [table_name])  # noqa: F821
    return bool(env.cr.fetchone()[0])  # noqa: F821


def scalar(sql: str, params: list[object] | None = None) -> object:
    env.cr.execute(sql, params or [])  # noqa: F821
    row = env.cr.fetchone()  # noqa: F821
    return row[0] if row else None


def rows(sql: str, params: list[object] | None = None) -> list[tuple[object, ...]]:
    env.cr.execute(sql, params or [])  # noqa: F821
    return env.cr.fetchall()  # noqa: F821


def count_table(table_name: str, where: str = "TRUE") -> int:
    if not table_exists(table_name):
        return 0
    return int(scalar(f"SELECT COUNT(*) FROM {table_name} WHERE {where}") or 0)


def sum_table(table_name: str, column_name: str, where: str = "TRUE") -> float:
    if not table_exists(table_name):
        return 0.0
    return float(scalar(f"SELECT COALESCE(SUM({column_name}), 0) FROM {table_name} WHERE {where}") or 0.0)


ARTIFACT_ROOT = resolve_artifact_root()
OUTPUT_JSON = ARTIFACT_ROOT / "history_treasury_reconciliation_probe_result_v1.json"
OUTPUT_REPORT = ARTIFACT_ROOT / "history_treasury_reconciliation_probe_report_v1.md"

counts = {
    "treasury_ledger_rows": count_table("sc_treasury_ledger"),
    "treasury_ledger_posted_rows": count_table("sc_treasury_ledger", "state = 'posted'"),
    "treasury_ledger_with_project": count_table("sc_treasury_ledger", "project_id IS NOT NULL"),
    "treasury_ledger_with_partner": count_table("sc_treasury_ledger", "partner_id IS NOT NULL"),
    "treasury_ledger_income_rows": count_table("sc_treasury_ledger", "direction = 'in'"),
    "treasury_ledger_outflow_rows": count_table("sc_treasury_ledger", "direction = 'out'"),
    "treasury_ledger_income_amount": sum_table("sc_treasury_ledger", "amount", "direction = 'in'"),
    "treasury_ledger_outflow_amount": sum_table("sc_treasury_ledger", "amount", "direction = 'out'"),
    "fund_daily_snapshot_rows": count_table("sc_legacy_fund_daily_snapshot_fact"),
    "fund_daily_snapshot_with_project": count_table("sc_legacy_fund_daily_snapshot_fact", "project_id IS NOT NULL"),
    "fund_daily_snapshot_difference_amount": sum_table(
        "sc_legacy_fund_daily_snapshot_fact",
        "source_bank_system_difference",
    ),
    "fund_daily_line_rows": count_table("sc_legacy_fund_daily_line"),
    "fund_daily_line_active_rows": count_table("sc_legacy_fund_daily_line", "active"),
    "fund_daily_line_with_project": count_table("sc_legacy_fund_daily_line", "project_id IS NOT NULL"),
    "fund_daily_line_income_amount": sum_table("sc_legacy_fund_daily_line", "daily_income", "active"),
    "fund_daily_line_expense_amount": sum_table("sc_legacy_fund_daily_line", "daily_expense", "active"),
    "fund_daily_line_difference_amount": sum_table("sc_legacy_fund_daily_line", "bank_system_difference", "active"),
    "financing_loan_rows": count_table("sc_legacy_financing_loan_fact"),
    "financing_loan_with_project": count_table("sc_legacy_financing_loan_fact", "project_id IS NOT NULL"),
    "financing_loan_with_partner": count_table("sc_legacy_financing_loan_fact", "partner_id IS NOT NULL"),
    "financing_loan_amount": sum_table("sc_legacy_financing_loan_fact", "source_amount"),
    "fund_confirmation_rows": count_table("sc_legacy_fund_confirmation_line"),
    "fund_confirmation_with_project": count_table("sc_legacy_fund_confirmation_line", "project_id IS NOT NULL"),
    "fund_confirmation_current_actual": sum_table("sc_legacy_fund_confirmation_line", "current_actual_amount"),
}

distributions = {
    "treasury_by_source_kind": [
        {"source_kind": row[0], "direction": row[1], "rows": int(row[2]), "amount": float(row[3] or 0)}
        for row in rows(
            """
            SELECT source_kind, direction, COUNT(*), COALESCE(SUM(amount), 0)
            FROM sc_treasury_ledger
            GROUP BY source_kind, direction
            ORDER BY COUNT(*) DESC
            """
        )
    ] if table_exists("sc_treasury_ledger") else [],
    "financing_by_direction": [
        {"source_direction": row[0], "source_family": row[1], "rows": int(row[2]), "amount": float(row[3] or 0)}
        for row in rows(
            """
            SELECT source_direction, source_family, COUNT(*), COALESCE(SUM(source_amount), 0)
            FROM sc_legacy_financing_loan_fact
            GROUP BY source_direction, source_family
            ORDER BY COUNT(*) DESC
            """
        )
    ] if table_exists("sc_legacy_financing_loan_fact") else [],
}

samples = {
    "treasury_ledger": [
        {"id": row[0], "date": str(row[1] or ""), "direction": row[2], "amount": float(row[3] or 0), "source_kind": row[4]}
        for row in rows(
            """
            SELECT id, date, direction, amount, source_kind
            FROM sc_treasury_ledger
            ORDER BY date DESC NULLS LAST, id DESC
            LIMIT 5
            """
        )
    ] if table_exists("sc_treasury_ledger") else [],
    "fund_daily_line": [
        {
            "id": row[0],
            "document_date": str(row[1] or ""),
            "project_id": row[2],
            "account_name": row[3],
            "daily_income": float(row[4] or 0),
            "daily_expense": float(row[5] or 0),
        }
        for row in rows(
            """
            SELECT id, document_date, project_id, account_name, daily_income, daily_expense
            FROM sc_legacy_fund_daily_line
            WHERE active
            ORDER BY document_date DESC NULLS LAST, id DESC
            LIMIT 5
            """
        )
    ] if table_exists("sc_legacy_fund_daily_line") else [],
    "financing_loan": [
        {"id": row[0], "document_date": str(row[1] or ""), "source_direction": row[2], "amount": float(row[3] or 0)}
        for row in rows(
            """
            SELECT id, document_date, source_direction, source_amount
            FROM sc_legacy_financing_loan_fact
            ORDER BY document_date DESC NULLS LAST, id DESC
            LIMIT 5
            """
        )
    ] if table_exists("sc_legacy_financing_loan_fact") else [],
}

gaps = {
    "missing_treasury_ledger_surface": counts["treasury_ledger_rows"] == 0,
    "missing_fund_daily_snapshot_surface": counts["fund_daily_snapshot_rows"] == 0,
    "missing_fund_daily_line_surface": counts["fund_daily_line_rows"] == 0,
    "missing_financing_loan_surface": counts["financing_loan_rows"] == 0,
    "fund_daily_line_project_link_gap": counts["fund_daily_line_rows"] > 0 and counts["fund_daily_line_with_project"] == 0,
    "financing_loan_project_link_gap": counts["financing_loan_rows"] > 0 and counts["financing_loan_with_project"] == 0,
}
failing_gaps = [key for key, value in gaps.items() if value]
decision = "history_treasury_reconciliation_ready" if not failing_gaps else "history_treasury_reconciliation_gap"

payload = {
    "status": "PASS",
    "mode": "history_treasury_reconciliation_probe",
    "database": env.cr.dbname,  # noqa: F821
    "db_writes": 0,
    "counts": counts,
    "distributions": distributions,
    "samples": samples,
    "gaps": gaps,
    "decision": decision,
}

write_json(OUTPUT_JSON, payload)
write_report(OUTPUT_REPORT, payload)
print(
    "HISTORY_TREASURY_RECONCILIATION_PROBE="
    + json.dumps(
        {
            "status": payload["status"],
            "database": payload["database"],
            "decision": decision,
            "gap_count": len(failing_gaps),
            "treasury_ledger_rows": counts["treasury_ledger_rows"],
            "fund_daily_line_rows": counts["fund_daily_line_rows"],
            "financing_loan_rows": counts["financing_loan_rows"],
            "db_writes": 0,
        },
        ensure_ascii=False,
        sort_keys=True,
    )
)
