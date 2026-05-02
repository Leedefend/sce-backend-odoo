# -*- coding: utf-8 -*-
from odoo import SUPERUSER_ID, api


def _migrate_catalog_prices(env):
    Catalog = env["sc.material.catalog"].sudo()
    Price = env["sc.material.price"].sudo()
    catalogs = Catalog.search(["|", ("planned_price", ">", 0), ("internal_price", ">", 0)])
    created = 0
    currency = env.company.currency_id
    for catalog in catalogs:
        for price_type, amount in (("planned", catalog.planned_price), ("internal", catalog.internal_price)):
            if not amount:
                continue
            existing = Price.search(
                [
                    ("source_model", "=", catalog._name),
                    ("source_res_id", "=", catalog.id),
                    ("source_type", "=", price_type),
                ],
                limit=1,
            )
            if existing:
                continue
            Price.create(
                {
                    "material_catalog_id": catalog.id,
                    "product_id": catalog.promoted_product_id.id or False,
                    "project_id": catalog.project_id.id or False,
                    "price_type": price_type,
                    "currency_id": currency.id,
                    "unit_price": amount,
                    "source_model": catalog._name,
                    "source_res_id": catalog.id,
                    "source_type": price_type,
                    "note": "由材料档案历史价格迁移生成。",
                }
            )
            created += 1
    return created


def migrate(cr, version):
    env = api.Environment(cr, SUPERUSER_ID, {})
    ICP = env["ir.config_parameter"].sudo()
    if ICP.get_param("sc.professionalization.v17_0_0_11.done") == "1":
        return
    price_count = _migrate_catalog_prices(env)
    ICP.set_param("sc.professionalization.v17_0_0_11.material_price_count", str(price_count))
    ICP.set_param("sc.professionalization.v17_0_0_11.done", "1")
