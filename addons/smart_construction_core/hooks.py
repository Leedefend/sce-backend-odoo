# -*- coding: utf-8 -*-
from odoo import SUPERUSER_ID, api


def ensure_core_taxes(env_or_cr, registry=None):
    """Post-init hook to guarantee税组与税率存在，即便被意外删除也能自愈。

    Compatible with both legacy (cr, registry) and new (env) signatures.
    """
    if registry:
        env = api.Environment(env_or_cr, SUPERUSER_ID, {})
    else:
        env = env_or_cr
    company = env.ref("base.main_company")
    country = env.ref("base.cn", raise_if_not_found=False)

    tax_group_vals = {
        "name": "增值税",
        "sequence": 10,
        "company_id": company.id,
    }
    if country:
        tax_group_vals["country_id"] = country.id
    tax_group = (
        env["account.tax.group"]
        .sudo()
        .with_context(active_test=False)
        .search(
            [
                ("name", "=", tax_group_vals["name"]),
                ("company_id", "=", company.id),
            ],
            limit=1,
        )
    )
    if not tax_group:
        tax_group = env["account.tax.group"].sudo().create(tax_group_vals)

    tax_defs = [
        ("销项VAT 9%", 9, "sale"),
        ("进项VAT 13%", 13, "purchase"),
        ("进项VAT 3%", 3, "purchase"),
        ("进项VAT 1%", 1, "purchase"),
    ]
    Tax = env["account.tax"].sudo()
    for name, amount, tax_use in tax_defs:
        tax = Tax.with_context(active_test=False).search(
            [
                ("company_id", "=", company.id),
                ("type_tax_use", "in", [tax_use, "all"]),
                ("amount_type", "=", "percent"),
                ("amount", "=", amount),
            ],
            limit=1,
        )
        if not tax:
            vals = {
                "name": name,
                "amount_type": "percent",
                "amount": amount,
                "type_tax_use": tax_use,
                "tax_group_id": tax_group.id,
                "company_id": company.id,
                "active": True,
            }
            if country:
                vals["country_id"] = country.id
            tax = Tax.create(vals)
        else:
            if not tax.active:
                tax.active = True


def pre_init_hook(env):
    """Protect legacy tax/tax group xmlids from upgrade-time cleanup.

    Odoo passes env to pre_init_hook. Use env.cr to run SQL.
    """
    env.cr.execute(
        """
        UPDATE ir_model_data
           SET noupdate = TRUE,
               module   = 'smart_construction_legacy'
         WHERE module = 'smart_construction_core'
           AND name IN (
                'tax_default_sale_9',
                'tax_default_purchase_13',
                'tax_purchase_vat_13',
                'tax_purchase_vat_3',
                'tax_purchase_vat_1',
                'tax_sale_vat_9',
                'tax_group_vat_cn'
           );
        """
    )
