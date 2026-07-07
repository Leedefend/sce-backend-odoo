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
            "name": "MPPR Project %s" % _token(),
            "company_id": env.company.id,  # noqa: F821
            "manager_id": env.user.id,  # noqa: F821
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
            "name": "MPPR Warehouse",
            "code": "MPPR",
            "company_id": env.company.id,  # noqa: F821
        }
    )


def _material(project):
    token = _token()
    return env["sc.material.catalog"].sudo().create(  # noqa: F821
        {
            "name": "MPPR Material %s" % token,
            "code": "MPPR-%s" % token,
            "company_id": env.company.id,  # noqa: F821
            "project_id": project.id,
            "spec_model": "MPPR-SPEC",
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
                        "quantity": 6.0,
                        "note": "MPPR计划行",
                    },
                )
            ],
        }
    )
    plan.action_submit()
    plan.action_approve()
    plan.invalidate_recordset()
    return plan


def _find_request(plan):
    return env["sc.material.purchase.request"].sudo().search(  # noqa: F821
        [
            ("source_material_plan_id", "=", plan.id),
            ("state", "!=", "cancel"),
        ],
        order="id desc",
        limit=1,
    )


def _create_acceptance(request, shared):
    acceptance = env["sc.material.acceptance"].sudo().create(  # noqa: F821
        {
            "purchase_request_id": request.id,
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
        "product": _product(),
        "warehouse": _warehouse(),
    }
    shared["material"] = _material(shared["project"])
    plan = _create_plan(shared)
    plan_line = plan.line_ids[:1]

    action = plan.action_create_purchase_request()
    request = _find_request(plan)
    _expect(bool(request), "purchase_request: expected generated request from material plan", failures)
    _expect(action.get("res_model") == "sc.material.purchase.request", "action: expected purchase request form action", failures)
    if request:
        _expect(request.source_material_plan_id == plan, "request.source_material_plan_id: expected plan link", failures)
        _expect(request.project_id == plan.project_id, "request.project_id: expected plan project", failures)
        _expect(request.required_date == plan.date_plan, "request.required_date: expected plan date", failures)
        _expect(len(request.line_ids) == len(plan.line_ids), "request.line_ids: expected one line per plan line", failures)
        _expect(
            all(line.source_material_plan_line_id in plan.line_ids for line in request.line_ids),
            "request.line.source_material_plan_line_id: expected plan line link",
            failures,
        )
        line = request.line_ids[:1]
        _expect(line.source_material_plan_line_id == plan_line, "request.line: expected source plan line", failures)
        _expect(line.material_catalog_id == plan_line.material_catalog_id, "request.line: expected material catalog", failures)
        _expect(line.qty == plan_line.quantity, "request.line.qty: expected plan quantity", failures)

        second_action = plan.action_create_purchase_request()
        second_request = _find_request(plan)
        _expect(second_request == request, "purchase_request.idempotent: expected existing request", failures)
        _expect(second_action.get("res_id") == request.id, "purchase_request.idempotent: expected existing request action", failures)

        request.action_submit()
        request.action_approve()
        request.invalidate_recordset()
        _expect(request.state == "approved", "request.state: expected approved", failures)

        acceptance = _create_acceptance(request, shared)
        _expect(acceptance.purchase_request_id == request, "acceptance.purchase_request_id: expected request link", failures)
        _expect(
            all(line.purchase_request_line_id.source_material_plan_line_id in plan.line_ids for line in acceptance.line_ids),
            "acceptance.line.purchase_request_line_id.source_material_plan_line_id: expected plan traceability",
            failures,
        )
    else:
        acceptance = False

    evidence = {
        "project": shared["project"].id,
        "material": shared["material"].id,
        "plan": plan.id,
        "plan_line": plan_line.id,
        "purchase_request": request.id if request else False,
        "purchase_request_line": request.line_ids[:1].id if request and request.line_ids else False,
        "acceptance": acceptance.id if acceptance else False,
    }
except Exception as err:
    failures.append("unexpected error: %s" % err)
    failures.append(traceback.format_exc())

result = {
    "audit": "material_plan_purchase_request_traceability_audit",
    "status": "PASS" if not failures else "FAIL",
    "evidence": evidence,
    "failures": failures,
}
print("MATERIAL_PLAN_PURCHASE_REQUEST_TRACEABILITY_AUDIT: %s" % json.dumps(result, ensure_ascii=False, sort_keys=True))
if failures:
    print("FAILURES:")
    for failure in failures:
        print("- %s" % failure)

sys.exit(0 if not failures else 1)
