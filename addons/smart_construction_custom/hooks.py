# -*- coding: utf-8 -*-
from odoo.exceptions import UserError


def ensure_company_currency_cny(env):
    Currency = env["res.currency"].sudo().with_context(active_test=False)
    currency = env.ref("base.CNY", raise_if_not_found=False)
    if not currency:
        currency = Currency.search([("name", "=", "CNY")], limit=1)
    if not currency:
        raise UserError("CNY currency not found. Install base currency data before smart construction custom.")
    if not currency.active:
        currency.write({"active": True})
    companies = env["res.company"].sudo().search([])
    if companies:
        companies.write({"currency_id": currency.id})


def apply_business_full_policy(env):
    env["sc.security.policy"].apply_business_full_policy()


def apply_platform_initialization(env):
    env["sc.platform.initialization"].apply_baseline()


def post_init_hook(env):
    ensure_company_currency_cny(env)
    apply_platform_initialization(env)
    apply_business_full_policy(env)
