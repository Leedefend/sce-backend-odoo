# -*- coding: utf-8 -*-
"""Backfill mechanical settlement counterparties from user-visible legacy data.

Run inside Odoo shell:
    odoo shell -d sc_demo < scripts/ops/backfill_mechanical_settlement_partner.py

Dry-run by default. Set APPLY=1 or MIGRATION_APPLY=1 to write.
"""

from __future__ import annotations

import json
import os
import sys
import traceback


SOURCE_MODEL = "sc.legacy.direct.acceptance.fact"
ACCEPTANCE_LABEL = "机械结算单"
COUNTERPARTY_FIELD = "legacy_visible_05"


def _text(value) -> str:
    value = "" if value in (None, False) else str(value)
    value = value.replace("\r\n", "\n").replace("\r", "\n").strip()
    if value in {"False", "false", "None", "none"}:
        return ""
    return value


def _candidate_partner_by_name():
    env.cr.execute(  # noqa: F821
        """
        SELECT name, COUNT(*) AS partner_count, MIN(id) AS partner_id
          FROM res_partner
         WHERE COALESCE(name, '') <> ''
         GROUP BY name
        """
    )
    return {
        row[0]: {"partner_count": int(row[1] or 0), "partner_id": int(row[2] or 0)}
        for row in env.cr.fetchall()  # noqa: F821
    }


def main() -> int:
    apply = os.getenv("APPLY") == "1" or os.getenv("MIGRATION_APPLY") == "1"
    Settlement = env["sc.settlement.order"].sudo().with_context(  # noqa: F821
        active_test=False,
        legacy_migration_allow_missing_contract=True,
    )
    partner_by_name = _candidate_partner_by_name()
    records = Settlement.search(
        [
            ("legacy_fact_model", "=", SOURCE_MODEL),
            ("legacy_acceptance_label", "=", ACCEPTANCE_LABEL),
            ("partner_id", "=", False),
            (COUNTERPARTY_FIELD, "!=", False),
        ],
        order="id",
    )

    planned = []
    residuals = []
    amount_planned = 0.0
    amount_residual = 0.0
    residual_by_reason = {}

    for record in records:
        counterparty_name = _text(getattr(record, COUNTERPARTY_FIELD))
        partner_match = partner_by_name.get(counterparty_name)
        reason = ""
        if not counterparty_name:
            reason = "missing_counterparty_name"
        elif not partner_match:
            reason = "missing_partner"
        elif partner_match["partner_count"] != 1:
            reason = "duplicate_partner_name"

        if reason:
            amount_residual += record.amount_total or 0.0
            residual_by_reason[reason] = residual_by_reason.get(reason, 0) + 1
            residuals.append(
                {
                    "id": record.id,
                    "name": record.name,
                    "project_id": record.project_id.id,
                    "counterparty_name": counterparty_name,
                    "amount_total": record.amount_total,
                    "reason": reason,
                    "partner_count": partner_match["partner_count"] if partner_match else 0,
                }
            )
            continue

        partner_id = partner_match["partner_id"]
        amount_planned += record.amount_total or 0.0
        planned.append(
            {
                "id": record.id,
                "name": record.name,
                "project_id": record.project_id.id,
                "counterparty_name": counterparty_name,
                "partner_id": partner_id,
                "amount_total": record.amount_total,
            }
        )
        if apply:
            vals = {
                "partner_id": partner_id,
                "settlement_unit_id": partner_id,
            }
            if not _text(record.legacy_counterparty_name):
                vals["legacy_counterparty_name"] = counterparty_name
            record.write(vals)

    if apply:
        env.cr.commit()  # noqa: F821

    result = {
        "operation": "backfill_mechanical_settlement_partner",
        "status": "PASS",
        "applied": apply,
        "source_model": SOURCE_MODEL,
        "acceptance_label": ACCEPTANCE_LABEL,
        "counterparty_field": COUNTERPARTY_FIELD,
        "planned_count": len(planned),
        "planned_amount": round(amount_planned, 2),
        "residual_count": len(residuals),
        "residual_amount": round(amount_residual, 2),
        "residual_by_reason": residual_by_reason,
        "sample_planned": planned[:20],
        "sample_residuals": residuals[:20],
    }
    print("MECHANICAL_SETTLEMENT_PARTNER_BACKFILL: %s" % json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0


try:
    sys.exit(main())
except Exception as err:
    result = {
        "operation": "backfill_mechanical_settlement_partner",
        "status": "FAIL",
        "error": str(err),
        "traceback": traceback.format_exc(),
    }
    print("MECHANICAL_SETTLEMENT_PARTNER_BACKFILL: %s" % json.dumps(result, ensure_ascii=False, sort_keys=True))
    sys.exit(1)
