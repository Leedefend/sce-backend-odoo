# -*- coding: utf-8 -*-
import logging

from odoo.exceptions import UserError

from ..registry import SeedStep, register

_logger = logging.getLogger(__name__)


def _find_cny(env):
    currency = env.ref("base.CNY", raise_if_not_found=False)
    if currency:
        return currency
    Currency = env["res.currency"].sudo().with_context(active_test=False)
    return Currency.search([("name", "=", "CNY")], limit=1)


def _run(env):
    company = env.company.sudo()
    currency = _find_cny(env)
    if not currency:
        _logger.warning("Seed currency skipped: base.CNY not found")
        return
    if company.currency_id.id != currency.id:
        if env["account.move.line"].sudo().search_count([]):
            raise UserError("Cannot switch company currency to CNY after journal items exist.")
        company.write({"currency_id": currency.id})
    env["ir.config_parameter"].sudo().set_param("sc.seed.company_currency", currency.name)


register(
    SeedStep(
        name="company_currency_cny",
        description="Ensure company currency is CNY for demo/seed environments.",
        run=_run,
    )
)
