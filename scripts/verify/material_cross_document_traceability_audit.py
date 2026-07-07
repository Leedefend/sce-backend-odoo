# -*- coding: utf-8 -*-
import json
import sys
import traceback

from odoo import fields


def _token():
    return env["ir.sequence"].sudo().next_by_code("sc.business.fact") or str(fields.Datetime.now())  # noqa: F821


def _expect(condition, label, failures):
    if not condition:
        failures.append(label)
        return False
    return True


def _ensure_groups():
    user = env.user.sudo()  # noqa: F821
    for xmlid in (
        "smart_construction_core.group_sc_cap_business_initiator",
        "smart_construction_core.group_sc_cap_material_user",
        "smart_construction_core.group_sc_cap_material_manager",
    ):
        group = env.ref(xmlid, raise_if_not_found=False)  # noqa: F821
        if group and group.id not in user.groups_id.ids:
            user.write({"groups_id": [(4, group.id)]})
    env.invalidate_all()  # noqa: F821


def _project():
    return env["project.project"].sudo().create(  # noqa: F821
        {
            "name": "MCDT Project %s" % _token(),
            "company_id": env.company.id,  # noqa: F821
            "manager_id": env.user.id,  # noqa: F821
        }
    )


def _supplier():
    return env["res.partner"].sudo().create(  # noqa: F821
        {
            "name": "MCDT Supplier %s" % _token(),
            "supplier_rank": 1,
        }
    )


def _product():
    product = env["product.product"].sudo().search([("default_code", "=", "SC-SYSTEM-DEFAULT-MATERIAL")], limit=1)  # noqa: F821
    if product:
        return product
    return env["product.product"].sudo().create(  # noqa: F821
        {
            "name": "系统默认材料",
            "default_code": "SC-SYSTEM-DEFAULT-MATERIAL",
            "type": "product",
        }
    )


def _warehouse():
    warehouse = env["stock.warehouse"].sudo().search([("company_id", "in", [env.company.id, False])], limit=1)  # noqa: F821
    if warehouse:
        return warehouse
    return env["stock.warehouse"].sudo().create(  # noqa: F821
        {
            "name": "MCDT Warehouse",
            "code": "MCDT",
            "company_id": env.company.id,  # noqa: F821
        }
    )


def _material(project):
    token = _token()
    return env["sc.material.catalog"].sudo().create(  # noqa: F821
        {
            "name": "MCDT Material %s" % token,
            "code": "MCDT-%s" % token,
            "company_id": env.company.id,  # noqa: F821
            "project_id": project.id,
            "spec_model": "MCDT-SPEC",
            "uom_text": "件",
        }
    )


def _create_plan(shared):
    plan = env["project.material.plan"].sudo().create(  # noqa: F821
        {
            "project_id": shared["project"].id,
            "line_ids": [
                (
                    0,
                    0,
                    {
                        "material_catalog_id": shared["material"].id,
                        "product_id": shared["product"].id,
                        "uom_id": shared["product"].uom_id.id,
                        "quantity": 4.0,
                        "vendor_id": shared["supplier"].id,
                        "note": "MCDT计划行",
                    },
                )
            ],
        }
    )
    plan.action_submit()
    plan.action_approve()
    plan.invalidate_recordset()
    return plan


def _generate_rfq(plan, shared):
    wizard = env["material.plan.to.rfq.wizard"].sudo().with_context(  # noqa: F821
        active_model="project.material.plan",
        active_ids=[plan.id],
    ).create(
        {
            "partner_id": shared["supplier"].id,
            "note": "MCDT计划生成询价",
        }
    )
    wizard.action_generate_rfq()
    rfq = env["sc.material.rfq"].sudo().search([("source_material_plan_id", "=", plan.id)], order="id desc", limit=1)  # noqa: F821
    if rfq:
        rfq.line_ids.write({"unit_price": 18.0})
        rfq.line_ids[:1].write({"selected": True})
        rfq.action_submit()
        rfq.action_select()
        rfq.invalidate_recordset()
    return rfq


def _create_purchase_order(rfq):
    rfq.action_create_purchase_order()
    order = env["purchase.order"].sudo().search([("source_material_rfq_id", "=", rfq.id)], order="id desc", limit=1)  # noqa: F821
    return order


def _create_acceptance_from_order(order, shared):
    acceptance = env["sc.material.acceptance"].sudo().create(  # noqa: F821
        {
            "purchase_order_id": order.id,
            "warehouse_id": shared["warehouse"].id,
            "dest_location_id": shared["warehouse"].lot_stock_id.id,
        }
    )
    acceptance.action_submit()
    acceptance.action_accept()
    acceptance.invalidate_recordset()
    return acceptance


def _create_inbound_from_acceptance(acceptance, shared):
    inbound = env["sc.material.inbound"].sudo().create(  # noqa: F821
        {
            "acceptance_id": acceptance.id,
            "warehouse_id": shared["warehouse"].id,
            "dest_location_id": shared["warehouse"].lot_stock_id.id,
        }
    )
    inbound.action_load_acceptance_lines()
    inbound.action_submit()
    inbound.action_receive()
    inbound.invalidate_recordset()
    return inbound


