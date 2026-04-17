"""Sync imported project lifecycle from downstream business facts.

Run through Odoo shell:
SYNC_MODE=check odoo shell -d sc_demo -c /var/lib/odoo/odoo.conf < /mnt/scripts/migration/project_continuity_downstream_fact_state_sync.py
SYNC_MODE=write odoo shell -d sc_demo -c /var/lib/odoo/odoo.conf < /mnt/scripts/migration/project_continuity_downstream_fact_state_sync.py
"""

from __future__ import annotations

import csv
import json
import os
from pathlib import Path


RUN_ID = "ITER-2026-04-17-PROJECT-CONTINUITY-TRANSITION-GUARD-RECOVERY"
TARGET_DB = "sc_demo"
EXPECTED_TOTAL = 701
OUTPUT_JSON = Path("/mnt/artifacts/migration/project_continuity_downstream_fact_state_sync_result_v1.json")
SNAPSHOT_CSV = Path("/mnt/artifacts/migration/project_continuity_downstream_fact_state_sync_snapshot_v1.csv")
ROLLBACK_CSV = Path("/mnt/artifacts/migration/project_continuity_downstream_fact_state_sync_rollback_v1.csv")


def clean(value):
    return ("" if value is None else str(value)).strip()


def fetchall_dict(query, params=None):
    env.cr.execute(query, params or ())  # noqa: F821
    columns = [item[0] for item in env.cr.description]  # noqa: F821
    return [dict(zip(columns, row)) for row in env.cr.fetchall()]  # noqa: F821


