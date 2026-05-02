# -*- coding: utf-8 -*-
from odoo import SUPERUSER_ID, api


KIND_MAP = {
    "safety_document": ("safety", "安全资料"),
    "quality_document": ("quality", "质量资料"),
    "self_inspection_document": ("self_inspection", "自检资料"),
    "archive_document": ("archive", "归档备案"),
}


def _doc_type(env, kind, label):
    Dictionary = env["sc.dictionary"].sudo()
    code = "doc_%s" % kind
    record = Dictionary.search([("type", "=", "doc_type"), ("code", "=", code)], limit=1)
    if record:
        return record
    return Dictionary.create({"type": "doc_type", "code": code, "name": label})


def _map_state(record):
    if record.state == "done":
        return "done"
    if record.state == "cancel":
        return "cancel"
    if record.state == "in_progress":
        return "review"
    return "draft"


def _backfill_document_kind(env):
    env.cr.execute("UPDATE sc_project_document SET document_kind = 'site' WHERE document_kind IS NULL")


def _migrate_project_document_facts(env):
    Source = env["sc.project.document.fact"].sudo()
    Document = env["sc.project.document"].sudo()
    records = Source.search([("fact_type", "in", list(KIND_MAP)), ("project_id", "!=", False)])
    created = 0
    for record in records:
        existing = Document.search([("legacy_source_model", "=", record._name), ("legacy_record_id", "=", str(record.id))], limit=1)
        if existing:
            continue
        kind, label = KIND_MAP[record.fact_type]
        doc_type = _doc_type(env, kind, label)
        Document.create(
            {
                "name": record.name or record.document_no or label,
                "document_kind": kind,
                "project_id": record.project_id.id,
                "doc_type_id": doc_type.id,
                "date_doc": record.business_date,
                "version": record.document_version,
                "is_mandatory": record.fact_type == "archive_document",
                "responsible_id": record.handler_id.id or record.requester_id.id or env.user.id,
                "note": record.description or record.result_note or record.archive_no,
                "state": _map_state(record),
                "legacy_source_model": record._name,
                "legacy_record_id": str(record.id),
                "legacy_document_state": record.state,
            }
        )
        created += 1
    return created


def migrate(cr, version):
    env = api.Environment(cr, SUPERUSER_ID, {})
    ICP = env["ir.config_parameter"].sudo()
    if ICP.get_param("sc.professionalization.v17_0_0_31.done") == "1":
        return
    _backfill_document_kind(env)
    count = _migrate_project_document_facts(env)
    ICP.set_param("sc.professionalization.v17_0_0_31.project_document_count", str(count))
    ICP.set_param("sc.professionalization.v17_0_0_31.done", "1")
