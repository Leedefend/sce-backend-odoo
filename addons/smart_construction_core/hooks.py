# -*- coding: utf-8 -*-
import zlib
from odoo import SUPERUSER_ID, api


def _tax_key(company_id, type_tax_use, name, amount, amount_type, price_include=False):
    raw = f"{company_id}|{type_tax_use}|{amount_type}|{amount}|{int(bool(price_include))}|{name}".encode("utf-8")
    return zlib.crc32(raw) & 0xFFFFFFFF


def _advisory_xact_lock(cr, key_int):
    cr.execute("SELECT pg_advisory_xact_lock(%s)", (int(key_int),))


def _find_or_create_tax(
    env,
    *,
    company,
    type_tax_use,
    name,
    amount,
    amount_type="percent",
    price_include=False,
    tax_group=None,
    country=None,
):
    """Idempotent tax getter with tx-level lock to avoid duplicate create under concurrency."""
    Tax = env["account.tax"].with_context(active_test=False).sudo()
    domain = [
        ("company_id", "=", company.id),
        ("type_tax_use", "=", type_tax_use),
        ("amount_type", "=", amount_type),
        ("amount", "=", amount),
        ("price_include", "=", bool(price_include)),
        ("name", "=", name),
    ]
    tax = Tax.search(domain, limit=1)
    if tax:
        if not tax.active:
            tax.active = True
        return tax

    lock_key = _tax_key(company.id, type_tax_use, name, amount, amount_type, price_include)
    _advisory_xact_lock(env.cr, lock_key)

    tax = Tax.search(domain, limit=1)
    if tax:
        if not tax.active:
            tax.active = True
        return tax

    vals = {
        "name": name,
        "amount_type": amount_type,
        "amount": amount,
        "type_tax_use": type_tax_use,
        "price_include": bool(price_include),
        "company_id": company.id,
        "active": True,
    }
    if tax_group:
        vals["tax_group_id"] = tax_group.id
    if country:
        vals["country_id"] = country.id
    return Tax.create(vals)


def ensure_core_taxes(env_or_cr, registry=None):
    """Guarantee税组与税率存在，即便被意外删除也能自愈."""
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
    for name, amount, tax_use in tax_defs:
        tax = _find_or_create_tax(
            env,
            company=company,
            type_tax_use=tax_use,
            name=name,
            amount=amount,
            amount_type="percent",
            price_include=False,
            tax_group=tax_group,
            country=country,
        )


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


def post_init_hook(env):
    """Install-time hook to ensure core taxes are present."""
    ensure_core_taxes(env)
    _archive_default_project_stages(env)


def _archive_default_project_stages(env):
    """Archive Odoo default project stages to keep lifecycle stages canonical."""
    Stage = env["project.project.stage"].sudo()
    builtin_names = [
        "To Do",
        "In Progress",
        "Done",
        "Canceled",
        "Cancelled",
        "New",
    ]
    for name in builtin_names:
        stages = Stage.search([("name", "ilike", name), ("active", "=", True)])
        if stages:
            stages.write({"active": False})
