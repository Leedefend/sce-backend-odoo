# -*- coding: utf-8 -*-
from odoo import SUPERUSER_ID, api


def _map_request_state(record):
    if record.state == "done":
        return "approved"
    if record.state == "cancel":
        return "cancel"
    if record.state == "in_progress":
        return "submitted"
    return "draft"


def _migrate_material_purchase_request(env):
    Source = env["sc.material.document"].sudo()
    Request = env["sc.material.purchase.request"].sudo()
    records = Source.search([("fact_type", "=", "purchase_request"), ("project_id", "!=", False)])
    created = 0
    for record in records:
        existing = Request.search([("legacy_fact_model", "=", record._name), ("legacy_fact_id", "=", record.id)], limit=1)
        if existing:
            continue
        line_vals = []
        if record.product_id and record.quantity:
            line_vals.append(
                (
                    0,
                    0,
                    {
                        "product_id": record.product_id.id,
                        "material_spec": record.material_spec,
                        "product_uom_id": record.uom_id.id or record.product_id.uom_id.id,
                        "qty": record.quantity,
                        "estimated_unit_price": record.unit_price,
                        "currency_id": record.currency_id.id,
                    },
                )
            )
        Request.create(
            {
                "name": record.document_no or record.name or "历史材料采购申请",
                "project_id": record.project_id.id,
                "request_date": record.business_date or record.create_date.date(),
                "required_date": record.due_date or record.planned_date,
                "requester_id": record.requester_id.id or False,
                "department_id": record.department_id.id or False,
                "purpose": record.name if record.name != record.document_no else "",
                "state": _map_request_state(record),
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
    if ICP.get_param("sc.professionalization.v17_0_0_10.done") == "1":
        return
    request_count = _migrate_material_purchase_request(env)
    ICP.set_param("sc.professionalization.v17_0_0_10.material_purchase_request_count", str(request_count))
    ICP.set_param("sc.professionalization.v17_0_0_10.done", "1")
