# -*- coding: utf-8 -*-
from odoo.exceptions import UserError

from ..registry import SeedStep, register


COMMON_TAX_PERCENTAGES = (1.0, 3.0, 6.0, 9.0, 13.0)


def _format_tax_name(amount):
    return f"{amount:g}%"


def _tax_xmlid(type_tax_use, amount):
    return f"smart_construction_seed.tax_{amount:g}"


def _get_country_id(env):
    company = env.company
    country = company.account_fiscal_country_id or company.partner_id.country_id
    if country:
        return country.id

    Country = env["res.country"].sudo().with_context(active_test=False)
    cn = (
        Country.search([("code", "=", "CN")], limit=1)
        or Country.search([("name", "ilike", "China")], limit=1)
        or Country.search([("name", "ilike", "中国")], limit=1)
        or Country.search([], limit=1)
    )
    if not cn:
        raise UserError("无法创建默认税：系统未初始化国家，请先安装国家基础数据。")

    # 补齐公司国家，以满足 account_tax.country_id 非空约束
    company.sudo().write({"account_fiscal_country_id": cn.id})
    if company.partner_id:
        company.partner_id.sudo().write({"country_id": cn.id})

    return cn.id


def _get_tax_group(env, type_tax_use: str):
    Group = env["account.tax.group"].sudo().with_context(active_test=False)
    company = env.company
    preferred_name = "合同税率"
    grp = Group.search([("company_id", "=", company.id), ("name", "=", preferred_name)], limit=1)
    if grp:
        return grp
    legacy_names = ["销项税率", "进项税率", "销项税组", "进项税组", "默认税组(销项)", "默认税组(进项)"]
    grp = Group.search([("company_id", "=", company.id), ("name", "in", legacy_names)], limit=1)
    if grp:
        grp.write({"name": preferred_name})
        return grp
    # fallback: create minimal group
    return Group.create({"name": preferred_name, "company_id": company.id})


def _find_template_tax(env, type_tax_use: str):
    Tax = env["account.tax"].with_context(active_test=False)
    company = env.company
    domain = [
        ("company_id", "=", company.id),
        ("type_tax_use", "=", type_tax_use),
        ("amount_type", "=", "percent"),
        ("price_include", "=", False),
        ("active", "in", [True, False]),
    ]
    tax = Tax.search(domain, limit=1)
    return tax


def _bind_xmlid(env, xmlid, record):
    Imd = env["ir.model.data"].sudo().with_context(active_test=False)
    module, name_id = xmlid.split(".")
    existing = Imd.search([("module", "=", module), ("name", "=", name_id)], limit=1)
    if existing:
        existing.write({"model": record._name, "res_id": record.id, "noupdate": True})
    else:
        Imd.create(
            {
                "module": module,
                "name": name_id,
                "model": record._name,
                "res_id": record.id,
                "noupdate": True,
            }
        )


def _ensure_tax(env, xmlid, name, amount, type_tax_use):
    ICP = env["ir.config_parameter"].sudo()
    Tax = env["account.tax"].sudo().with_context(active_test=False)
    company = env.company

    tax = env.ref(xmlid, raise_if_not_found=False)
    if tax:
        vals = {}
        if tax.name != name:
            vals["name"] = name
        if tax.amount != float(amount):
            vals["amount"] = float(amount)
        if tax.amount_type != "percent":
            vals["amount_type"] = "percent"
        if tax.type_tax_use != type_tax_use:
            vals["type_tax_use"] = type_tax_use
        if tax.price_include:
            vals["price_include"] = False
        if tax.company_id.id != company.id:
            vals["company_id"] = company.id
        if not tax.active:
            vals["active"] = True
        if not tax.tax_group_id:
            vals["tax_group_id"] = _get_tax_group(env, type_tax_use).id
        if vals:
            tax.write(vals)
        ICP.set_param(f"sc.seed.tax.{type_tax_use}.{amount}", str(tax.id))
        return tax

    domain = [
        ("company_id", "=", company.id),
        ("type_tax_use", "=", type_tax_use),
        ("amount_type", "=", "percent"),
        ("price_include", "=", False),
        ("amount", "=", float(amount)),
    ]
    tax = Tax.search(domain, limit=1)
    if tax:
        tax.write({"name": name, "active": True})
    else:
        tmpl = _find_template_tax(env, type_tax_use)
        if tmpl:
            tax = tmpl.copy(
                {
                    "name": name,
                    "amount": float(amount),
                    "type_tax_use": type_tax_use,
                    "amount_type": "percent",
                    "price_include": False,
                    "active": True,
                }
            )
        else:
            country_id = _get_country_id(env)
            group = _get_tax_group(env, type_tax_use)
            tax = Tax.create(
                {
                    "name": name,
                    "company_id": company.id,
                    "country_id": country_id,
                    "tax_group_id": group.id,
                    "type_tax_use": type_tax_use,
                    "amount_type": "percent",
                    "amount": float(amount),
                    "price_include": False,
                    "active": True,
                }
            )

    _bind_xmlid(env, xmlid, tax)
    ICP.set_param(f"sc.seed.tax.{type_tax_use}.{amount}", str(tax.id))
    return tax


def _run(env):
    ensured_by_amount = {}
    for amount in COMMON_TAX_PERCENTAGES:
        tax = _ensure_tax(env, _tax_xmlid("none", amount), _format_tax_name(amount), amount, "none")
        ensured_by_amount[float(amount)] = tax
    legacy_xmlids = {
        "smart_construction_seed.tax_sale_9": 9.0,
        "smart_construction_seed.tax_purchase_13": 13.0,
    }
    for xmlid, amount in legacy_xmlids.items():
        tax = ensured_by_amount.get(float(amount))
        if tax:
            _bind_xmlid(env, xmlid, tax)
    env["ir.config_parameter"].sudo().set_param("sc.seed.tax_seeded", "1")


register(
    SeedStep(
        name="tax_defaults",
        description="Seed common contract taxes as direct percentage options.",
        run=_run,
    )
)
