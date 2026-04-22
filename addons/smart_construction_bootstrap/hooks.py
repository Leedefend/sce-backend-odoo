# -*- coding: utf-8 -*-
import logging

from odoo import SUPERUSER_ID, api
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


def _as_env(env_or_cr, registry=None):
    if isinstance(env_or_cr, api.Environment):
        return env_or_cr
    return api.Environment(env_or_cr, SUPERUSER_ID, {})


def _find_currency(env, code):
    currency = env.ref(f"base.{code}", raise_if_not_found=False)
    if currency:
        return currency
    return env["res.currency"].sudo().with_context(active_test=False).search(
        [("name", "=", code)],
        limit=1,
    )


def _ensure_company_currency(env, code):
    currency = _find_currency(env, code)
    if not currency:
        raise UserError(f"{code} currency not found. Install base currency data before bootstrap.")
    if not currency.active:
        currency.sudo().active = True

    Company = env["res.company"].sudo()
    companies = Company.search([])
    if not companies or all(company.currency_id == currency for company in companies):
        return
    if "account.move.line" in env.registry and env["account.move.line"].sudo().search_count([]):
        raise UserError(f"Cannot switch company currency to {code} after journal items exist.")
    companies.write({"currency_id": currency.id})
    env["ir.config_parameter"].sudo().set_param("sc.bootstrap.currency", code)


def post_init_hook(env_or_cr, registry=None):
    """Apply fresh-DB currency compatibility for legacy bootstrap flows."""
    env = _as_env(env_or_cr, registry)

    icp = env["ir.config_parameter"].sudo()
    cur = icp.get_param("sc.bootstrap.currency", "CNY")
    _ensure_company_currency(env, cur)

    _logger.info("Construction bootstrap compatibility applied: currency=%s", cur)
