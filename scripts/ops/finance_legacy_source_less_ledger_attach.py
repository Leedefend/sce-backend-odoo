# -*- coding: utf-8 -*-
"""Attach exact source records to source-less legacy treasury ledger rows.

Default mode is dry-run. Set APPLY=1 to update rows. The script only writes
source_model/source_res_id on rows that pass the same one-to-one match rule used
by the reconciliation audit.
"""

from __future__ import annotations

import json
import os
import sys
import traceback


def _fetchall_dict(query, params=None):
    env.cr.execute(query, params or {})  # noqa: F821
    columns = [column.name for column in env.cr.description]  # noqa: F821
    return [dict(zip(columns, row)) for row in env.cr.fetchall()]  # noqa: F821


def _fetchone_dict(query, params=None):
    rows = _fetchall_dict(query, params)
    return rows[0] if rows else {}


def _assert_apply_allowed(apply):
    if not apply:
        return
    db_name = env.cr.dbname  # noqa: F821
    allowed = db_name in {"sc_demo", "sc_test"} or db_name.startswith(("sc_demo_", "sc_test_"))
    if allowed:
        return
    if os.environ.get("FINANCE_LEGACY_SOURCE_ATTACH_ALLOW_DB") == "1":
        return
    raise RuntimeError(
        "APPLY=1 is only allowed for sc_demo/sc_test unless FINANCE_LEGACY_SOURCE_ATTACH_ALLOW_DB=1 is set; db=%s"
        % db_name
    )


