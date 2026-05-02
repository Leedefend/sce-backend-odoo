# -*- coding: utf-8 -*-
from odoo import SUPERUSER_ID, api


def _map_labor_price_state(record):
    if record.state in ("done", "in_progress"):
        return "active"
    if record.state == "cancel":
        return "inactive"
    return "draft"


def _migrate_labor_price(env):
    Source = env["sc.labor.document"].sudo()
    Price = env["sc.labor.price"].sudo()
    records = Source.search([("fact_type", "=", "labor_price_library")])
    created = 0
    for record in records:
        existing = Price.search([("legacy_fact_model", "=", record._name), ("legacy_fact_id", "=", record.id)], limit=1)
        if existing:
            continue
        Price.create(
            {
                "name": record.document_no or record.name or "历史劳务价格",
                "project_id": record.project_id.id or False,
                "contractor_id": record.partner_id.id or False,
                "labor_team": record.labor_team,
                "work_content": record.work_content or record.name or "历史劳务价格",
                "unit_name": record.uom_id.name or "工日",
                "unit_price": record.amount or 0,
                "tax_rate": 0,
                "effective_date": record.business_date or record.create_date.date(),
                "expire_date": record.due_date,
                "state": _map_labor_price_state(record),
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
    if ICP.get_param("sc.professionalization.v17_0_0_18.done") == "1":
        return
    price_count = _migrate_labor_price(env)
    ICP.set_param("sc.professionalization.v17_0_0_18.labor_price_count", str(price_count))
    ICP.set_param("sc.professionalization.v17_0_0_18.done", "1")
