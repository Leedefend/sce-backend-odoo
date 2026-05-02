# -*- coding: utf-8 -*-
from odoo import SUPERUSER_ID, api


def _map_equipment_plan_state(record):
    if record.state == "done":
        return "approved"
    if record.state == "cancel":
        return "cancel"
    if record.state == "in_progress":
        return "submitted"
    return "draft"


def _migrate_equipment_plan(env):
    Source = env["sc.equipment.document"].sudo()
    Plan = env["sc.equipment.plan"].sudo()
    records = Source.search([("fact_type", "=", "equipment_plan"), ("project_id", "!=", False)])
    created = 0
    for record in records:
        existing = Plan.search([("legacy_fact_model", "=", record._name), ("legacy_fact_id", "=", record.id)], limit=1)
        if existing:
            continue
        line_vals = []
        if record.equipment_name or record.equipment_code or record.usage_hours:
            line_vals.append(
                (
                    0,
                    0,
                    {
                        "equipment_name": record.equipment_name or record.name or "历史设备计划",
                        "equipment_code": record.equipment_code,
                        "planned_qty": record.quantity or 1,
                        "planned_hours": record.usage_hours,
                        "usage_location": record.usage_location,
                        "operator_requirement": record.operator_name,
                        "note": record.result_note,
                    },
                )
            )
        Plan.create(
            {
                "name": record.document_no or record.name or "历史设备计划",
                "project_id": record.project_id.id,
                "plan_date": record.business_date or record.create_date.date(),
                "start_date": record.planned_date,
                "end_date": record.due_date,
                "usage_location": record.usage_location,
                "owner_id": record.handler_id.id or record.requester_id.id or False,
                "supplier_id": record.partner_id.id or False,
                "state": _map_equipment_plan_state(record),
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
    if ICP.get_param("sc.professionalization.v17_0_0_19.done") == "1":
        return
    plan_count = _migrate_equipment_plan(env)
    ICP.set_param("sc.professionalization.v17_0_0_19.equipment_plan_count", str(plan_count))
    ICP.set_param("sc.professionalization.v17_0_0_19.done", "1")
