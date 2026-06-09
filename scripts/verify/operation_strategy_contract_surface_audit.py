# -*- coding: utf-8 -*-
"""Audit stored operation strategy and contract number business surfaces.

Run inside Odoo shell:
    odoo shell -d sc_demo < scripts/verify/operation_strategy_contract_surface_audit.py
"""

import json
import sys
import traceback


STRATEGY_TARGETS = (
    ("sc_general_contract", "project_id", "sc.general.contract"),
    ("sc_fund_account", "project_id", "sc.fund.account"),
    ("sc_treasury_reconciliation", "project_id", "sc.treasury.reconciliation"),
)


def _fetchall(sql, params=None):
    env.cr.execute(sql, params or [])  # noqa: F821
    names = [desc[0] for desc in env.cr.description]  # noqa: F821
    return [dict(zip(names, row)) for row in env.cr.fetchall()]  # noqa: F821


def _scalar(sql, params=None):
    env.cr.execute(sql, params or [])  # noqa: F821
    row = env.cr.fetchone()  # noqa: F821
    return row[0] if row else None


def main():
    failures = []
    strategy = {}
    for table, project_column, model in STRATEGY_TARGETS:
        mismatch_rows = _fetchall(
            """
            SELECT target.id, target.%s AS project_id, target.operation_strategy AS stored_strategy,
                   project.operation_strategy AS project_strategy
              FROM %s AS target
              JOIN project_project AS project ON project.id = target.%s
             WHERE COALESCE(target.operation_strategy, '') IS DISTINCT FROM COALESCE(project.operation_strategy, '')
             ORDER BY target.id
             LIMIT 20
            """
            % (project_column, table, project_column)
        )
        missing_with_project = int(
            _scalar(
                """
                SELECT COUNT(*)
                  FROM %s AS target
                  JOIN project_project AS project ON project.id = target.%s
                 WHERE COALESCE(target.operation_strategy, '') = ''
                """
                % (table, project_column)
            )
            or 0
        )
        total = int(_scalar("SELECT COUNT(*) FROM %s" % table) or 0)
        no_project = int(_scalar("SELECT COUNT(*) FROM %s WHERE %s IS NULL" % (table, project_column)) or 0)
        strategy[model] = {
            "total": total,
            "no_project": no_project,
            "missing_with_project": missing_with_project,
            "mismatch_sample": mismatch_rows,
        }
        if mismatch_rows or missing_with_project:
            failures.append(
                {
                    "check": "operation_strategy_matches_project",
                    "model": model,
                    "missing_with_project": missing_with_project,
                    "mismatch_sample": mismatch_rows,
                }
            )

    general_contract_no = {
        "total": int(_scalar("SELECT COUNT(*) FROM sc_general_contract") or 0),
        "missing_contract_no": int(
            _scalar("SELECT COUNT(*) FROM sc_general_contract WHERE COALESCE(contract_no, '') = ''") or 0
        ),
        "missing_contract_no_with_document_no": int(
            _scalar(
                """
                SELECT COUNT(*)
                  FROM sc_general_contract
                 WHERE COALESCE(contract_no, '') = ''
                   AND COALESCE(document_no, '') <> ''
                """
            )
            or 0
        ),
    }
    if general_contract_no["missing_contract_no_with_document_no"]:
        failures.append(
            {
                "check": "general_contract_contract_no_document_no_fallback",
                **general_contract_no,
            }
        )

    result = {
        "audit": "operation_strategy_contract_surface_audit",
        "status": "PASS" if not failures else "FAIL",
        "strategy": strategy,
        "general_contract_no": general_contract_no,
        "failures": failures,
    }
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    print("OPERATION_STRATEGY_CONTRACT_SURFACE_AUDIT: %s" % json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0 if not failures else 1


try:
    sys.exit(main())
except Exception as err:
    result = {
        "audit": "operation_strategy_contract_surface_audit",
        "status": "FAIL",
        "error": str(err),
        "traceback": traceback.format_exc(),
    }
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    print("OPERATION_STRATEGY_CONTRACT_SURFACE_AUDIT: %s" % json.dumps(result, ensure_ascii=False, sort_keys=True))
    sys.exit(1)
