# -*- coding: utf-8 -*-
from odoo import SUPERUSER_ID, api


def _map_equipment_usage_state(record):
    if record.state == "done":
        return "confirmed"
    if record.state == "cancel":
        return "cancel"
    if record.state == "in_progress":
        return "submitted"
    return "draft"


def _migrate_equipment_usage(env):
    Source = env["sc.equipment.document"].sudo()
    Usage = env["sc.equipment.usage"].sudo()
    records = Source.search([("fact_type", "=", "equipment_usage"), ("project_id", "!=", False)])
    created = 0
    for record in records:
        existing = Usage.search([("legacy_fact_model", "=", record._name), ("legacy_fact_id", "=", record.id)], limit=1)
        if existing:
            continue
        Usage.create(
            {
                "name": record.document_no or record.name or "历史设备使用登记",
                "project_id": record.project_id.id,
                "usage_date": record.business_date or record.create_date.date(),
                "equipment_name": record.equipment_name or record.name or "历史设备",
                "equipment_code": record.equipment_code,
                "usage_location": record.usage_location or "历史使用地点",
                "operator_name": record.operator_name or "历史操作人员",
                "usage_qty": record.quantity or 1,
                "usage_hours": record.usage_hours or 1,
                "supplier_id": record.partner_id.id or False,
                "recorder_id": record.handler_id.id or record.requester_id.id or False,
                "state": _map_equipment_usage_state(record),
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
    if ICP.get_param("sc.professionalization.v17_0_0_21.done") == "1":
        return
    usage_count = _migrate_equipment_usage(env)
    ICP.set_param("sc.professionalization.v17_0_0_21.equipment_usage_count", str(usage_count))
    ICP.set_param("sc.professionalization.v17_0_0_21.done", "1")
