# -*- coding: utf-8 -*-
from odoo import SUPERUSER_ID, api


def _map_labor_usage_state(record):
    if record.state == "done":
        return "confirmed"
    if record.state == "cancel":
        return "cancel"
    if record.state == "in_progress":
        return "submitted"
    return "draft"


def _migrate_labor_usage(env):
    Source = env["sc.labor.document"].sudo()
    Usage = env["sc.labor.usage"].sudo()
    records = Source.search([("fact_type", "=", "labor_employment"), ("project_id", "!=", False)])
    created = 0
    for record in records:
        existing = Usage.search([("legacy_fact_model", "=", record._name), ("legacy_fact_id", "=", record.id)], limit=1)
        if existing:
            continue
        Usage.create(
            {
                "name": record.document_no or record.name or "历史劳务用工",
                "project_id": record.project_id.id,
                "usage_date": record.business_date or record.attendance_date or record.create_date.date(),
                "labor_team": record.labor_team or "未标明班组",
                "contractor_id": record.partner_id.id or False,
                "work_content": record.work_content or record.name or "历史劳务用工",
                "worker_qty": record.worker_count or 1,
                "work_hours": record.work_hours,
                "recorder_id": record.handler_id.id or record.requester_id.id or False,
                "state": _map_labor_usage_state(record),
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
    if ICP.get_param("sc.professionalization.v17_0_0_14.done") == "1":
        return
    usage_count = _migrate_labor_usage(env)
    ICP.set_param("sc.professionalization.v17_0_0_14.labor_usage_count", str(usage_count))
    ICP.set_param("sc.professionalization.v17_0_0_14.done", "1")