def _prepare_match_tables():
    env.cr.execute(  # noqa: F821
        """
        DROP TABLE IF EXISTS tmp_finance_legacy_source_attach_source_less;
        DROP TABLE IF EXISTS tmp_finance_legacy_source_attach_candidates;
        DROP TABLE IF EXISTS tmp_finance_legacy_source_attach_exact;
        DROP TABLE IF EXISTS tmp_finance_legacy_source_attach_exact_counts;
        DROP TABLE IF EXISTS tmp_finance_legacy_source_attach_safe;
        DROP TABLE IF EXISTS tmp_finance_legacy_source_attach_conflicts;
        DROP TABLE IF EXISTS tmp_finance_legacy_source_attach_attachable;

        CREATE TEMP TABLE tmp_finance_legacy_source_attach_source_less AS
        SELECT
            l.id AS ledger_id,
            l.name AS ledger_name,
            l.date AS ledger_date,
            l.project_id,
            l.partner_id,
            l.direction,
            l.source_kind,
            l.amount,
            l.currency_id,
            l.legacy_record_id,
            l.legacy_source_ref,
            l.note
        FROM sc_treasury_ledger l
        WHERE l.source_kind IN ('legacy_actual_outflow', 'legacy_receipt')
          AND COALESCE(l.source_model, '') = ''
          AND l.source_res_id IS NULL
          AND l.state != 'void';

        CREATE INDEX ON tmp_finance_legacy_source_attach_source_less(legacy_record_id);
        CREATE INDEX ON tmp_finance_legacy_source_attach_source_less(ledger_id);

        CREATE TEMP TABLE tmp_finance_legacy_source_attach_candidates AS
        SELECT
            'sc.payment.execution'::varchar AS source_model,
            e.id AS source_res_id,
            e.name AS source_record_name,
            e.legacy_record_id,
            e.project_id,
            e.partner_id,
            e.date_payment AS document_date,
            'out'::varchar AS direction,
            'legacy_actual_outflow'::varchar AS source_kind,
            COALESCE(e.paid_amount, 0.0) AS amount,
            e.currency_id,
            e.payment_family AS business_category
        FROM sc_payment_execution e
        WHERE e.source_origin = 'legacy'
          AND e.state = 'legacy_confirmed'
          AND COALESCE(e.legacy_record_id, '') != ''

        UNION ALL

        SELECT
            'sc.receipt.income'::varchar AS source_model,
            r.id AS source_res_id,
            r.name AS source_record_name,
            r.legacy_record_id,
            r.project_id,
            r.partner_id,
            r.date_receipt AS document_date,
            'in'::varchar AS direction,
            'legacy_receipt'::varchar AS source_kind,
            COALESCE(r.amount, 0.0) AS amount,
            r.currency_id,
            COALESCE(NULLIF(r.income_category, ''), NULLIF(r.legacy_receipt_type, ''), r.source_family) AS business_category
        FROM sc_receipt_income r
        WHERE r.source_origin = 'legacy'
          AND r.state = 'legacy_confirmed'
          AND COALESCE(r.legacy_record_id, '') != ''

        UNION ALL

        SELECT
            'sc.expense.claim'::varchar AS source_model,
            c.id AS source_res_id,
            c.name AS source_record_name,
            c.legacy_record_id,
            c.project_id,
            c.partner_id,
            c.date_claim AS document_date,
            CASE WHEN c.direction = 'inflow' THEN 'in' ELSE 'out' END::varchar AS direction,
            CASE WHEN c.direction = 'inflow' THEN 'legacy_receipt' ELSE 'legacy_actual_outflow' END::varchar AS source_kind,
            COALESCE(c.approved_amount, c.amount, 0.0) AS amount,
            c.currency_id,
            COALESCE(NULLIF(c.expense_type, ''), c.claim_type) AS business_category
        FROM sc_expense_claim c
        WHERE c.source_origin = 'legacy'
          AND c.state = 'legacy_confirmed'
          AND COALESCE(c.legacy_record_id, '') != '';

        CREATE INDEX ON tmp_finance_legacy_source_attach_candidates(legacy_record_id);
        CREATE INDEX ON tmp_finance_legacy_source_attach_candidates(source_model, source_res_id);

        CREATE TEMP TABLE tmp_finance_legacy_source_attach_exact AS
        SELECT
            l.*,
            c.source_model,
            c.source_res_id,
            c.source_record_name,
            c.document_date,
            c.business_category
        FROM tmp_finance_legacy_source_attach_source_less l
        JOIN tmp_finance_legacy_source_attach_candidates c
          ON c.legacy_record_id = l.legacy_record_id
         AND c.project_id = l.project_id
         AND c.direction = l.direction
         AND c.source_kind = l.source_kind
         AND ABS(COALESCE(c.amount, 0.0) - COALESCE(l.amount, 0.0)) <= 0.01
         AND (
                COALESCE(c.currency_id, 0) = COALESCE(l.currency_id, 0)
             OR (c.currency_id IS NULL AND l.currency_id IS NOT NULL)
         );

        CREATE INDEX ON tmp_finance_legacy_source_attach_exact(ledger_id);
        CREATE INDEX ON tmp_finance_legacy_source_attach_exact(source_model, source_res_id, project_id, direction, source_kind);

        CREATE TEMP TABLE tmp_finance_legacy_source_attach_exact_counts AS
        SELECT ledger_id, COUNT(*)::integer AS exact_count
        FROM tmp_finance_legacy_source_attach_exact
        GROUP BY ledger_id;

        CREATE TEMP TABLE tmp_finance_legacy_source_attach_safe AS
        SELECT e.*
        FROM tmp_finance_legacy_source_attach_exact e
        JOIN tmp_finance_legacy_source_attach_exact_counts ec ON ec.ledger_id = e.ledger_id
        WHERE ec.exact_count = 1;

        CREATE INDEX ON tmp_finance_legacy_source_attach_safe(ledger_id);
        CREATE INDEX ON tmp_finance_legacy_source_attach_safe(source_model, source_res_id, project_id, direction, source_kind);

        CREATE TEMP TABLE tmp_finance_legacy_source_attach_conflicts AS
        SELECT se.*
        FROM tmp_finance_legacy_source_attach_safe se
        WHERE EXISTS (
            SELECT 1
            FROM sc_treasury_ledger existing
            WHERE existing.source_model = se.source_model
              AND existing.source_res_id = se.source_res_id
              AND existing.project_id = se.project_id
              AND existing.direction = se.direction
              AND existing.source_kind = se.source_kind
              AND existing.id != se.ledger_id
              AND existing.state != 'void'
        );

        CREATE INDEX ON tmp_finance_legacy_source_attach_conflicts(ledger_id);

        CREATE TEMP TABLE tmp_finance_legacy_source_attach_attachable AS
        SELECT se.*
        FROM tmp_finance_legacy_source_attach_safe se
        LEFT JOIN tmp_finance_legacy_source_attach_conflicts c ON c.ledger_id = se.ledger_id
        WHERE c.ledger_id IS NULL;

        CREATE INDEX ON tmp_finance_legacy_source_attach_attachable(ledger_id);
        CREATE INDEX ON tmp_finance_legacy_source_attach_attachable(source_kind, source_model);
        """
    )


def _summary():
    return _fetchone_dict(
        """
        SELECT
            (SELECT COUNT(*)::integer FROM tmp_finance_legacy_source_attach_source_less) AS source_less_legacy_ledger_count,
            (SELECT COUNT(*)::integer FROM tmp_finance_legacy_source_attach_exact_counts WHERE exact_count > 1) AS ambiguous_exact_count,
            (SELECT COUNT(*)::integer FROM tmp_finance_legacy_source_attach_safe) AS safe_exact_count,
            (SELECT COUNT(*)::integer FROM tmp_finance_legacy_source_attach_conflicts) AS conflict_count,
            (SELECT COUNT(*)::integer FROM tmp_finance_legacy_source_attach_attachable) AS attachable_count,
            (SELECT COALESCE(SUM(amount), 0.0) FROM tmp_finance_legacy_source_attach_attachable) AS attachable_amount,
            (
                SELECT COUNT(*)::integer
                FROM sc_treasury_ledger
                WHERE source_model IN ('sc.payment.execution', 'sc.receipt.income', 'sc.expense.claim')
                  AND source_res_id IS NOT NULL
                  AND source_kind IN ('legacy_actual_outflow', 'legacy_receipt')
                  AND state != 'void'
            ) AS source_linked_legacy_count
        """
    )


