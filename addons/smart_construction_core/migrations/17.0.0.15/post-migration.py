# -*- coding: utf-8 -*-
from odoo import SUPERUSER_ID, api


def _map_labor_settlement_state(record):
    if record.state == "done":
        return "confirmed"
    if record.state == "cancel":
        return "cancel"
    if record.state == "in_progress":
        return "submitted"
    return "draft"


def _migrate_labor_settlement(env):
    Source = env["sc.labor.document"].sudo()
    Settlement = env["sc.labor.settlement"].sudo()
    records = Source.search([("fact_type", "=", "labor_settlement"), ("project_id", "!=", False), ("partner_id", "!=", False)])
    created = 0
    currency = env.company.currency_id
    for record in records:
        existing = Settlement.search([("legacy_fact_model", "=", record._name), ("legacy_fact_id", "=", record.id)], limit=1)
        if existing:
            continue
        qty = record.worker_count or record.work_hours or 1
        total = record.amount or 0.0
        unit_price = total / qty if qty else total
        Settlement.create(
            {
                "name": record.document_no or record.name or "历史劳务结算",
                "project_id": record.project_id.id,
                "contractor_id": record.partner_id.id,
                "settlement_date": record.business_date or record.attendance_date or record.create_date.date(),
                "owner_id": record.handler_id.id or record.requester_id.id or False,
                "currency_id": record.currency_id.id or currency.id,
                "state": _map_labor_settlement_state(record),
                "note": record.description or record.result_note,
                "legacy_fact_model": record._name,
                "legacy_fact_id": record.id,
                "legacy_fact_type": record.fact_type,
                "line_ids": [
                    (
                        0,
                        0,
                        {
                            "labor_team": record.labor_team,
                            "work_content": record.work_content or record.name or "历史劳务结算",
                            "qty": qty,
                            "unit_name": "项",
                            "unit_price": unit_price,
                            "note": record.result_note,
                        },
                    )
                ],
            }
        )
        created += 1
    return created


def migrate(cr, version):
    env = api.Environment(cr, SUPERUSER_ID, {})
    ICP = env["ir.config_parameter"].sudo()
    if ICP.get_param("sc.professionalization.v17_0_0_15.done") == "1":
        return
    settlement_count = _migrate_labor_settlement(env)
    ICP.set_param("sc.professionalization.v17_0_0_15.labor_settlement_count", str(settlement_count))
    ICP.set_param("sc.professionalization.v17_0_0_15.done", "1")
