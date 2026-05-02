# -*- coding: utf-8 -*-
from odoo import SUPERUSER_ID, api


def _map_outbound_state(record):
    if record.state == "done":
        return "issued"
    if record.state == "cancel":
        return "cancel"
    if record.state == "in_progress":
        return "submitted"
    return "draft"


def _migrate_material_outbound(env):
    Source = env["sc.material.document"].sudo()
    Outbound = env["sc.material.outbound"].sudo()
    records = Source.search([("fact_type", "=", "outbound"), ("project_id", "!=", False)])
    created = 0
    for record in records:
        existing = Outbound.search([("legacy_fact_model", "=", record._name), ("legacy_fact_id", "=", record.id)], limit=1)
        if existing:
            continue
        if not record.warehouse_id or not record.source_location_id:
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
                    },
                )
            )
        Outbound.create(
            {
                "name": record.document_no or record.name or "历史材料出库",
                "project_id": record.project_id.id,
                "outbound_date": record.business_date or record.create_date.date(),
                "warehouse_id": record.warehouse_id.id,
                "source_location_id": record.source_location_id.id,
                "receiver_id": record.partner_id.id or False,
                "receiver_user_id": record.requester_id.id or False,
                "keeper_id": record.handler_id.id or record.requester_id.id or False,
                "state": _map_outbound_state(record),
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
    if ICP.get_param("sc.professionalization.v17_0_0_9.done") == "1":
        return
    outbound_count = _migrate_material_outbound(env)
    ICP.set_param("sc.professionalization.v17_0_0_9.material_outbound_count", str(outbound_count))
    ICP.set_param("sc.professionalization.v17_0_0_9.done", "1")
