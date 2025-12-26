# -*- coding: utf-8 -*-
from odoo import SUPERUSER_ID, api


def _bind_xmlid(env, record, xmlid, model):
    """Ensure ir.model.data entry exists for the given record/xmlid."""
    module, name = xmlid.split(".", 1)
    data = env["ir.model.data"].sudo().search(
        [("module", "=", module), ("name", "=", name)], limit=1
    )
    if not data:
        env["ir.model.data"].sudo().create(
            {
                "module": module,
                "name": name,
                "model": model,
                "res_id": record.id,
                "noupdate": True,
            }
        )


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
    tax_group = env.ref("smart_construction_core.tax_group_vat_cn", raise_if_not_found=False)
    if not tax_group:
        tax_group = env["account.tax.group"].search([
            ("name", "=", tax_group_vals["name"]),
            ("company_id", "=", company.id),
        ], limit=1)
        if not tax_group:
            tax_group = env["account.tax.group"].create(tax_group_vals)
        _bind_xmlid(env, tax_group, "smart_construction_core.tax_group_vat_cn", "account.tax.group")

    tax_defs = [
        # 默认 xmlid（合同、测试依赖）
        ("smart_construction_core.tax_default_sale_9", "销项VAT 9%", 9, "sale"),
        ("smart_construction_core.tax_default_purchase_13", "进项VAT 13%", 13, "purchase"),
        # 兼容旧命名
        ("smart_construction_core.tax_sale_vat_9", "销项VAT 9%", 9, "sale"),
        ("smart_construction_core.tax_purchase_vat_13", "进项VAT 13%", 13, "purchase"),
        ("smart_construction_core.tax_purchase_vat_3", "进项VAT 3%", 3, "purchase"),
        ("smart_construction_core.tax_purchase_vat_1", "进项VAT 1%", 1, "purchase"),
    ]
    for xmlid, name, amount, tax_use in tax_defs:
        tax = env.ref(xmlid, raise_if_not_found=False)
        if not tax:
            Tax = env["account.tax"].with_context(active_test=False)
            tax = Tax.search([
                ("company_id", "=", company.id),
                ("type_tax_use", "=", tax_use),
                ("amount_type", "=", "percent"),
                ("amount", "=", amount),
                ("name", "=", name),
            ], limit=1)
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
        _bind_xmlid(env, tax, xmlid, "account.tax")
