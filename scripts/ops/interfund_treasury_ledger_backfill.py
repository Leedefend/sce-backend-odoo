# -*- coding: utf-8 -*-
"""Backfill historical interfund cash-flow facts into sc.treasury.ledger.

Default mode is dry-run. Set APPLY=1 to write rows.
"""

from __future__ import annotations

import json
import os
import sys
import traceback


EXPECTED_SQL = """
WITH expected AS (
    SELECT
        f.source_model,
        f.source_res_id,
        f.source_record_name,
        f.movement_type,
        f.source_menu_hint,
        f.document_date,
        f.company_id,
        f.currency_id,
        f.partner_id,
        f.amount,
        f.source_project_id AS project_id,
        'out'::varchar AS direction,
        'source_project_outflow'::varchar AS backfill_role
    FROM sc_interfund_movement_fact f
    WHERE f.amount > 0
      AND f.source_project_id IS NOT NULL
      AND f.movement_type IN (
            'project_to_project_transfer',
            'project_to_company_transfer',
            'project_to_contractor_borrow',
            'project_to_company_repay'
      )
    UNION ALL
    SELECT
        f.source_model,
        f.source_res_id,
        f.source_record_name,
        f.movement_type,
        f.source_menu_hint,
        f.document_date,
        f.company_id,
        f.currency_id,
        f.partner_id,
        f.amount,
        f.target_project_id AS project_id,
        'in'::varchar AS direction,
        'target_project_inflow'::varchar AS backfill_role
    FROM sc_interfund_movement_fact f
    WHERE f.amount > 0
      AND f.target_project_id IS NOT NULL
      AND f.movement_type IN (
            'project_to_project_transfer',
            'company_to_project_transfer',
            'company_to_project_borrow',
            'contractor_to_project_repay'
      )
),
matched AS (
    SELECT
        e.*,
        l.id AS ledger_id
    FROM expected e
    LEFT JOIN sc_treasury_ledger l
      ON l.source_model = e.source_model
     AND l.source_res_id = e.source_res_id
     AND l.project_id = e.project_id
     AND l.direction = e.direction
     AND l.source_kind = 'interfund'
     AND l.state != 'void'
)
"""


def _fetchall_dict(query, params=None):
    env.cr.execute(query, params or {})  # noqa: F821
    columns = [column.name for column in env.cr.description]  # noqa: F821
    return [dict(zip(columns, row)) for row in env.cr.fetchall()]  # noqa: F821


def _fetchone_dict(query, params=None):
    rows = _fetchall_dict(query, params)
    return rows[0] if rows else {}


def _summary():
    return _fetchone_dict(
        EXPECTED_SQL
        + """
        SELECT
            COUNT(*)::integer AS expected_ledger_entry_count,
            COUNT(*) FILTER (WHERE ledger_id IS NOT NULL)::integer AS existing_ledger_entry_count,
            COUNT(*) FILTER (WHERE ledger_id IS NULL)::integer AS missing_ledger_entry_count,
            COALESCE(SUM(amount), 0.0) AS expected_ledger_amount,
            COALESCE(SUM(amount) FILTER (WHERE ledger_id IS NULL), 0.0) AS missing_ledger_amount
        FROM matched
        """
    )


def _missing_rows():
    return _fetchall_dict(
        EXPECTED_SQL
        + """
        SELECT
            source_model,
            source_res_id,
            source_record_name,
            movement_type,
            source_menu_hint,
            document_date,
            company_id,
            currency_id,
            partner_id,
            amount,
            project_id,
            direction,
            backfill_role
        FROM matched
        WHERE ledger_id IS NULL
        ORDER BY source_model, source_res_id, project_id, direction
        """
    )