def _by_source():
    return _fetchall_dict(
        """
        SELECT
            source_kind,
            source_model,
            COUNT(*)::integer AS attachable_count,
            COALESCE(SUM(amount), 0.0) AS attachable_amount
        FROM tmp_finance_legacy_source_attach_attachable
        GROUP BY source_kind, source_model
        ORDER BY attachable_count DESC, source_kind, source_model
        """
    )


def _samples():
    return _fetchall_dict(
        """
        SELECT
            ledger_id,
            ledger_name,
            ledger_date,
            source_kind,
            direction,
            amount,
            legacy_record_id,
            source_model,
            source_res_id,
            source_record_name,
            project_id,
            partner_id
        FROM tmp_finance_legacy_source_attach_attachable
        ORDER BY ledger_id
        LIMIT 20
        """
    )


def _apply():
    env.cr.execute(  # noqa: F821
        """
        UPDATE sc_treasury_ledger ledger
           SET source_model = attachable.source_model,
               source_res_id = attachable.source_res_id,
               note = CASE
                   WHEN COALESCE(ledger.note, '') LIKE '%%[source_attach:legacy_treasury_exact]%%'
                       THEN ledger.note
                   ELSE COALESCE(ledger.note || ' ', '') || '[source_attach:legacy_treasury_exact]'
               END,
               write_uid = %s,
               write_date = NOW()
          FROM tmp_finance_legacy_source_attach_attachable attachable
         WHERE ledger.id = attachable.ledger_id
           AND COALESCE(ledger.source_model, '') = ''
           AND ledger.source_res_id IS NULL
        """,
        [env.uid],  # noqa: F821
    )
    return env.cr.rowcount  # noqa: F821


def main():
    apply = os.environ.get("APPLY") == "1"
    _assert_apply_allowed(apply)
    _prepare_match_tables()

    before = _summary()
    by_source_before = _by_source()
    samples_before = _samples()
    failures = []
    if int(before.get("ambiguous_exact_count") or 0) != 0:
        failures.append("ambiguous_exact_count=%s" % before.get("ambiguous_exact_count"))
    if int(before.get("conflict_count") or 0) != 0:
        failures.append("conflict_count=%s" % before.get("conflict_count"))

    updated_rows = 0
    if apply and not failures:
        updated_rows = _apply()
        env.cr.commit()  # noqa: F821
    if apply:
        _prepare_match_tables()
    after = _summary()
    if apply and not failures and updated_rows != int(before.get("attachable_count") or 0):
        failures.append("updated_rows=%s attachable_before=%s" % (updated_rows, before.get("attachable_count")))

    result = {
        "operation": "finance_legacy_source_less_ledger_attach",
        "status": "PASS" if not failures else "FAIL",
        "database": env.cr.dbname,  # noqa: F821
        "apply": apply,
        "before": before,
        "after": after,
        "by_source_before": by_source_before,
        "samples_before": samples_before,
        "updated_rows": updated_rows,
        "failures": failures,
        "policy": {
            "write_scope": "source-less sc.treasury.ledger legacy_actual_outflow/legacy_receipt rows with exact one-to-one formal source match",
            "write_fields": "source_model, source_res_id, note marker, write metadata only",
            "safe_attach_rule": "legacy_record_id + project_id + direction + source_kind + amount + currency; exact_count=1; no active source unique-key conflict",
            "db_write_guard": "APPLY=1 only on sc_demo/sc_test unless explicitly allowed",
        },
    }
    print("FINANCE_LEGACY_SOURCE_LESS_LEDGER_ATTACH: %s" % json.dumps(result, ensure_ascii=False, sort_keys=True, default=str))
    return 0 if not failures else 1


try:
    sys.exit(main())
except Exception as err:
    env.cr.rollback()  # noqa: F821
    result = {
        "operation": "finance_legacy_source_less_ledger_attach",
        "status": "FAIL",
        "database": env.cr.dbname,  # noqa: F821
        "apply": os.environ.get("APPLY") == "1",
        "error": str(err),
        "traceback": traceback.format_exc(),
    }
    print("FINANCE_LEGACY_SOURCE_LESS_LEDGER_ATTACH: %s" % json.dumps(result, ensure_ascii=False, sort_keys=True, default=str))
    sys.exit(1)
