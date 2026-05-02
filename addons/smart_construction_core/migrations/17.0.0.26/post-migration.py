# -*- coding: utf-8 -*-
from odoo import SUPERUSER_ID, api


def _map_subcontract_register_state(record):
    if record.state == "done":
        return "closed"
    if record.state == "cancel":
        return "cancel"
    if record.state == "in_progress":
        return "active"
    return "draft"


def _migrate_subcontract_register(env):
    Source = env["sc.subcontract.document"].sudo()
    Register = env["sc.subcontract.register"].sudo()
    records = Source.search([("fact_type", "=", "subcontract_register"), ("project_id", "!=", False)])
    created = 0
    for record in records:
        existing = Register.search([("legacy_fact_model", "=", record._name), ("legacy_fact_id", "=", record.id)], limit=1)
        if existing:
            continue
        scope = record.subcontract_scope or record.name or "历史分包登记"
        line_vals = [
            (
                0,
                0,
                {
                    "work_scope": scope,
                    "work_content": record.description,
                    "contract_qty": record.quantity or 1,
                    "unit_name": record.uom_id.name,
                    "registered_amount": record.amount or 0,
                    "note": record.result_note,
                },
            )
        ]
        Register.create(
            {
                "name": record.document_no or record.name or "历史分包登记",
                "project_id": record.project_id.id,
                "contract_id": record.contract_id.id or False,
                "register_date": record.business_date or record.create_date.date(),
                "start_date": record.start_date or record.planned_date,
                "end_date": record.end_date or record.due_date,
                "subcontract_scope": scope,
                "subcontractor_id": record.subcontractor_id.id or record.partner_id.id or False,
                "responsible_id": record.handler_id.id or record.requester_id.id or False,
                "currency_id": env.company.currency_id.id,
                "state": _map_subcontract_register_state(record),
                "management_note": record.description,
                "note": record.result_note,
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
    if ICP.get_param("sc.professionalization.v17_0_0_26.done") == "1":
        return
    register_count = _migrate_subcontract_register(env)
    ICP.set_param("sc.professionalization.v17_0_0_26.subcontract_register_count", str(register_count))
    ICP.set_param("sc.professionalization.v17_0_0_26.done", "1")
