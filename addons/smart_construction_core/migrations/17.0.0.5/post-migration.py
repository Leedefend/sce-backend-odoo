# -*- coding: utf-8 -*-
from odoo import SUPERUSER_ID, api


def _map_issue_state(record):
    if record.state == "done":
        return "closed"
    if record.state == "cancel":
        return "cancel"
    if record.fact_type.endswith("_rectification"):
        return "rechecking" if record.rectification_result else "rectifying"
    if record.state == "in_progress":
        return "rectifying"
    return "submitted"


def _base_issue_vals(record):
    return {
        "name": record.name or record.document_no or "历史检查问题",
        "project_id": record.project_id.id,
        "issue_date": record.business_date or record.create_date.date(),
        "location": record.inspection_location or getattr(record, "location_detail", "") or "",
        "issue_level": record.issue_level or "normal",
        "responsible_party_id": record.responsible_party_id.id or False,
        "owner_id": record.handler_id.id or record.requester_id.id or False,
        "rectification_deadline": record.rectification_deadline or record.due_date,
        "description": record.description,
        "state": _map_issue_state(record),
        "legacy_fact_model": record._name,
        "legacy_fact_id": record.id,
        "legacy_fact_type": record.fact_type,
    }


def _migrate_quality(env):
    Source = env["sc.construction.inspection"].sudo()
    Issue = env["sc.quality.issue"].sudo()
    Rectification = env["sc.quality.rectification"].sudo()
    records = Source.search([("fact_type", "in", ["quality_check", "quality_rectification"]), ("project_id", "!=", False)])
    created_issue = 0
    created_rectification = 0
    for record in records:
        issue = Issue.search([("legacy_fact_model", "=", record._name), ("legacy_fact_id", "=", record.id)], limit=1)
        if not issue:
            issue = Issue.create(_base_issue_vals(record))
            created_issue += 1
        if record.rectification_result:
            existing = Rectification.search(
                [("legacy_fact_model", "=", record._name), ("legacy_fact_id", "=", record.id)],
                limit=1,
            )
            if not existing:
                Rectification.create(
                    {
                        "issue_id": issue.id,
                        "rectification_date": record.write_date.date() if record.write_date else record.business_date,
                        "handler_id": record.handler_id.id or record.requester_id.id or False,
                        "result": record.rectification_result,
                        "legacy_fact_model": record._name,
                        "legacy_fact_id": record.id,
                        "legacy_fact_type": record.fact_type,
                    }
                )
                created_rectification += 1
    return created_issue, created_rectification


def _migrate_safety(env):
    Source = env["sc.construction.inspection"].sudo()
    Issue = env["sc.safety.issue"].sudo()
    Rectification = env["sc.safety.rectification"].sudo()
    records = Source.search([("fact_type", "in", ["safety_check", "safety_rectification"]), ("project_id", "!=", False)])
    created_issue = 0
    created_rectification = 0
    for record in records:
        issue = Issue.search([("legacy_fact_model", "=", record._name), ("legacy_fact_id", "=", record.id)], limit=1)
        if not issue:
            vals = _base_issue_vals(record)
            issue = Issue.create(vals)
            created_issue += 1
        if record.rectification_result:
            existing = Rectification.search(
                [("legacy_fact_model", "=", record._name), ("legacy_fact_id", "=", record.id)],
                limit=1,
            )
            if not existing:
                Rectification.create(
                    {
                        "issue_id": issue.id,
                        "rectification_date": record.write_date.date() if record.write_date else record.business_date,
                        "handler_id": record.handler_id.id or record.requester_id.id or False,
                        "result": record.rectification_result,
                        "legacy_fact_model": record._name,
                        "legacy_fact_id": record.id,
                        "legacy_fact_type": record.fact_type,
                    }
                )
                created_rectification += 1
    return created_issue, created_rectification


def migrate(cr, version):
    env = api.Environment(cr, SUPERUSER_ID, {})
    ICP = env["ir.config_parameter"].sudo()
    if ICP.get_param("sc.professionalization.v17_0_0_5.done") == "1":
        return
    q_issue, q_rect = _migrate_quality(env)
    s_issue, s_rect = _migrate_safety(env)
    ICP.set_param("sc.professionalization.v17_0_0_5.quality_issue_count", str(q_issue))
    ICP.set_param("sc.professionalization.v17_0_0_5.quality_rectification_count", str(q_rect))
    ICP.set_param("sc.professionalization.v17_0_0_5.safety_issue_count", str(s_issue))
    ICP.set_param("sc.professionalization.v17_0_0_5.safety_rectification_count", str(s_rect))
    ICP.set_param("sc.professionalization.v17_0_0_5.done", "1")
