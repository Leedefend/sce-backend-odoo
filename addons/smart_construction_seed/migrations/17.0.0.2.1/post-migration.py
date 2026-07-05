# -*- coding: utf-8 -*-

import logging

from odoo import SUPERUSER_ID, api


_logger = logging.getLogger(__name__)

_DEMO_DBS = {"sc_demo", "sc_test"}
_DEMO_MODULES = ("smart_construction_demo",)
_ARCHIVE_MODELS = ("project.project", "res.partner")


def _is_demo_db(env):
    db_name = str(env.cr.dbname or "").strip()
    return db_name in _DEMO_DBS or db_name.startswith("sc_demo_") or db_name.startswith("sc_test_")


def _safe_unlink_or_archive(record):
    if not record.exists():
        return "missing"
    try:
        with record.env.cr.savepoint():
            record.unlink()
        return "unlinked"
    except Exception as exc:  # pragma: no cover - depends on live FK graph
        record = record.exists().sudo()
        if record and "active" in record._fields:
            record.write({"active": False})
            return f"archived:{type(exc).__name__}"
        return f"kept:{type(exc).__name__}"


def migrate(cr, version):
    env = api.Environment(cr, SUPERUSER_ID, {})
    if _is_demo_db(env):
        _logger.info("smart_construction_seed migration: keep demo XMLIDs in demo database %s", env.cr.dbname)
        return

    actions = []
    rows = env["ir.model.data"].sudo().search([("module", "in", list(_DEMO_MODULES))])
    for row in rows:
        action = "xmlid-only"
        if row.model == "res.users":
            action = "xmlid-only-user-kept"
        elif row.model in env:
            rec = env[row.model].sudo().with_context(active_test=False).browse(row.res_id).exists()
            if rec:
                if row.model in _ARCHIVE_MODELS and "active" in rec._fields:
                    action = _safe_unlink_or_archive(rec)
                else:
                    action = _safe_unlink_or_archive(rec)
        actions.append("%s.%s:%s:%s" % (row.module, row.name, row.model, action))
        row.exists().unlink()

    ICP = env["ir.config_parameter"].sudo()
    ICP.set_param("sc.demo_data_cleanup.v17_0_0_2_1.done", "1")
    ICP.set_param("sc.demo_data_cleanup.v17_0_0_2_1.count", str(len(actions)))
    _logger.info(
        "smart_construction_seed migration: removed demo XMLID residues in %s actions=%s",
        env.cr.dbname,
        actions,
    )
