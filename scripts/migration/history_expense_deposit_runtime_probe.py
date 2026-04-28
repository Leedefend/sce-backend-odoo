#!/usr/bin/env python3
"""Read-only probe for historical expense reimbursement and deposit surfaces."""

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
        "# History Expense Deposit Runtime Probe v1",
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
OUTPUT_JSON = ARTIFACT_ROOT / "history_expense_deposit_runtime_probe_result_v1.json"
OUTPUT_REPORT = ARTIFACT_ROOT / "history_expense_deposit_runtime_probe_report_v1.md"

counts = {
    "expense_deposit_rows": count_table("sc_legacy_expense_deposit_fact"),
    "expense_deposit_with_project": count_table("sc_legacy_expense_deposit_fact", "project_id IS NOT NULL"),
    "expense_deposit_with_partner": count_table("sc_legacy_expense_deposit_fact", "partner_id IS NOT NULL"),
    "expense_deposit_amount": sum_table("sc_legacy_expense_deposit_fact", "source_amount"),
    "expense_deposit_outflow_rows": count_table("sc_legacy_expense_deposit_fact", "direction = 'outflow'"),
    "expense_deposit_refund_rows": count_table("sc_legacy_expense_deposit_fact", "direction = 'inflow_or_refund'"),
    "expense_reimbursement_line_rows": count_table("sc_legacy_expense_reimbursement_line"),
    "expense_reimbursement_line_active_rows": count_table("sc_legacy_expense_reimbursement_line", "active"),
    "expense_reimbursement_line_with_project": count_table(
        "sc_legacy_expense_reimbursement_line",
        "project_id IS NOT NULL",
    ),
    "expense_reimbursement_line_with_payee": count_table(
        "sc_legacy_expense_reimbursement_line",
        "payee IS NOT NULL AND payee <> ''",
    ),
    "expense_reimbursement_line_amount": sum_table("sc_legacy_expense_reimbursement_line", "amount", "active"),
    "expense_reimbursement_line_approved_amount": sum_table(
        "sc_legacy_expense_reimbursement_line",
        "approved_amount",
        "active",
    ),
}

distributions = {
    "expense_deposit_by_family": [
        {"source_family": row[0], "direction": row[1], "rows": int(row[2]), "amount": float(row[3] or 0)}
        for row in rows(
            """
            SELECT source_family, direction, COUNT(*), COALESCE(SUM(source_amount), 0)
            FROM sc_legacy_expense_deposit_fact
            GROUP BY source_family, direction
            ORDER BY COUNT(*) DESC
            """
        )
    ] if table_exists("sc_legacy_expense_deposit_fact") else [],
    "reimbursement_by_finance_type": [
        {"finance_type": row[0], "rows": int(row[1]), "amount": float(row[2] or 0), "approved_amount": float(row[3] or 0)}
        for row in rows(
            """
            SELECT finance_type, COUNT(*), COALESCE(SUM(amount), 0), COALESCE(SUM(approved_amount), 0)
            FROM sc_legacy_expense_reimbursement_line
            WHERE active
            GROUP BY finance_type
            ORDER BY COUNT(*) DESC
            LIMIT 20
            """
        )
    ] if table_exists("sc_legacy_expense_reimbursement_line") else [],
}

samples = {
    "expense_deposit": [
        {
            "id": row[0],
            "document_date": str(row[1] or ""),
            "document_no": row[2],
            "source_family": row[3],
            "direction": row[4],
            "project_id": row[5],
            "partner_id": row[6],
            "amount": float(row[7] or 0),
        }
        for row in rows(
            """
            SELECT id, document_date, document_no, source_family, direction, project_id, partner_id, source_amount
            FROM sc_legacy_expense_deposit_fact
            ORDER BY document_date DESC NULLS LAST, id DESC
            LIMIT 5
            """
        )
    ] if table_exists("sc_legacy_expense_deposit_fact") else [],
    "expense_reimbursement_line": [
        {
            "id": row[0],
            "document_date": row[1],
            "document_no": row[2],
            "project_id": row[3],
            "applicant_name": row[4],
            "finance_type": row[5],
            "amount": float(row[6] or 0),
            "approved_amount": float(row[7] or 0),
        }
        for row in rows(
            """
            SELECT id, document_date, document_no, project_id, applicant_name, finance_type, amount, approved_amount
            FROM sc_legacy_expense_reimbursement_line
            WHERE active
            ORDER BY document_date DESC NULLS LAST, id DESC
            LIMIT 5
            """
        )
    ] if table_exists("sc_legacy_expense_reimbursement_line") else [],
}

gaps = {
    "missing_expense_deposit_surface": counts["expense_deposit_rows"] == 0,
    "missing_expense_reimbursement_line_surface": counts["expense_reimbursement_line_rows"] == 0,
    "expense_deposit_project_link_gap": counts["expense_deposit_rows"] > 0 and counts["expense_deposit_with_project"] == 0,
    "expense_reimbursement_line_project_link_gap": (
        counts["expense_reimbursement_line_rows"] > 0
        and counts["expense_reimbursement_line_with_project"] == 0
    ),
}
failing_gaps = [key for key, value in gaps.items() if value]
decision = "history_expense_deposit_runtime_ready" if not failing_gaps else "history_expense_deposit_runtime_gap"

payload = {
    "status": "PASS",
    "mode": "history_expense_deposit_runtime_probe",
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
    "HISTORY_EXPENSE_DEPOSIT_RUNTIME_PROBE="
    + json.dumps(
        {
            "status": payload["status"],
            "database": payload["database"],
            "decision": decision,
            "gap_count": len(failing_gaps),
            "expense_deposit_rows": counts["expense_deposit_rows"],
            "expense_reimbursement_line_rows": counts["expense_reimbursement_line_rows"],
            "db_writes": 0,
        },
        ensure_ascii=False,
        sort_keys=True,
    )
)
