# -*- coding: utf-8 -*-
from odoo import SUPERUSER_ID, api


REPORT_TYPE_LABELS = {
    "daily_report": "日报表",
    "weekly_report": "周报表",
    "monthly_report": "月报表",
}


def _map_report_state(record):
    if record.state == "done":
        return "done"
    if record.state == "cancel":
        return "cancel"
    if record.state == "in_progress":
        return "confirmed"
    return "draft"


def _migrate_construction_reports(env):
    Source = env["sc.construction.report"].sudo()
    Diary = env["sc.construction.diary"].sudo()
    records = Source.search([("fact_type", "in", list(REPORT_TYPE_LABELS)), ("project_id", "!=", False)])
    created = 0
    for record in records:
        existing = Diary.search([("legacy_source_model", "=", record._name), ("legacy_record_id", "=", str(record.id))], limit=1)
        if existing:
            continue
        report_type = REPORT_TYPE_LABELS[record.fact_type]
        Diary.create(
            {
                "name": record.document_no or record.name or report_type,
                "source_origin": "legacy",
                "state": _map_report_state(record),
                "project_id": record.project_id.id,
                "date_diary": record.business_date or record.create_date,
                "report_period_start": record.period_start or record.business_date,
                "report_period_end": record.period_end or record.business_date,
                "document_no": record.document_no,
                "title": record.name,
                "diary_type": report_type,
                "category": "施工报表",
                "weather": record.weather,
                "manpower_count": record.manpower_count,
                "handler_name": record.handler_id.name or record.requester_id.name,
                "description": record.completed_work or record.description,
                "next_plan": record.next_plan,
                "header_description": record.description,
                "legacy_source_model": record._name,
                "legacy_record_id": str(record.id),
                "legacy_document_state": record.state,
                "note": record.result_note,
            }
        )
        created += 1
    return created


def migrate(cr, version):
    env = api.Environment(cr, SUPERUSER_ID, {})
    ICP = env["ir.config_parameter"].sudo()
    if ICP.get_param("sc.professionalization.v17_0_0_30.done") == "1":
        return
    report_count = _migrate_construction_reports(env)
    ICP.set_param("sc.professionalization.v17_0_0_30.construction_report_count", str(report_count))
    ICP.set_param("sc.professionalization.v17_0_0_30.done", "1")
