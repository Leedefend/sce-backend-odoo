#!/usr/bin/env python3
"""Read-only probe for historical invoice, tax, deduction, and fund-confirmation surfaces."""

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


def scalar(sql: str, params: list[object] | None = None) -> float:
    env.cr.execute(sql, params or [])  # noqa: F821
    return env.cr.fetchone()[0] or 0  # noqa: F821


def fetchall(sql: str, params: list[object] | None = None) -> list[tuple[object, ...]]:
    env.cr.execute(sql, params or [])  # noqa: F821
    return env.cr.fetchall()  # noqa: F821


ARTIFACT_ROOT = resolve_artifact_root()
OUTPUT_JSON = ARTIFACT_ROOT / "history_invoice_tax_runtime_probe_result_v1.json"
OUTPUT_REPORT = ARTIFACT_ROOT / "history_invoice_tax_runtime_probe_report_v1.md"

counts = {
    "invoice_registration_rows": int(scalar("SELECT COUNT(*) FROM sc_legacy_invoice_registration_line")),
    "invoice_registration_active_rows": int(scalar("SELECT COUNT(*) FROM sc_legacy_invoice_registration_line WHERE active")),
    "invoice_registration_with_project": int(scalar("SELECT COUNT(*) FROM sc_legacy_invoice_registration_line WHERE project_id IS NOT NULL")),
    "invoice_registration_with_partner": int(scalar("SELECT COUNT(*) FROM sc_legacy_invoice_registration_line WHERE partner_id IS NOT NULL")),
    "invoice_registration_amount_total": float(scalar("SELECT COALESCE(SUM(amount_total), 0) FROM sc_legacy_invoice_registration_line")),
    "invoice_registration_tax_amount": float(scalar("SELECT COALESCE(SUM(tax_amount), 0) FROM sc_legacy_invoice_registration_line")),
    "invoice_tax_fact_rows": int(scalar("SELECT COUNT(*) FROM sc_legacy_invoice_tax_fact")),
    "invoice_tax_source_amount": float(scalar("SELECT COALESCE(SUM(source_amount), 0) FROM sc_legacy_invoice_tax_fact")),
    "invoice_tax_source_tax_amount": float(scalar("SELECT COALESCE(SUM(source_tax_amount), 0) FROM sc_legacy_invoice_tax_fact")),
    "deduction_adjustment_rows": int(scalar("SELECT COUNT(*) FROM sc_legacy_deduction_adjustment_line")),
    "deduction_adjustment_with_project": int(scalar("SELECT COUNT(*) FROM sc_legacy_deduction_adjustment_line WHERE project_id IS NOT NULL")),
    "deduction_adjustment_current_actual": float(scalar("SELECT COALESCE(SUM(current_actual_amount), 0) FROM sc_legacy_deduction_adjustment_line")),
    "fund_confirmation_rows": int(scalar("SELECT COUNT(*) FROM sc_legacy_fund_confirmation_line")),
    "fund_confirmation_with_project": int(scalar("SELECT COUNT(*) FROM sc_legacy_fund_confirmation_line WHERE project_id IS NOT NULL")),
    "fund_confirmation_current_actual": float(scalar("SELECT COALESCE(SUM(current_actual_amount), 0) FROM sc_legacy_fund_confirmation_line")),
}

distributions = {
    "invoice_type_top": [
        {"invoice_type": row[0], "rows": int(row[1]), "amount_total": float(row[2] or 0)}
        for row in fetchall(
            """
            SELECT invoice_type, COUNT(*), COALESCE(SUM(amount_total), 0)
            FROM sc_legacy_invoice_registration_line
            GROUP BY invoice_type
            ORDER BY COUNT(*) DESC
            LIMIT 20
            """
        )
    ],
    "invoice_tax_by_direction": [
        {"direction": row[0], "source_family": row[1], "rows": int(row[2]), "tax_amount": float(row[3] or 0)}
        for row in fetchall(
            """
            SELECT direction, source_family, COUNT(*), COALESCE(SUM(source_tax_amount), 0)
            FROM sc_legacy_invoice_tax_fact
            GROUP BY direction, source_family
            ORDER BY COUNT(*) DESC
            """
        )
    ],
}

samples = {
    "invoice_registration": [
        {"id": row[0], "invoice_no": row[1], "project_id": row[2], "partner_id": row[3], "amount_total": float(row[4] or 0)}
        for row in fetchall(
            """
            SELECT id, invoice_no, project_id, partner_id, amount_total
            FROM sc_legacy_invoice_registration_line
            ORDER BY invoice_date DESC NULLS LAST, id DESC
            LIMIT 5
            """
        )
    ],
    "invoice_tax": [
        {"id": row[0], "document_no": row[1], "direction": row[2], "source_amount": float(row[3] or 0), "tax_amount": float(row[4] or 0)}
        for row in fetchall(
            """
            SELECT id, document_no, direction, source_amount, source_tax_amount
            FROM sc_legacy_invoice_tax_fact
            ORDER BY document_date DESC NULLS LAST, id DESC
            LIMIT 5
            """
        )
    ],
}

gaps = {
    "missing_invoice_registration_surface": counts["invoice_registration_rows"] == 0,
    "missing_invoice_tax_surface": counts["invoice_tax_fact_rows"] == 0,
    "missing_deduction_adjustment_surface": counts["deduction_adjustment_rows"] == 0,
    "missing_fund_confirmation_surface": counts["fund_confirmation_rows"] == 0,
}
failing_gaps = [key for key, value in gaps.items() if value]
decision = "history_invoice_tax_runtime_ready" if not failing_gaps else "history_invoice_tax_runtime_gap"

payload = {
    "status": "PASS",
    "mode": "history_invoice_tax_runtime_probe",
    "database": env.cr.dbname,  # noqa: F821
    "db_writes": 0,
    "counts": counts,
    "distributions": distributions,
    "samples": samples,
    "gaps": gaps,
    "decision": decision,
}

write_json(OUTPUT_JSON, payload)
write_json(ARTIFACT_ROOT / "history_invoice_tax_runtime_probe_report_v1.json", payload)
print(
    "HISTORY_INVOICE_TAX_RUNTIME_PROBE="
    + json.dumps(
        {
            "status": payload["status"],
            "database": payload["database"],
            "decision": decision,
            "gap_count": len(failing_gaps),
            "invoice_registration_rows": counts["invoice_registration_rows"],
            "invoice_tax_fact_rows": counts["invoice_tax_fact_rows"],
            "db_writes": 0,
        },
        ensure_ascii=False,
        sort_keys=True,
    )
)
