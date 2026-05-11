# -*- coding: utf-8 -*-

import logging

from odoo import SUPERUSER_ID, api


_logger = logging.getLogger(__name__)

_DEMO_DBS = {"sc_demo", "sc_test"}
_DEMO_MODULES = ("smart_construction_demo",)
_SEED_DEMO_XMLIDS = (
    ("smart_construction_seed", "seed_partner_contract"),
    ("smart_construction_seed", "seed_partner_owner"),
    ("smart_construction_seed", "seed_partner_supplier"),
)

_UNLINK_FIRST_MODELS = (
    "payment.request",
    "sc.payment.execution",
    "sc.receipt.income",
    "construction.contract",
    "sc.settlement.order.line",
    "sc.settlement.order",
    "project.task",
    "account.move",
    "project.cost.ledger",
    "project.progress.entry",
    "project.budget.cost.alloc",
    "project.budget.boq.line",
    "project.budget",
    "project.boq.line",
    "project.wbs",
    "sc.project.structure",
    "construction.work.breakdown",
)
_ARCHIVE_MODELS = (
    "project.project",
    "res.partner",
)


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


def _safe_archive(record):
    if not record.exists() or "active" not in record._fields:
        return "missing"
    try:
        with record.env.cr.savepoint():
            record.write({"active": False})
        return "archived"
    except Exception as exc:  # pragma: no cover - depends on live FK graph
        return f"kept:{type(exc).__name__}"


def _archive_by_xmlids(env, xmlid_pairs):
    imd = env["ir.model.data"].sudo()
    archived = []
    for module, name in xmlid_pairs:
        rows = imd.search([("module", "=", module), ("name", "=", name)])
        for row in rows:
            if row.model in env and row.model in _ARCHIVE_MODELS:
                rec = env[row.model].sudo().with_context(active_test=False).browse(row.res_id).exists()
                if rec and "active" in rec._fields:
                    archived.append(f"{module}.{name}:{_safe_archive(rec)}")
            row.exists().unlink()
    return archived


def _cleanup_demo_module_xmlids(env):
    imd = env["ir.model.data"].sudo()
    rows = imd.search([("module", "in", list(_DEMO_MODULES))])
    by_model = {}
    for row in rows:
        by_model.setdefault(row.model, env["ir.model.data"].sudo())
        by_model[row.model] |= row

    actions = []
    ordered_models = list(_UNLINK_FIRST_MODELS) + list(_ARCHIVE_MODELS)
    ordered_models += sorted(model for model in by_model if model not in set(ordered_models))

    for model in ordered_models:
        model_rows = by_model.get(model)
        if not model_rows:
            continue
        for row in model_rows:
            module = row.module
            name = row.name
            action = "xmlid-only"
            if model in env:
                rec = env[model].sudo().with_context(active_test=False).browse(row.res_id).exists()
                if rec:
                    if model in _ARCHIVE_MODELS and "active" in rec._fields:
                        action = _safe_archive(rec)
                    else:
                        action = _safe_unlink_or_archive(rec)
            row.exists().unlink()
            actions.append((model, module, name, action))
    return actions


def migrate(cr, version):
    env = api.Environment(cr, SUPERUSER_ID, {})
    if _is_demo_db(env):
        _logger.info("smart_construction_seed migration: keep demo data in demo database %s", env.cr.dbname)
        return

    ICP = env["ir.config_parameter"].sudo()
    if ICP.get_param("sc.login.env") == "demo":
        ICP.set_param("sc.login.env", "prod")
    if ICP.get_param("sc.bootstrap.mode") == "demo":
        ICP.set_param("sc.bootstrap.mode", "prod")
    ICP.set_param("sc.bootstrap.seed_enabled", "0")

    archived_seed = _archive_by_xmlids(env, _SEED_DEMO_XMLIDS)
    cleaned_demo = _cleanup_demo_module_xmlids(env)
    ICP.set_param("sc.demo_data_cleanup.v17_0_0_2_0.done", "1")
    ICP.set_param("sc.demo_data_cleanup.v17_0_0_2_0.count", str(len(archived_seed) + len(cleaned_demo)))
    _logger.info(
        "smart_construction_seed migration: removed demo residues in %s seed=%s demo_xmlids=%s",
        env.cr.dbname,
        archived_seed,
        len(cleaned_demo),
    )
