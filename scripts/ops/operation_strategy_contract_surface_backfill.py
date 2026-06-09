# -*- coding: utf-8 -*-
"""Backfill stored operation strategy and contract number surfaces.

Run inside Odoo shell:
    odoo shell -d sc_demo < scripts/ops/operation_strategy_contract_surface_backfill.py
"""

import json
import sys
import traceback


STRATEGY_TARGETS = (
    ("sc_general_contract", "project_id"),
    ("sc_fund_account", "project_id"),
    ("sc_treasury_reconciliation", "project_id"),
)


def _scalar(sql, params=None):
    env.cr.execute(sql, params or [])  # noqa: F821
    row = env.cr.fetchone()  # noqa: F821
    return row[0] if row else None


def _refresh_operation_strategy(table, project_column):
    before = int(
        _scalar(
            """
            SELECT COUNT(*)
              FROM %s AS target
              JOIN project_project AS project ON project.id = target.%s
             WHERE COALESCE(target.operation_strategy, '') IS DISTINCT FROM COALESCE(project.operation_strategy, '')
            """
            % (table, project_column)
        )
        or 0
    )
    env.cr.execute(  # noqa: F821
        """
        UPDATE %s AS target
           SET operation_strategy = project.operation_strategy,
               write_date = NOW()
          FROM project_project AS project
         WHERE project.id = target.%s
           AND COALESCE(target.operation_strategy, '') IS DISTINCT FROM COALESCE(project.operation_strategy, '')
        """
        % (table, project_column)
    )
    updated = env.cr.rowcount  # noqa: F821
    return {"before_mismatch": before, "updated": updated}


def main():
    strategy_updates = {
        table: _refresh_operation_strategy(table, project_column)
        for table, project_column in STRATEGY_TARGETS
    }

    env.cr.execute(  # noqa: F821
        """
        UPDATE sc_general_contract
           SET contract_no = NULLIF(document_no, ''),
               write_date = NOW()
         WHERE COALESCE(contract_no, '') = ''
           AND COALESCE(document_no, '') <> ''
        """
    )
    contract_no_updated = env.cr.rowcount  # noqa: F821

    env.cr.commit()  # noqa: F821

    result = {
        "operation": "operation_strategy_contract_surface_backfill",
        "status": "PASS",
        "strategy_updates": strategy_updates,
        "contract_no_updated": contract_no_updated,
        "remaining": {
            "sc_general_contract_no_strategy": int(
                _scalar("SELECT COUNT(*) FROM sc_general_contract WHERE COALESCE(operation_strategy, '') = ''") or 0
            ),
            "sc_general_contract_no_contract_no": int(
                _scalar("SELECT COUNT(*) FROM sc_general_contract WHERE COALESCE(contract_no, '') = ''") or 0
            ),
            "sc_fund_account_no_strategy": int(
                _scalar("SELECT COUNT(*) FROM sc_fund_account WHERE COALESCE(operation_strategy, '') = ''") or 0
            ),
            "sc_treasury_reconciliation_no_strategy": int(
                _scalar("SELECT COUNT(*) FROM sc_treasury_reconciliation WHERE COALESCE(operation_strategy, '') = ''") or 0
            ),
        },
    }
    print("OPERATION_STRATEGY_CONTRACT_SURFACE_BACKFILL: %s" % json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0


try:
    sys.exit(main())
except Exception as err:
    result = {
        "operation": "operation_strategy_contract_surface_backfill",
        "status": "FAIL",
        "error": str(err),
        "traceback": traceback.format_exc(),
    }
    print("OPERATION_STRATEGY_CONTRACT_SURFACE_BACKFILL: %s" % json.dumps(result, ensure_ascii=False, sort_keys=True))
    sys.exit(1)
