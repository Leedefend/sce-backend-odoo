# -*- coding: utf-8 -*-
from odoo import SUPERUSER_ID, api


def _map_equipment_request_state(record):
    if record.state == "done":
        return "approved"
    if record.state == "cancel":
        return "cancel"
    if record.state == "in_progress":
        return "submitted"
    return "draft"


def _migrate_equipment_request(env):
    Source = env["sc.equipment.document"].sudo()
    Request = env["sc.equipment.request"].sudo()
    records = Source.search([("fact_type", "=", "equipment_request"), ("project_id", "!=", False)])
    created = 0
    for record in records:
        existing = Request.search([("legacy_fact_model", "=", record._name), ("legacy_fact_id", "=", record.id)], limit=1)
        if existing:
            continue
        line_vals = []
        if record.equipment_name or record.equipment_code or record.usage_hours:
            line_vals.append(
                (
                    0,
                    0,
                    {
                        "equipment_name": record.equipment_name or record.name or "历史设备申请",
                        "equipment_code": record.equipment_code,
                        "requested_qty": record.quantity or 1,
                        "planned_hours": record.usage_hours,
                        "usage_location": record.usage_location,
                        "operator_requirement": record.operator_name,
                        "note": record.result_note,
                    },
                )
            )
        Request.create(
            {
                "name": record.document_no or record.name or "历史设备申请",
                "project_id": record.project_id.id,
                "request_date": record.business_date or record.create_date.date(),
                "required_date": record.planned_date or record.due_date,
                "usage_location": record.usage_location,
                "requester_id": record.requester_id.id or record.handler_id.id or False,
                "supplier_id": record.partner_id.id or False,
                "state": _map_equipment_request_state(record),
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
    if ICP.get_param("sc.professionalization.v17_0_0_20.done") == "1":
        return
    request_count = _migrate_equipment_request(env)
    ICP.set_param("sc.professionalization.v17_0_0_20.equipment_request_count", str(request_count))
    ICP.set_param("sc.professionalization.v17_0_0_20.done", "1")