def _unsafe_summary():
    return _fetchone_dict(
        """
        SELECT
            COUNT(*) FILTER (WHERE movement_type = 'same_project_account_transfer')::integer AS same_project_fact_count,
            COALESCE(SUM(amount) FILTER (WHERE movement_type = 'same_project_account_transfer'), 0.0) AS same_project_amount,
            COUNT(*) FILTER (WHERE movement_type = 'unclassified_account_transfer')::integer AS unclassified_fact_count,
            COALESCE(SUM(amount) FILTER (WHERE movement_type = 'unclassified_account_transfer'), 0.0) AS unclassified_amount,
            COUNT(*) FILTER (WHERE amount <= 0)::integer AS non_positive_fact_count,
            COALESCE(SUM(amount) FILTER (WHERE amount <= 0), 0.0) AS non_positive_amount
        FROM sc_interfund_movement_fact
        """
    )


def _assert_apply_allowed(apply):
    if not apply:
        return
    db_name = env.cr.dbname  # noqa: F821
    allowed = db_name in {"sc_demo", "sc_test"} or db_name.startswith(("sc_demo_", "sc_test_"))
    if allowed:
        return
    if os.environ.get("INTERFUND_TREASURY_BACKFILL_ALLOW_DB") == "1":
        return
    raise RuntimeError(
        "APPLY=1 is only allowed for sc_demo/sc_test unless INTERFUND_TREASURY_BACKFILL_ALLOW_DB=1 is set; db=%s"
        % db_name
    )


def _create_ledgers(rows):
    Ledger = env["sc.treasury.ledger"].sudo()  # noqa: F821
    Project = env["project.project"].sudo()  # noqa: F821
    Partner = env["res.partner"].sudo()  # noqa: F821
    Currency = env["res.currency"].sudo()  # noqa: F821
    created = 0
    skipped = 0
    for row in rows:
        project = Project.browse(row["project_id"]).exists()
        if not project:
            skipped += 1
            continue
        partner = Partner.browse(row["partner_id"]).exists() if row.get("partner_id") else False
        currency = Currency.browse(row["currency_id"]).exists() if row.get("currency_id") else False
        source = env[row["source_model"]].sudo().browse(row["source_res_id"]).exists()  # noqa: F821
        if not source:
            skipped += 1
            continue
        ledger = Ledger._ensure_interfund_ledger(
            source,
            project=project,
            partner=partner,
            direction=row["direction"],
            amount=row["amount"],
            date=row["document_date"],
            currency=currency,
            note="backfill:interfund_treasury_ledger:%s:%s" % (row["movement_type"], row["backfill_role"]),
        )
        if ledger:
            created += 1
    return created, skipped


def main():
    apply = os.environ.get("APPLY") == "1"
    _assert_apply_allowed(apply)

    before = _summary()
    unsafe = _unsafe_summary()
    rows = _missing_rows()
    created = 0
    skipped = 0
    if apply:
        created, skipped = _create_ledgers(rows)
        env.cr.commit()  # noqa: F821
    after = _summary()
    status = "PASS"
    failures = []
    if apply and int(after.get("missing_ledger_entry_count") or 0) != 0:
        status = "FAIL"
        failures.append("missing_ledger_entry_count_after_apply=%s" % after.get("missing_ledger_entry_count"))
    result = {
        "operation": "interfund_treasury_ledger_backfill",
        "status": status,
        "database": env.cr.dbname,  # noqa: F821
        "apply": apply,
        "before": before,
        "after": after,
        "unsafe_or_non_backfillable": unsafe,
        "candidate_rows": len(rows),
        "created_or_existing_rows": created,
        "skipped_rows": skipped,
        "failures": failures,
    }
    print("INTERFUND_TREASURY_LEDGER_BACKFILL: %s" % json.dumps(result, ensure_ascii=False, sort_keys=True, default=str))
    return 0 if status == "PASS" else 1


try:
    sys.exit(main())
except Exception as err:
    env.cr.rollback()  # noqa: F821
    result = {
        "operation": "interfund_treasury_ledger_backfill",
        "status": "FAIL",
        "database": env.cr.dbname,  # noqa: F821
        "apply": os.environ.get("APPLY") == "1",
        "error": str(err),
        "traceback": traceback.format_exc(),
    }
    print("INTERFUND_TREASURY_LEDGER_BACKFILL: %s" % json.dumps(result, ensure_ascii=False, sort_keys=True, default=str))
    sys.exit(1)
