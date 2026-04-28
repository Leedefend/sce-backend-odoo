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
    if not companies:
        env["ir.config_parameter"].sudo().set_param("sc.bootstrap.currency", code)
        return
    if all(company.currency_id == currency for company in companies):
        env["ir.config_parameter"].sudo().set_param("sc.bootstrap.currency", code)
        return
    if "account.move.line" in env.registry and env["account.move.line"].sudo().search_count([]):
        raise UserError(f"Cannot switch company currency to {code} after journal items exist.")
    companies.write({"currency_id": currency.id})
    env["ir.config_parameter"].sudo().set_param("sc.bootstrap.currency", code)


def _ensure_language(env, code):
    lang = env["res.lang"].sudo().with_context(active_test=False).search(
        [("code", "=", code)],
        limit=1,
    )
    if not lang:
        raise UserError(f"{code} language not found. Install base language data before bootstrap.")
    if not lang.active:
        lang.write({"active": True})
    return lang.code


def _ensure_user_preferences(env, lang, tz):
    Users = env["res.users"].sudo().with_context(active_test=False)
    users = Users.search(["|", ("share", "=", False), ("login", "in", ["public", "__system__"])])

    for xmlid in ("base.user_admin", "base.user_root", "base.public_user"):
        user = env.ref(xmlid, raise_if_not_found=False)
        if user:
            users |= user.sudo()

    users = users.filtered(lambda user: user.partner_id)
    if users:
        users.mapped("partner_id").write({"lang": lang, "tz": tz})


def _ensure_res_users_notification_default(env):
    env.cr.execute(
        """
        SELECT 1
          FROM information_schema.columns
         WHERE table_name = 'res_users'
           AND column_name = 'notification_type'
        """
    )
    if env.cr.fetchone():
        env.cr.execute("ALTER TABLE res_users ALTER COLUMN notification_type SET DEFAULT 'email'")


def post_init_hook(env_or_cr, registry=None):
    """Apply fresh-DB baseline compatibility for legacy bootstrap flows."""
    env = _as_env(env_or_cr, registry)

    icp = env["ir.config_parameter"].sudo()
    lang = icp.get_param("sc.bootstrap.lang", "zh_CN")
    tz = icp.get_param("sc.bootstrap.tz", "Asia/Shanghai")
    cur = icp.get_param("sc.bootstrap.currency", "CNY")
    lang = _ensure_language(env, lang)
    _ensure_user_preferences(env, lang, tz)
    _ensure_res_users_notification_default(env)
    icp.set_param("sc.bootstrap.lang", lang)
    icp.set_param("sc.bootstrap.tz", tz)
    _ensure_company_currency(env, cur)

    _logger.info("Construction bootstrap compatibility applied: lang=%s tz=%s currency=%s", lang, tz, cur)