def write_json(path, payload):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_csv(path, fieldnames, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def target_rows():
    return fetchall_dict(
        """
        WITH c AS (SELECT project_id, count(*) contract_count FROM construction_contract GROUP BY project_id),
             p AS (SELECT project_id, count(*) request_count FROM payment_request GROUP BY project_id),
             pl AS (SELECT project_id, count(*) ledger_count FROM payment_ledger GROUP BY project_id),
             ri AS (SELECT project_id, count(*) receipt_count FROM sc_legacy_receipt_income_fact GROUP BY project_id),
             ed AS (SELECT project_id, count(*) expense_count FROM sc_legacy_expense_deposit_fact GROUP BY project_id),
             it AS (SELECT project_id, count(*) invoice_count FROM sc_legacy_invoice_tax_fact GROUP BY project_id),
             fl AS (SELECT project_id, count(*) loan_count FROM sc_legacy_financing_loan_fact GROUP BY project_id),
             fd AS (SELECT project_id, count(*) fund_count FROM sc_legacy_fund_daily_snapshot_fact GROUP BY project_id)
        SELECT pp.id,
               pp.name::text AS name,
               pp.legacy_project_id,
               pp.lifecycle_state,
               pp.phase_key,
               pp.sc_execution_state,
               pp.stage_id,
               pp.owner_id,
               pp.location,
               pp.boq_line_count,
               COALESCE(c.contract_count, 0) AS contract_count,
               COALESCE(p.request_count, 0) AS request_count,
               COALESCE(pl.ledger_count, 0) AS ledger_count,
               COALESCE(ri.receipt_count, 0) AS receipt_count,
               COALESCE(ed.expense_count, 0) AS expense_count,
               COALESCE(it.invoice_count, 0) AS invoice_count,
               COALESCE(fl.loan_count, 0) AS loan_count,
               COALESCE(fd.fund_count, 0) AS fund_count
          FROM project_project pp
          LEFT JOIN c ON c.project_id = pp.id
          LEFT JOIN p ON p.project_id = pp.id
          LEFT JOIN pl ON pl.project_id = pp.id
          LEFT JOIN ri ON ri.project_id = pp.id
          LEFT JOIN ed ON ed.project_id = pp.id
          LEFT JOIN it ON it.project_id = pp.id
          LEFT JOIN fl ON fl.project_id = pp.id
          LEFT JOIN fd ON fd.project_id = pp.id
         WHERE COALESCE(pp.legacy_project_id, '') <> ''
           AND (
                COALESCE(c.contract_count, 0) > 0
             OR COALESCE(p.request_count, 0) > 0
             OR COALESCE(pl.ledger_count, 0) > 0
             OR COALESCE(ri.receipt_count, 0) > 0
             OR COALESCE(ed.expense_count, 0) > 0
             OR COALESCE(it.invoice_count, 0) > 0
             OR COALESCE(fl.loan_count, 0) > 0
             OR COALESCE(fd.fund_count, 0) > 0
           )
         ORDER BY pp.id
        """
    )


def main():
    mode = clean(os.environ.get("SYNC_MODE") or "check")
    if mode not in {"check", "write"}:
        raise RuntimeError({"invalid_sync_mode": mode})
    if env.cr.dbname != TARGET_DB:  # noqa: F821
        raise RuntimeError({"database_not_sc_demo": env.cr.dbname})  # noqa: F821

    rows = target_rows()
    if len(rows) != EXPECTED_TOTAL:
        raise RuntimeError({"target_count_drift": len(rows), "expected": EXPECTED_TOTAL})

    snapshot_fields = [
        "id",
        "legacy_project_id",
        "name",
        "lifecycle_state",
        "phase_key",
        "sc_execution_state",
        "stage_id",
        "owner_id",
        "location",
        "boq_line_count",
        "contract_count",
        "request_count",
        "ledger_count",
        "receipt_count",
        "expense_count",
        "invoice_count",
        "loan_count",
        "fund_count",
    ]
    snapshot_rows = [{field: clean(row.get(field)) for field in snapshot_fields} for row in rows]
    rollback_rows = [
        {
            "id": clean(row.get("id")),
            "legacy_project_id": clean(row.get("legacy_project_id")),
            "lifecycle_state": clean(row.get("lifecycle_state")),
            "phase_key": clean(row.get("phase_key")),
            "sc_execution_state": clean(row.get("sc_execution_state")),
            "stage_id": clean(row.get("stage_id")),
        }
        for row in rows
    ]

    needs_sync_ids = [
        int(row["id"])
        for row in rows
        if clean(row.get("lifecycle_state")) == "draft"
        and clean(row.get("phase_key")) == "initiation"
        and clean(row.get("sc_execution_state")) == "ready"
    ]
    already_synced = [
        int(row["id"])
        for row in rows
        if clean(row.get("lifecycle_state")) == "in_progress"
        and clean(row.get("phase_key")) == "execution"
        and clean(row.get("sc_execution_state")) == "in_progress"
    ]

    write_csv(SNAPSHOT_CSV, snapshot_fields, snapshot_rows)
    write_csv(
        ROLLBACK_CSV,
        ["id", "legacy_project_id", "lifecycle_state", "phase_key", "sc_execution_state", "stage_id"],
        rollback_rows,
    )

    if mode == "write" and needs_sync_ids:
        Project = env["project.project"].sudo().with_context(sc_imported_project_continuity_sync=True)  # noqa: F821
        projects = Project.browse(needs_sync_ids)
        projects.write({
            "lifecycle_state": "in_progress",
            "phase_key": "execution",
            "sc_execution_state": "in_progress",
        })
        env.cr.commit()  # noqa: F821

    result = {
        "run_id": RUN_ID,
        "mode": mode,
        "database": env.cr.dbname,  # noqa: F821
        "target_total": len(rows),
        "needs_sync_count": len(needs_sync_ids),
        "already_synced_count": len(already_synced),
        "written_count": len(needs_sync_ids) if mode == "write" else 0,
        "snapshot_csv": str(SNAPSHOT_CSV),
        "rollback_csv": str(ROLLBACK_CSV),
        "sample_ids": needs_sync_ids[:20],
    }
    write_json(OUTPUT_JSON, result)
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))


main()