def _find_stock_summary(shared):
    return env["sc.material.stock.summary"].sudo().search(  # noqa: F821
        [
            ("project_id", "=", shared["project"].id),
            ("material_code", "=", shared["material"].code),
            ("material_name", "=", shared["material"].name),
            ("material_spec", "=", "MCDT-SPEC"),
        ],
        limit=1,
    )


failures = []
evidence = {}

try:
    _ensure_groups()
    shared = {
        "project": _project(),
        "supplier": _supplier(),
        "product": _product(),
        "warehouse": _warehouse(),
    }
    shared["material"] = _material(shared["project"])

    plan = _create_plan(shared)
    plan_line = plan.line_ids[:1]
    rfq = _generate_rfq(plan, shared)
    _expect(bool(rfq), "rfq: expected RFQ generated from material plan", failures)
    if rfq:
        _expect(rfq.source_material_plan_id == plan, "rfq.source_material_plan_id: expected plan link", failures)
        _expect(rfq.state == "selected", "rfq.state: expected selected", failures)
        _expect(
            all(line.source_material_plan_line_id == plan_line for line in rfq.line_ids),
            "rfq.line.source_material_plan_line_id: expected plan line link",
            failures,
        )

    order = _create_purchase_order(rfq) if rfq else False
    _expect(bool(order), "purchase_order: expected RFQ-generated purchase order", failures)
    if order:
        _expect(order.plan_id == plan, "purchase_order.plan_id: expected plan link", failures)
        _expect(order.source_material_rfq_id == rfq, "purchase_order.source_material_rfq_id: expected RFQ link", failures)
        _expect(
            all(line.plan_line_id == plan_line for line in order.order_line),
            "purchase_order.line.plan_line_id: expected plan line link",
            failures,
        )
        _expect(
            all(line.source_material_rfq_line_id in rfq.line_ids for line in order.order_line),
            "purchase_order.line.source_material_rfq_line_id: expected RFQ line link",
            failures,
        )

    acceptance = _create_acceptance_from_order(order, shared) if order else False
    _expect(bool(acceptance), "acceptance: expected purchase-order acceptance", failures)
    if acceptance:
        _expect(acceptance.purchase_order_id == order, "acceptance.purchase_order_id: expected order link", failures)
        _expect(acceptance.project_id == shared["project"], "acceptance.project_id: expected project from order", failures)
        _expect(acceptance.supplier_id == shared["supplier"], "acceptance.supplier_id: expected supplier from order", failures)
        _expect(
            all(line.purchase_order_line_id in order.order_line for line in acceptance.line_ids),
            "acceptance.line.purchase_order_line_id: expected order line link",
            failures,
        )

    inbound = _create_inbound_from_acceptance(acceptance, shared) if acceptance else False
    _expect(bool(inbound), "inbound: expected acceptance-generated inbound", failures)
    if inbound:
        _expect(inbound.acceptance_id == acceptance, "inbound.acceptance_id: expected acceptance link", failures)
        _expect(inbound.state == "received", "inbound.state: expected received", failures)
        _expect(
            all(line.acceptance_line_id in acceptance.line_ids for line in inbound.line_ids),
            "inbound.line.acceptance_line_id: expected acceptance line link",
            failures,
        )

    env.flush_all()  # noqa: F821
    summary = _find_stock_summary(shared)
    _expect(bool(summary), "stock_summary: expected inbound from cross-document chain in summary", failures)
    if summary:
        _expect(summary.in_qty >= 4.0, "stock_summary.in_qty: expected >= 4, got %s" % summary.in_qty, failures)
        _expect(summary.in_amount >= 72.0, "stock_summary.in_amount: expected >= 72, got %s" % summary.in_amount, failures)

    evidence = {
        "project": shared["project"].id,
        "material": shared["material"].id,
        "plan": plan.id,
        "plan_line": plan_line.id if plan_line else False,
        "rfq": rfq.id if rfq else False,
        "purchase_order": order.id if order else False,
        "acceptance": acceptance.id if acceptance else False,
        "inbound": inbound.id if inbound else False,
        "summary": summary.id if summary else False,
        "summary_in_qty": summary.in_qty if summary else 0.0,
        "summary_in_amount": summary.in_amount if summary else 0.0,
    }
except Exception as err:
    failures.append("unexpected error: %s" % err)
    failures.append(traceback.format_exc())

result = {
    "audit": "material_cross_document_traceability_audit",
    "status": "PASS" if not failures else "FAIL",
    "evidence": evidence,
    "failures": failures,
}
print("MATERIAL_CROSS_DOCUMENT_TRACEABILITY_AUDIT: %s" % json.dumps(result, ensure_ascii=False, sort_keys=True))
if failures:
    print("FAILURES:")
    for failure in failures:
        print("- %s" % failure)

sys.exit(0 if not failures else 1)
