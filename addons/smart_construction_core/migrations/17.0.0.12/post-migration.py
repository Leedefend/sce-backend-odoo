# -*- coding: utf-8 -*-
from odoo import SUPERUSER_ID, api


def _fallback_date(record):
    return record.business_date or (record.create_date.date() if record.create_date else False)


def _map_rfq_state(record):
    if record.state == "done":
        return "selected"
    if record.state == "cancel":
        return "cancel"
    if record.state == "in_progress":
        return "submitted"
    return "draft"


def _map_settlement_state(record):
    if record.state == "done":
        return "confirmed"
    if record.state == "cancel":
        return "cancel"
    if record.state == "in_progress":
        return "submitted"
    return "draft"


def _unit_price(record):
    if record.unit_price:
        return record.unit_price
    if record.amount and record.quantity:
        return record.amount / record.quantity
    return 0.0


def _migrate_material_rfq(env):
    Source = env["sc.material.document"].sudo()
    Rfq = env["sc.material.rfq"].sudo()
    records = Source.search([("fact_type", "=", "rfq"), ("project_id", "!=", False)])
    created = 0
    currency = env.company.currency_id
    for record in records:
        existing = Rfq.search([("legacy_fact_model", "=", record._name), ("legacy_fact_id", "=", record.id)], limit=1)
        if existing:
            continue
        line_vals = []
        if record.partner_id and record.product_id and record.quantity:
            line_vals.append(
                (
                    0,
                    0,
                    {
                        "supplier_id": record.partner_id.id,
                        "product_id": record.product_id.id,
                        "material_spec": record.material_spec,
                        "product_uom_id": record.uom_id.id or record.product_id.uom_id.id,
                        "qty": record.quantity,
                        "currency_id": record.currency_id.id or currency.id,
                        "unit_price": _unit_price(record),
                        "selected": record.state == "done",
                        "note": record.supplier_quote or record.result_note,
                    },
                )
            )
        Rfq.create(
            {
                "name": record.document_no or record.name or "历史材料询比价",
                "project_id": record.project_id.id,
                "rfq_date": _fallback_date(record),
                "due_date": record.due_date,
                "owner_id": record.handler_id.id or record.requester_id.id or False,
                "selected_supplier_id": record.partner_id.id if record.state == "done" else False,
                "state": _map_rfq_state(record),
                "note": record.description or record.result_note,
                "legacy_fact_model": record._name,
                "legacy_fact_id": record.id,
                "legacy_fact_type": record.fact_type,
                "line_ids": line_vals,
            }
        )
        created += 1
    return created


def _migrate_material_settlement(env):
    Source = env["sc.material.document"].sudo()
    Settlement = env["sc.material.settlement"].sudo()
    records = Source.search([("fact_type", "=", "settlement"), ("project_id", "!=", False), ("partner_id", "!=", False)])
    created = 0
    currency = env.company.currency_id
    for record in records:
        existing = Settlement.search([("legacy_fact_model", "=", record._name), ("legacy_fact_id", "=", record.id)], limit=1)
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
                        "unit_price": _unit_price(record),
                        "note": record.result_note,
                    },
                )
            )
        Settlement.create(
            {
                "name": record.document_no or record.name or "历史材料结算",
                "project_id": record.project_id.id,
                "supplier_id": record.partner_id.id,
                "settlement_date": _fallback_date(record),
                "owner_id": record.handler_id.id or record.requester_id.id or False,
                "currency_id": record.currency_id.id or currency.id,
                "state": _map_settlement_state(record),
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
    if ICP.get_param("sc.professionalization.v17_0_0_12.done") == "1":
        return
    rfq_count = _migrate_material_rfq(env)
    settlement_count = _migrate_material_settlement(env)
    ICP.set_param("sc.professionalization.v17_0_0_12.material_rfq_count", str(rfq_count))
    ICP.set_param("sc.professionalization.v17_0_0_12.material_settlement_count", str(settlement_count))
    ICP.set_param("sc.professionalization.v17_0_0_12.done", "1")
