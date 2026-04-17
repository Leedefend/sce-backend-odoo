# -*- coding: utf-8 -*-
from odoo import SUPERUSER_ID, api
from odoo.addons.smart_construction_core.hooks import ensure_core_taxes
from odoo.exceptions import UserError


def _as_env(env_or_cr, registry=None):
    if isinstance(env_or_cr, api.Environment):
        return env_or_cr
    return api.Environment(env_or_cr, SUPERUSER_ID, {})


def _find_cny(env):
    currency = env.ref("base.CNY", raise_if_not_found=False)
    if currency:
        return currency
    return env["res.currency"].sudo().with_context(active_test=False).search(
        [("name", "=", "CNY")],
        limit=1,
    )


def _apply_company_currency_baseline(env):
    currency = _find_cny(env)
    if not currency:
        raise UserError("CNY currency not found. Install base currency data before customer bootstrap.")
    if not currency.active:
        currency.sudo().active = True

    Company = env["res.company"].sudo()
    companies = Company.search([])
    if not companies or all(company.currency_id == currency for company in companies):
        return
    if "account.move.line" in env.registry and env["account.move.line"].sudo().search_count([]):
        raise UserError("Cannot switch company currency to CNY after journal items exist.")
    companies.write({"currency_id": currency.id})
    env["ir.config_parameter"].sudo().set_param("sc.custom.company_currency", currency.name)


def _apply_user_locale_baseline(env, lang="zh_CN", tz="Asia/Shanghai"):
    env["res.lang"]._activate_lang(lang)
    icp = env["ir.config_parameter"].sudo()
    icp.set_param("lang", lang)
    icp.set_param("tz", tz)

    users = env["res.users"].sudo().search([
        ("share", "=", False),
        ("active", "=", True),
    ])
    for user in users:
        vals = {}
        if user.lang != lang:
            vals["lang"] = lang
        if (user.tz or "") != tz:
            vals["tz"] = tz
        if vals:
            user.write(vals)


def _ensure_xmlid(env, xmlid, record):
    module, name = xmlid.split(".", 1)
    imd = env["ir.model.data"].sudo().search(
        [("module", "=", module), ("name", "=", name)],
        limit=1,
    )
    values = {
        "module": module,
        "name": name,
        "model": record._name,
        "res_id": record.id,
        "noupdate": True,
    }
    if imd:
        imd.write(values)
    else:
        env["ir.model.data"].sudo().create(values)


def ensure_customer_default_taxes(env):
    """Materialize contract default taxes for no-demo customer installs."""
    ensure_core_taxes(env)
    required = [
        ("smart_construction_seed.tax_sale_9", "销项VAT 9%", 9.0, "sale"),
        ("smart_construction_seed.tax_purchase_13", "进项VAT 13%", 13.0, "purchase"),
    ]
    Tax = env["account.tax"].sudo().with_context(active_test=False)
    company = env.ref("base.main_company")
    for xmlid, name, amount, tax_use in required:
        tax = env.ref(xmlid, raise_if_not_found=False)
        if not tax:
            tax = Tax.search(
                [
                    ("company_id", "=", company.id),
                    ("name", "=", name),
                    ("amount", "=", amount),
                    ("amount_type", "=", "percent"),
                    ("type_tax_use", "=", tax_use),
                    ("price_include", "=", False),
                ],
                limit=1,
            )
        if not tax:
            raise UserError("缺少客户默认税率：%s %.1f%% %s" % (name, amount, tax_use))
        if not tax.active:
            tax.active = True
        _ensure_xmlid(env, xmlid, tax)


def _ensure_language_pack_loaded(env, lang="zh_CN"):
    language = env["res.lang"].search([("code", "=", lang)], limit=1)
    if not language:
        return

    needs_install = True
    settings_menu = env.ref("base.menu_administration", raise_if_not_found=False)
    if settings_menu:
        env.cr.execute("SELECT name FROM ir_ui_menu WHERE id = %s", (settings_menu.id,))
        row = env.cr.fetchone()
        if row and isinstance(row[0], dict) and lang in row[0]:
            needs_install = False

    if not needs_install:
        return

    wizard = env["base.language.install"].create(
        {
            "lang_ids": [(6, 0, [language.id])],
            "overwrite": True,
        }
    )
    wizard.lang_install()


def apply_business_full_policy(env):
    env["sc.security.policy"].apply_business_full_policy()


def post_init_hook(env_or_cr, registry=None):
    env = _as_env(env_or_cr, registry)
    _ensure_language_pack_loaded(env)
    _apply_company_currency_baseline(env)
    ensure_customer_default_taxes(env)
    _apply_user_locale_baseline(env)
    apply_business_full_policy(env)
