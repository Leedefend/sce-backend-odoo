# -*- coding: utf-8 -*-
from odoo import SUPERUSER_ID, api


def _map_subcontract_settlement_state(record):
    if record.state == "done":
        return "confirmed"
    if record.state == "cancel":
        return "cancel"
    if record.state == "in_progress":
        return "submitted"
    return "draft"


def _migrate_subcontract_settlement(env):
    Source = env["sc.subcontract.document"].sudo()
    Settlement = env["sc.subcontract.settlement"].sudo()
    records = Source.search([("fact_type", "=", "subcontract_settlement"), ("project_id", "!=", False), ("subcontractor_id", "!=", False)])
    created = 0
    currency = env.company.currency_id
    for record in records:
        existing = Settlement.search([("legacy_fact_model", "=", record._name), ("legacy_fact_id", "=", record.id)], limit=1)
        if existing:
            continue
        scope = record.subcontract_scope or record.name or "历史分包结算"
        qty = record.quantity or 1
        amount = record.amount or 0
        unit_price = amount / qty if qty else 0
        line_vals = [
            (
                0,
                0,
                {
                    "work_scope": scope,
                    "work_content": record.description,
                    "qty": qty,
                    "unit_name": record.uom_id.name or "项",
                    "unit_price": unit_price,
                    "tax_rate": 0,
                    "note": record.result_note,
                },
            )
        ]
        Settlement.create(
            {
                "name": record.document_no or record.name or "历史分包结算",
                "project_id": record.project_id.id,
                "contract_id": record.contract_id.id or False,
                "subcontractor_id": record.subcontractor_id.id,
                "settlement_date": record.business_date or record.create_date.date(),
                "owner_id": record.handler_id.id or record.requester_id.id or False,
                "currency_id": currency.id,
                "state": _map_subcontract_settlement_state(record),
                "note": record.description or record.result_note,
                "legacy_fact_model": record._name,
                "legacy_fact_id": record.id,
                "legacy_fact_type": record.fact_type,
                "line_ids": line_vals,
            }
        )
        created += 1
    return created


def migrate(cr, version):
    env = api.Environment(cr, SUPERUSER_ID, {})
    ICP = env["ir.config_parameter"].sudo()
    if ICP.get_param("sc.professionalization.v17_0_0_27.done") == "1":
        return
    settlement_count = _migrate_subcontract_settlement(env)
    ICP.set_param("sc.professionalization.v17_0_0_27.subcontract_settlement_count", str(settlement_count))
    ICP.set_param("sc.professionalization.v17_0_0_27.done", "1")
