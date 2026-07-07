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
        "smart_construction_core.group_sc_cap_purchase_user",
        "smart_construction_core.group_sc_cap_purchase_manager",
    ):
        group = env.ref(xmlid, raise_if_not_found=False)  # noqa: F821
        if group and group.id not in user.groups_id.ids:
            user.write({"groups_id": [(4, group.id)]})
    env.invalidate_all()  # noqa: F821


def _project():
    return env["project.project"].sudo().create(  # noqa: F821
        {
            "name": "MPRDS Project %s" % _token(),
            "company_id": env.company.id,  # noqa: F821
            "manager_id": env.user.id,  # noqa: F821
        }
    )


def _supplier():
    return env["res.partner"].sudo().create(  # noqa: F821
        {
            "name": "MPRDS Supplier %s" % _token(),
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
            "name": "MPRDS Warehouse",
            "code": "MPRD",
            "company_id": env.company.id,  # noqa: F821
        }
    )


def _material(project):
    token = _token()
    return env["sc.material.catalog"].sudo().create(  # noqa: F821
        {
            "name": "MPRDS Material %s" % token,
            "code": "MPRDS-%s" % token,
            "company_id": env.company.id,  # noqa: F821
            "project_id": project.id,
            "spec_model": "MPRDS-SPEC",
            "uom_text": "件",
        }
    )


def _create_plan(shared):
    plan = env["project.material.plan"].sudo().create(  # noqa: F821
        {
            "project_id": shared["project"].id,
            "date_plan": fields.Date.context_today(env["project.material.plan"]),  # noqa: F821
            "line_ids": [
                (
                    0,
                    0,
                    {
                        "material_catalog_id": shared["material"].id,
                        "product_id": shared["product"].id,
                        "uom_id": shared["product"].uom_id.id,
                        "quantity": 7.0,
                        "note": "MPRDS计划行",
                    },
                )
            ],
        }
    )
    plan.action_submit()
    plan.action_approve()
    plan.invalidate_recordset()
    return plan


def _prepare_request(plan, supplier):
    plan.action_create_purchase_request()
    request = env["sc.material.purchase.request"].sudo().search(  # noqa: F821
        [
            ("source_material_plan_id", "=", plan.id),
            ("state", "!=", "cancel"),
        ],
        order="id desc",
        limit=1,
    )
    request.write({"supplier_id": supplier.id})
    request.line_ids.write({"estimated_unit_price": 19.0})
    request.action_submit()
    request.action_approve()
    request.invalidate_recordset()
    return request


def _find_rfq(request):
    return env["sc.material.rfq"].sudo().search(  # noqa: F821
        [
            ("purchase_request_id", "=", request.id),
            ("state", "!=", "cancel"),
        ],
        order="id desc",
        limit=1,
    )


def _find_order(request):
    return env["purchase.order"].sudo().search(  # noqa: F821
        [
            ("source_material_purchase_request_id", "=", request.id),
            ("state", "!=", "cancel"),
        ],
        order="id desc",
        limit=1,
    )


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
    request = _prepare_request(plan, shared["supplier"])
    request_line = request.line_ids[:1]

    _expect(request.state == "approved", "request.state: expected approved", failures)
    _expect(request.supplier_id == shared["supplier"], "request.supplier_id: expected supplier", failures)

    rfq_action = request.action_create_rfq()
    rfq = _find_rfq(request)
    _expect(bool(rfq), "rfq: expected request-generated RFQ", failures)
    _expect(rfq_action.get("res_model") == "sc.material.rfq", "rfq.action: expected RFQ action", failures)
    if rfq:
        _expect(rfq.purchase_request_id == request, "rfq.purchase_request_id: expected request link", failures)
        _expect(rfq.source_material_plan_id == plan, "rfq.source_material_plan_id: expected plan link", failures)
        _expect(
            all(line.source_material_purchase_request_line_id in request.line_ids for line in rfq.line_ids),
            "rfq.line.source_material_purchase_request_line_id: expected request line link",
            failures,
        )
        _expect(
            all(line.source_material_plan_line_id == plan_line for line in rfq.line_ids),
            "rfq.line.source_material_plan_line_id: expected plan line link",
            failures,
        )
        second_rfq_action = request.action_create_rfq()
        second_rfq = _find_rfq(request)
        _expect(second_rfq == rfq, "rfq.idempotent: expected existing RFQ", failures)
        _expect(second_rfq_action.get("res_id") == rfq.id, "rfq.idempotent.action: expected existing RFQ", failures)

    order_action = request.action_create_purchase_order()
    order = _find_order(request)
    _expect(bool(order), "purchase_order: expected request-generated purchase order", failures)
    _expect(order_action.get("res_model") == "purchase.order", "purchase_order.action: expected purchase order action", failures)
    if order:
        _expect(order.source_material_purchase_request_id == request, "purchase_order.source_request: expected request link", failures)
        _expect(order.plan_id == plan, "purchase_order.plan_id: expected plan link", failures)
        _expect(order.partner_id == shared["supplier"], "purchase_order.partner_id: expected supplier", failures)
        _expect(
            all(line.source_material_purchase_request_line_id in request.line_ids for line in order.order_line),
            "purchase_order.line.source_request_line: expected request line link",
            failures,
        )
        _expect(
            all(line.plan_line_id == plan_line for line in order.order_line),
            "purchase_order.line.plan_line_id: expected plan line link",
            failures,
        )
        line = order.order_line[:1]
        _expect(line.source_material_purchase_request_line_id == request_line, "purchase_order.line: expected source request line", failures)
        _expect(line.price_unit == request_line.estimated_unit_price, "purchase_order.line.price_unit: expected request estimate", failures)

        second_order_action = request.action_create_purchase_order()
        second_order = _find_order(request)
        _expect(second_order == order, "purchase_order.idempotent: expected existing order", failures)
        _expect(second_order_action.get("res_id") == order.id, "purchase_order.idempotent.action: expected existing order", failures)

        acceptance = _create_acceptance_from_order(order, shared)
        _expect(acceptance.purchase_order_id == order, "acceptance.purchase_order_id: expected order link", failures)
        _expect(
            all(line.purchase_order_line_id.source_material_purchase_request_line_id in request.line_ids for line in acceptance.line_ids),
            "acceptance.line.purchase_order_line.source_request_line: expected request traceability",
            failures,
        )
    else:
        acceptance = False

    evidence = {
        "project": shared["project"].id,
        "material": shared["material"].id,
        "plan": plan.id,
        "plan_line": plan_line.id,
        "purchase_request": request.id,
        "purchase_request_line": request_line.id,
        "rfq": rfq.id if rfq else False,
        "purchase_order": order.id if order else False,
        "acceptance": acceptance.id if acceptance else False,
    }
except Exception as err:
    failures.append("unexpected error: %s" % err)
    failures.append(traceback.format_exc())

result = {
    "audit": "material_purchase_request_downstream_strategy_audit",
    "status": "PASS" if not failures else "FAIL",
    "evidence": evidence,
    "failures": failures,
}
print("MATERIAL_PURCHASE_REQUEST_DOWNSTREAM_STRATEGY_AUDIT: %s" % json.dumps(result, ensure_ascii=False, sort_keys=True))
if failures:
    print("FAILURES:")
    for failure in failures:
        print("- %s" % failure)

sys.exit(0 if not failures else 1)
