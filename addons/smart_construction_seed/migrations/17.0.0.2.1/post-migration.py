# -*- coding: utf-8 -*-
"""Record demo-ownership risk without mutating owned records or XML IDs.

Database names and deployment environments are not data-ownership facts.  A
restored historical database must therefore produce exactly the same result
under every database name.  Any cleanup requires a separately approved,
fingerprint-bound operational workflow.
"""

import logging

from odoo import SUPERUSER_ID, api


_logger = logging.getLogger(__name__)

_DEMO_MODULE = "smart_construction_demo"
_MARKER_PREFIX = "sc.demo_ownership_review.v17_0_0_2_1"


def _risk_summary(env):
    rows = env["ir.model.data"].sudo().search([("module", "=", _DEMO_MODULE)])
    model_counts = {}
    existing_record_count = 0
    missing_record_count = 0
    for row in rows:
        model = str(row.model or "")
        model_counts[model] = model_counts.get(model, 0) + 1
        if model not in env:
            missing_record_count += 1
            continue
        record = env[model].sudo().with_context(active_test=False).browse(row.res_id).exists()
        if record:
            existing_record_count += 1
        else:
            missing_record_count += 1
    return {
        "xmlid_count": len(rows),
        "model_count": len(model_counts),
        "existing_record_count": existing_record_count,
        "missing_record_count": missing_record_count,
    }


def migrate(cr, version):
    del version
    env = api.Environment(cr, SUPERUSER_ID, {})
    summary = _risk_summary(env)
    ICP = env["ir.config_parameter"].sudo()
    values = {
        "mode": "report_only",
        "cleanup_required": "1" if summary["xmlid_count"] else "0",
        **{key: str(value) for key, value in summary.items()},
    }
    for key, value in values.items():
        ICP.set_param(f"{_MARKER_PREFIX}.{key}", value)
    _logger.warning(
        "smart_construction_seed migration retained all demo-owned XML IDs and records; "
        "explicit fingerprint-bound ownership review required; summary=%s",
        summary,
    )
