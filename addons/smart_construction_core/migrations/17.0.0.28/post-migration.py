# -*- coding: utf-8 -*-
from odoo import SUPERUSER_ID, api


def _map_subcontract_price_state(record):
    if record.state in ("done", "in_progress"):
        return "active"
    if record.state == "cancel":
        return "inactive"
    return "draft"


def _migrate_subcontract_price(env):
    Source = env["sc.subcontract.document"].sudo()
    Price = env["sc.subcontract.price"].sudo()
    records = Source.search([("fact_type", "=", "subcontract_price_library")])
    created = 0
    for record in records:
        existing = Price.search([("legacy_fact_model", "=", record._name), ("legacy_fact_id", "=", record.id)], limit=1)
        if existing:
            continue
        Price.create(
            {
                "name": record.document_no or record.name or "历史分包价格",
                "project_id": record.project_id.id or False,
                "subcontractor_id": record.subcontractor_id.id or record.partner_id.id or False,
                "work_scope": record.subcontract_scope or record.name or "历史分包价格",
                "work_content": record.description,
                "unit_name": record.uom_id.name or "项",
                "unit_price": record.amount or 0,
                "tax_rate": 0,
                "effective_date": record.business_date or record.create_date.date(),
                "expire_date": record.due_date,
                "state": _map_subcontract_price_state(record),
                "note": record.description or record.result_note,
                "legacy_fact_model": record._name,
                "legacy_fact_id": record.id,
                "legacy_fact_type": record.fact_type,
            }
        )
        created += 1
    return created


def migrate(cr, version):
    env = api.Environment(cr, SUPERUSER_ID, {})
    ICP = env["ir.config_parameter"].sudo()
    if ICP.get_param("sc.professionalization.v17_0_0_28.done") == "1":
        return
    price_count = _migrate_subcontract_price(env)
    ICP.set_param("sc.professionalization.v17_0_0_28.subcontract_price_count", str(price_count))
    ICP.set_param("sc.professionalization.v17_0_0_28.done", "1")
