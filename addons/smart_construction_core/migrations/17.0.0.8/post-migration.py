# -*- coding: utf-8 -*-
from odoo import SUPERUSER_ID, api


def _map_inbound_state(record):
    if record.state == "done":
        return "received"
    if record.state == "cancel":
        return "cancel"
    if record.state == "in_progress":
        return "submitted"
    return "draft"


def _migrate_material_inbound(env):
    Source = env["sc.material.document"].sudo()
    Acceptance = env["sc.material.acceptance"].sudo()
    Inbound = env["sc.material.inbound"].sudo()
    records = Source.search([("fact_type", "=", "inbound"), ("project_id", "!=", False)])
    created = 0
    for record in records:
        existing = Inbound.search([("legacy_fact_model", "=", record._name), ("legacy_fact_id", "=", record.id)], limit=1)
        if existing:
            continue
        acceptance = Acceptance.search([("legacy_fact_model", "=", record._name), ("legacy_fact_id", "=", record.id)], limit=1)
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
                    },
                )
            )
        if not record.warehouse_id or not record.dest_location_id:
            continue
        Inbound.create(
            {
                "name": record.document_no or record.name or "历史材料入库",
                "project_id": record.project_id.id,
                "inbound_date": record.business_date or record.create_date.date(),
                "acceptance_id": acceptance.id or False,
                "supplier_id": record.partner_id.id or False,
                "warehouse_id": record.warehouse_id.id,
                "dest_location_id": record.dest_location_id.id,
                "keeper_id": record.handler_id.id or record.requester_id.id or False,
                "state": _map_inbound_state(record),
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
    if ICP.get_param("sc.professionalization.v17_0_0_8.done") == "1":
        return
    inbound_count = _migrate_material_inbound(env)
    ICP.set_param("sc.professionalization.v17_0_0_8.material_inbound_count", str(inbound_count))
    ICP.set_param("sc.professionalization.v17_0_0_8.done", "1")
