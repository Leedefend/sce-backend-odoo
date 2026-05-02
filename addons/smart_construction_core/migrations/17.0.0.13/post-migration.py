# -*- coding: utf-8 -*-
from odoo import SUPERUSER_ID, api


def _map_attendance_state(record):
    if record.state == "done":
        return "confirmed"
    if record.state == "cancel":
        return "cancel"
    if record.state == "in_progress":
        return "submitted"
    return "draft"


def _migrate_attendance_checkin(env):
    Source = env["sc.labor.document"].sudo()
    Attendance = env["sc.attendance.checkin"].sudo()
    records = Source.search([("fact_type", "=", "attendance_record"), ("project_id", "!=", False)])
    created = 0
    for record in records:
        existing = Attendance.search([("legacy_fact_model", "=", record._name), ("legacy_fact_id", "=", record.id)], limit=1)
        if existing:
            continue
        Attendance.create(
            {
                "name": record.document_no or record.name or "历史考勤记录",
                "project_id": record.project_id.id,
                "attendance_date": record.attendance_date or record.business_date or record.create_date.date(),
                "labor_team": record.labor_team or "未标明班组",
                "work_content": record.work_content or record.name or "历史考勤",
                "attendance_qty": record.worker_count or 1,
                "work_hours": record.work_hours,
                "contractor_id": record.partner_id.id or False,
                "recorder_id": record.handler_id.id or record.requester_id.id or False,
                "state": _map_attendance_state(record),
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
    if ICP.get_param("sc.professionalization.v17_0_0_13.done") == "1":
        return
    attendance_count = _migrate_attendance_checkin(env)
    ICP.set_param("sc.professionalization.v17_0_0_13.attendance_checkin_count", str(attendance_count))
    ICP.set_param("sc.professionalization.v17_0_0_13.done", "1")
