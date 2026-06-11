# -*- coding: utf-8 -*-
"""Clear payment_request_id from source-linked legacy cashflow ledgers.

Legacy cashflow rows are traced through source_model/source_res_id. They must
not also look like payment.request generated runtime ledgers unless their source
is actually payment.request. Default mode is dry-run; set APPLY=1 to update.
"""

from __future__ import annotations

import json
import os
import sys
import traceback


SOURCE_MODELS = ("sc.payment.execution", "sc.receipt.income", "sc.expense.claim")
SOURCE_KINDS = ("legacy_actual_outflow", "legacy_receipt")


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
    if os.environ.get("FINANCE_LEGACY_LEDGER_BOUNDARY_ALLOW_DB") == "1":
        return
    raise RuntimeError(
        "APPLY=1 is only allowed for sc_demo/sc_test unless FINANCE_LEGACY_LEDGER_BOUNDARY_ALLOW_DB=1 is set; db=%s"
        % db_name
    )


def _summary():
    return _fetchone_dict(
        """
        SELECT
            COUNT(*)::integer AS legacy_source_linked_count,
            COUNT(*) FILTER (WHERE payment_request_id IS NOT NULL)::integer AS boundary_violation_count,
            COALESCE(SUM(amount) FILTER (WHERE payment_request_id IS NOT NULL), 0.0) AS boundary_violation_amount
        FROM sc_treasury_ledger
        WHERE source_model IN %(source_models)s
          AND source_res_id IS NOT NULL
          AND source_kind IN %(source_kinds)s
          AND state != 'void'
        """,
        {"source_models": SOURCE_MODELS, "source_kinds": SOURCE_KINDS},
    )


def _by_source():
    return _fetchall_dict(
        """
        SELECT
            source_model,
            source_kind,
            direction,
            COUNT(*) FILTER (WHERE payment_request_id IS NOT NULL)::integer AS boundary_violation_count,
            COALESCE(SUM(amount) FILTER (WHERE payment_request_id IS NOT NULL), 0.0) AS boundary_violation_amount
        FROM sc_treasury_ledger
        WHERE source_model IN %(source_models)s
          AND source_res_id IS NOT NULL
          AND source_kind IN %(source_kinds)s
          AND state != 'void'
        GROUP BY source_model, source_kind, direction
        HAVING COUNT(*) FILTER (WHERE payment_request_id IS NOT NULL) > 0
        ORDER BY boundary_violation_count DESC, source_model, source_kind, direction
        """,
        {"source_models": SOURCE_MODELS, "source_kinds": SOURCE_KINDS},
    )


def _samples():
    return _fetchall_dict(
        """
        SELECT
            id,
            name,
            source_model,
            source_res_id,
            source_kind,
            direction,
            amount,
            project_id,
            payment_request_id
        FROM sc_treasury_ledger
        WHERE source_model IN %(source_models)s
          AND source_res_id IS NOT NULL
          AND source_kind IN %(source_kinds)s
          AND state != 'void'
          AND payment_request_id IS NOT NULL
        ORDER BY id
        LIMIT 20
        """,
        {"source_models": SOURCE_MODELS, "source_kinds": SOURCE_KINDS},
    )


def _apply():
    env.cr.execute(  # noqa: F821
        """
        UPDATE sc_treasury_ledger
           SET payment_request_id = NULL,
               note = CASE
                   WHEN COALESCE(note, '') LIKE '%%[boundary:legacy_source_no_payment_request]%%'
                       THEN note
                   ELSE COALESCE(note || ' ', '') || '[boundary:legacy_source_no_payment_request]'
               END,
               write_uid = %(uid)s,
               write_date = NOW()
         WHERE source_model IN %(source_models)s
           AND source_res_id IS NOT NULL
           AND source_kind IN %(source_kinds)s
           AND state != 'void'
           AND payment_request_id IS NOT NULL
        """,
        {"source_models": SOURCE_MODELS, "source_kinds": SOURCE_KINDS, "uid": env.uid},  # noqa: F821
    )
    return env.cr.rowcount  # noqa: F821


def main():
    apply = os.environ.get("APPLY") == "1"
    _assert_apply_allowed(apply)
    before = _summary()
    by_source_before = _by_source()
    samples_before = _samples()
    updated_rows = 0
    if apply:
        updated_rows = _apply()
        env.cr.commit()  # noqa: F821
    after = _summary()
    failures = []
    if apply and int(after.get("boundary_violation_count") or 0) != 0:
        failures.append("boundary_violation_count_after_apply=%s" % after.get("boundary_violation_count"))
    result = {
        "operation": "finance_legacy_source_linked_ledger_payment_request_boundary",
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
            "scope": "source-linked legacy sc.treasury.ledger rows for payment execution, receipt income, and expense claim",
            "write_fields": "payment_request_id, note marker, write metadata only",
            "boundary": "legacy cashflow source is source_model/source_res_id; payment_request_id stays empty unless the ledger source is a real payment.request completion",
            "db_write_guard": "APPLY=1 only on sc_demo/sc_test unless explicitly allowed",
        },
    }
    print("FINANCE_LEGACY_SOURCE_LINKED_LEDGER_PAYMENT_REQUEST_BOUNDARY: %s" % json.dumps(result, ensure_ascii=False, sort_keys=True, default=str))
    return 0 if not failures else 1


try:
    sys.exit(main())
except Exception as err:
    env.cr.rollback()  # noqa: F821
    result = {
        "operation": "finance_legacy_source_linked_ledger_payment_request_boundary",
        "status": "FAIL",
        "database": env.cr.dbname,  # noqa: F821
        "apply": os.environ.get("APPLY") == "1",
        "error": str(err),
        "traceback": traceback.format_exc(),
    }
    print("FINANCE_LEGACY_SOURCE_LINKED_LEDGER_PAYMENT_REQUEST_BOUNDARY: %s" % json.dumps(result, ensure_ascii=False, sort_keys=True, default=str))
    sys.exit(1)
