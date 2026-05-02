# -*- coding: utf-8 -*-
from odoo import SUPERUSER_ID, api


def _map_subcontract_request_state(record):
    if record.state == "done":
        return "approved"
    if record.state == "cancel":
        return "cancel"
    if record.state == "in_progress":
        return "submitted"
    return "draft"


def _migrate_subcontract_request(env):
    Source = env["sc.subcontract.document"].sudo()
    Request = env["sc.subcontract.request"].sudo()
    records = Source.search([("fact_type", "=", "subcontract_request"), ("project_id", "!=", False)])
    created = 0
    for record in records:
        existing = Request.search([("legacy_fact_model", "=", record._name), ("legacy_fact_id", "=", record.id)], limit=1)
        if existing:
            continue
        scope = record.subcontract_scope or record.name or "历史分包申请"
        line_vals = [
            (
                0,
                0,
                {
                    "work_scope": scope,
                    "work_content": record.description,
                    "required_qty": record.quantity or 1,
                    "unit_name": record.uom_id.name,
                    "required_date": record.planned_date or record.due_date,
                    "estimated_amount": record.amount or 0,
                    "note": record.result_note,
                },
            )
        ]
        Request.create(
            {
                "name": record.document_no or record.name or "历史分包申请",
                "project_id": record.project_id.id,
                "contract_id": record.contract_id.id or False,
                "request_date": record.business_date or record.create_date.date(),
                "need_start_date": record.start_date or record.planned_date,
                "need_end_date": record.end_date or record.due_date,
                "subcontract_scope": scope,
                "suggested_subcontractor_id": record.subcontractor_id.id or record.partner_id.id or False,
                "applicant_id": record.requester_id.id or record.handler_id.id or False,
                "department_id": record.department_id.id or False,
                "currency_id": env.company.currency_id.id,
                "state": _map_subcontract_request_state(record),
                "request_reason": record.description,
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
    if ICP.get_param("sc.professionalization.v17_0_0_25.done") == "1":
        return
    request_count = _migrate_subcontract_request(env)
    ICP.set_param("sc.professionalization.v17_0_0_25.subcontract_request_count", str(request_count))
    ICP.set_param("sc.professionalization.v17_0_0_25.done", "1")
