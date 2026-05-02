# -*- coding: utf-8 -*-
from odoo import SUPERUSER_ID, api


def _map_acceptance_state(record):
    if record.state == "done":
        return "accepted"
    if record.state == "cancel":
        return "cancel"
    if record.state == "in_progress":
        return "submitted"
    return "draft"


def _migrate_material_acceptance(env):
    Source = env["sc.material.document"].sudo()
    Acceptance = env["sc.material.acceptance"].sudo()
    records = Source.search([("fact_type", "=", "inbound"), ("project_id", "!=", False)])
    created = 0
    for record in records:
        existing = Acceptance.search([("legacy_fact_model", "=", record._name), ("legacy_fact_id", "=", record.id)], limit=1)
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
                        "received_qty": record.quantity,
                        "accepted_qty": record.quantity if record.state == "done" else 0.0,
                        "result": "accepted" if record.state == "done" else "partial",
                    },
                )
            )
        Acceptance.create(
            {
                "name": record.document_no or record.name or "历史材料入库",
                "project_id": record.project_id.id,
                "acceptance_date": record.business_date or record.create_date.date(),
                "supplier_id": record.partner_id.id or False,
                "warehouse_id": record.warehouse_id.id or False,
                "dest_location_id": record.dest_location_id.id or False,
                "inspector_id": record.handler_id.id or record.requester_id.id or False,
                "state": _map_acceptance_state(record),
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
    if ICP.get_param("sc.professionalization.v17_0_0_7.done") == "1":
        return
    material_acceptance_count = _migrate_material_acceptance(env)
    ICP.set_param("sc.professionalization.v17_0_0_7.material_acceptance_count", str(material_acceptance_count))
    ICP.set_param("sc.professionalization.v17_0_0_7.done", "1")
