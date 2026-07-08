# -*- coding: utf-8 -*-
import json

from odoo.exceptions import UserError
from odoo.addons.smart_core.utils.backend_contract_boundaries import ensure_lowcode_contract_source_status


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


def apply_user_preferences(env):
    env["sc.user.preference.initialization"].apply_user_menu_preferences()
    env["sc.user.preference.initialization"].apply_user_form_preferences()
    env["sc.user.preference.initialization"].apply_customer_lowcode_contract_assets()
    backfill_lowcode_contract_source_status(env)


def backfill_lowcode_contract_source_status(env):
    Contract = env["ui.business.config.contract"].sudo()
    for rec in Contract.search([], order="id"):
        payload = rec.contract_json if isinstance(rec.contract_json, dict) else {}
        next_payload = ensure_lowcode_contract_source_status(payload)
        if next_payload == payload:
            continue
        env.cr.execute(
            """
            UPDATE ui_business_config_contract
               SET contract_json = %s::jsonb,
                   write_date = NOW()
             WHERE id = %s
            """,
            (json.dumps(next_payload, ensure_ascii=False), rec.id),
        )


def apply_user_data_baseline(env):
    env["sc.user.preference.initialization"].apply_user_data_baseline()


def post_init_hook(env):
    ensure_company_currency_cny(env)
    apply_platform_initialization(env)
    apply_business_full_policy(env)
    apply_user_data_baseline(env)
    apply_user_preferences(env)
