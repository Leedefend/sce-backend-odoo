# -*- coding: utf-8 -*-
import base64
import json
import sys
import traceback

from odoo import fields
from odoo.exceptions import UserError, ValidationError


def _token():
    return env["ir.sequence"].sudo().next_by_code("sc.business.fact") or str(fields.Datetime.now())  # noqa: F821


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


def _expect(condition, label, failures):
    if not condition:
        failures.append(label)
        return False
    return True


def _expect_state(label, record, expected, failures):
    record.invalidate_recordset()
    return _expect(record.state == expected, "%s: expected state=%s, got %s" % (label, expected, record.state), failures)


def _expect_exception(label, func, failures):
    try:
        with env.cr.savepoint():  # noqa: F821
            func()
    except (UserError, ValidationError):
        return True
    except Exception as err:
        failures.append("%s: expected business exception, got %s: %s" % (label, type(err).__name__, err))
        return False
    failures.append("%s: expected business exception, got success" % label)
    return False


def _audit_count(record, event_code, action=False):
    domain = [("model", "=", record._name), ("res_id", "=", record.id), ("event_code", "=", event_code)]
    if action:
        domain.append(("action", "=", action))
    return env["sc.audit.log"].sudo().search_count(domain)  # noqa: F821


def _attach(record, name):
    attachment = env["ir.attachment"].sudo().create(  # noqa: F821
        {
            "name": "%s %s.txt" % (name, _token()),
            "type": "binary",
            "datas": base64.b64encode(b"phase3 material handling evidence").decode("ascii"),
            "res_model": record._name,
            "res_id": record.id,
            "mimetype": "text/plain",
        }
    )
    if "attachment_ids" in record._fields:
        record.write({"attachment_ids": [(4, attachment.id)]})
    record.invalidate_recordset()
    return attachment


def _attachment_count(record):
    if "attachment_ids" in record._fields:
        return len(record.attachment_ids)
    return env["ir.attachment"].sudo().search_count([("res_model", "=", record._name), ("res_id", "=", record.id)])  # noqa: F821


def _project():
    return env["project.project"].sudo().create(  # noqa: F821
        {
            "name": "MHE Project %s" % _token(),
            "company_id": env.company.id,  # noqa: F821
            "manager_id": env.user.id,  # noqa: F821
        }
    )


def _supplier():
    return env["res.partner"].sudo().create(  # noqa: F821
        {
            "name": "MHE Supplier %s" % _token(),
            "supplier_rank": 1,
        }
    )


def _product():
    product = env["product.product"].sudo().search([("default_code", "=", "SC-SYSTEM-DEFAULT-MATERIAL")], limit=1)  # noqa: F821
    if product:
        return product
    return env["product.product"].sudo().create(  # noqa: F821
        {
            "name": "系统默认材料（技术兜底）",
            "default_code": "SC-SYSTEM-DEFAULT-MATERIAL",
            "type": "product",
        }
    )


def _material_catalog(project):
    return env["sc.material.catalog"].sudo().create(  # noqa: F821
        {
            "name": "MHE Material %s" % _token(),
            "code": "MHE-%s" % _token(),
            "company_id": env.company.id,  # noqa: F821
            "project_id": project.id,
            "spec_model": "MHE-SPEC",
            "uom_text": "件",
        }
    )


def _warehouse():
    warehouse = env["stock.warehouse"].sudo().search([("company_id", "in", [env.company.id, False])], limit=1)  # noqa: F821
    if warehouse:
        return warehouse
    return env["stock.warehouse"].sudo().create(  # noqa: F821
        {
            "name": "MHE Warehouse",
            "code": "MHE",
            "company_id": env.company.id,  # noqa: F821
        }
    )


def _shared():
    project = _project()
    return {
        "project": project,
        "supplier": _supplier(),
        "product": _product(),
        "material": _material_catalog(project),
        "warehouse": _warehouse(),
    }


def _line_vals(shared, qty_field="qty", price_field=None):
    vals = {
        "product_id": shared["product"].id,
        "material_catalog_id": shared["material"].id,
        "product_uom_id": shared["product"].uom_id.id,
        "material_spec": "MHE-SPEC",
        qty_field: 2.0,
    }
    if price_field:
        vals[price_field] = 10.0
    return vals


def _plan(shared):
    return env["project.material.plan"].sudo().create(  # noqa: F821
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
                        "quantity": 2.0,
                        "bill_qty": 2.0,
                        "uom_id": shared["product"].uom_id.id,
                        "material_uom_text": "件",
                        "vendor_id": shared["supplier"].id,
                    },
                )
            ],
        }
    )


def _purchase_request(shared):
    return env["sc.material.purchase.request"].sudo().create(  # noqa: F821
        {
            "project_id": shared["project"].id,
            "purpose": "MHE采购申请",
            "line_ids": [(0, 0, _line_vals(shared, qty_field="qty", price_field="estimated_unit_price"))],
        }
    )


def _acceptance(shared, request=False):
    return env["sc.material.acceptance"].sudo().create(  # noqa: F821
        {
            "project_id": shared["project"].id,
            "supplier_id": shared["supplier"].id,
            "purchase_request_id": request.id if request else False,
            "warehouse_id": shared["warehouse"].id,
            "dest_location_id": shared["warehouse"].lot_stock_id.id,
            "line_ids": [
                (
                    0,
                    0,
                    dict(
                        _line_vals(shared, qty_field="accepted_qty"),
                        planned_qty=2.0,
                        received_qty=2.0,
                    ),
                )
            ],
        }
    )


def _rfq(shared, plan=False, request=False):
    return env["sc.material.rfq"].sudo().create(  # noqa: F821
        {
            "project_id": shared["project"].id,
            "purchase_request_id": request.id if request else False,
            "source_material_plan_id": plan.id if plan else False,
            "line_ids": [
                (
                    0,
                    0,
                    dict(
                        _line_vals(shared, qty_field="qty", price_field="unit_price"),
                        supplier_id=shared["supplier"].id,
                        selected=True,
                    ),
                )
            ],
        }
    )


def _inbound(shared, acceptance=False):
    return env["sc.material.inbound"].sudo().create(  # noqa: F821
        {
            "project_id": shared["project"].id,
            "supplier_id": shared["supplier"].id,
            "acceptance_id": acceptance.id if acceptance else False,
            "warehouse_id": shared["warehouse"].id,
            "dest_location_id": shared["warehouse"].lot_stock_id.id,
            "line_ids": [(0, 0, _line_vals(shared, qty_field="qty", price_field="unit_price"))],
        }
    )


def _outbound(shared):
    return env["sc.material.outbound"].sudo().create(  # noqa: F821
        {
            "project_id": shared["project"].id,
            "receiver_id": shared["supplier"].id,
            "warehouse_id": shared["warehouse"].id,
            "source_location_id": shared["warehouse"].lot_stock_id.id,
            "purpose": "MHE领用",
            "line_ids": [(0, 0, _line_vals(shared, qty_field="qty"))],
        }
    )


def _settlement(shared):
    return env["sc.material.settlement"].sudo().create(  # noqa: F821
        {
            "project_id": shared["project"].id,
            "supplier_id": shared["supplier"].id,
            "line_ids": [(0, 0, _line_vals(shared, qty_field="qty", price_field="unit_price"))],
        }
    )


def _run_plan(shared, failures):
    plan = _plan(shared)
    _attach(plan, "material-plan")
    _expect(_attachment_count(plan) >= 1, "material_plan.attachment missing", failures)
    _expect_exception("material_plan.done_before_submit", plan.action_done, failures)
    plan.action_submit()
    _expect_state("material_plan.submit", plan, "submit", failures)
    plan.action_approve()
    _expect_state("material_plan.approve", plan, "approved", failures)
    plan.action_done()
    _expect_state("material_plan.done", plan, "done", failures)
    _expect(_audit_count(plan, "material_plan_submitted", "action_submit") >= 1, "material_plan.audit_submit missing", failures)
    _expect(_audit_count(plan, "material_plan_approved", "action_approve") >= 1, "material_plan.audit_approve missing", failures)
    _expect(_audit_count(plan, "material_plan_done", "action_done") >= 1, "material_plan.audit_done missing", failures)
    return plan


def _run_purchase_request(shared, failures):
    request = _purchase_request(shared)
    _expect_exception("purchase_request.approve_before_submit", request.action_approve, failures)
    request.action_submit()
    _expect_state("purchase_request.submit", request, "submitted", failures)
    request.action_approve()
    _expect_state("purchase_request.approve", request, "approved", failures)
    _expect(_audit_count(request, "material_purchase_request_submitted", "action_submit") >= 1, "purchase_request.audit_submit missing", failures)
    _expect(_audit_count(request, "material_purchase_request_approved", "action_approve") >= 1, "purchase_request.audit_approve missing", failures)
    return request


def _run_acceptance(shared, request, failures):
    acceptance = _acceptance(shared, request)
    _attach(acceptance, "material-acceptance")
    _expect(_attachment_count(acceptance) >= 1, "material_acceptance.attachment missing", failures)
    _expect_exception("acceptance.accept_before_submit", acceptance.action_accept, failures)
    acceptance.action_submit()
    _expect_state("acceptance.submit", acceptance, "submitted", failures)
    acceptance.action_accept()
    _expect_state("acceptance.accept", acceptance, "accepted", failures)
    _expect(_audit_count(acceptance, "material_acceptance_submitted", "action_submit") >= 1, "acceptance.audit_submit missing", failures)
    _expect(_audit_count(acceptance, "material_acceptance_accepted", "action_accept") >= 1, "acceptance.audit_accept missing", failures)
    return acceptance


def _run_rfq(shared, plan, request, failures):
    rfq = _rfq(shared, plan, request)
    _attach(rfq, "material-rfq")
    _expect(_attachment_count(rfq) >= 1, "material_rfq.attachment missing", failures)
    _expect_exception("rfq.select_before_submit", rfq.action_select, failures)
    rfq.action_submit()
    _expect_state("rfq.submit", rfq, "submitted", failures)
    rfq.action_select()
    _expect_state("rfq.select", rfq, "selected", failures)
    _expect(rfq.selected_supplier_id == shared["supplier"], "rfq.selected_supplier mismatch", failures)
    _expect(_audit_count(rfq, "material_rfq_submitted", "action_submit") >= 1, "rfq.audit_submit missing", failures)
    _expect(_audit_count(rfq, "material_rfq_selected", "action_select") >= 1, "rfq.audit_select missing", failures)
    return rfq


def _run_inbound(shared, acceptance, failures):
    inbound = _inbound(shared, acceptance)
    _attach(inbound, "material-inbound")
    _expect(_attachment_count(inbound) >= 1, "material_inbound.attachment missing", failures)
    _expect_exception("inbound.receive_before_submit", inbound.action_receive, failures)
    inbound.action_submit()
    _expect_state("inbound.submit", inbound, "submitted", failures)
    inbound.action_receive()
    _expect_state("inbound.receive", inbound, "received", failures)
    _expect(_audit_count(inbound, "material_inbound_submitted", "action_submit") >= 1, "inbound.audit_submit missing", failures)
    _expect(_audit_count(inbound, "material_inbound_received", "action_receive") >= 1, "inbound.audit_receive missing", failures)
    return inbound


def _run_outbound(shared, failures):
    outbound = _outbound(shared)
    _expect_exception("outbound.issue_before_submit", outbound.action_issue, failures)
    outbound.action_submit()
    _expect_state("outbound.submit", outbound, "submitted", failures)
    outbound.action_issue()
    _expect_state("outbound.issue", outbound, "issued", failures)
    _expect(_audit_count(outbound, "material_outbound_submitted", "action_submit") >= 1, "outbound.audit_submit missing", failures)
    _expect(_audit_count(outbound, "material_outbound_issued", "action_issue") >= 1, "outbound.audit_issue missing", failures)
    return outbound


def _run_settlement(shared, failures):
    settlement = _settlement(shared)
    _expect_exception("settlement.confirm_before_submit", settlement.action_confirm, failures)
    settlement.action_submit()
    _expect_state("settlement.submit", settlement, "submitted", failures)
    settlement.action_confirm()
    _expect_state("settlement.confirm", settlement, "confirmed", failures)
    _expect(settlement.amount_total > 0, "settlement.amount_total not computed", failures)
    _expect(_audit_count(settlement, "material_settlement_submitted", "action_submit") >= 1, "settlement.audit_submit missing", failures)
    _expect(_audit_count(settlement, "material_settlement_confirmed", "action_confirm") >= 1, "settlement.audit_confirm missing", failures)
    return settlement


failures = []
evidence = {}

try:
    _ensure_groups()
    shared = _shared()
    plan = _run_plan(shared, failures)
    request = _run_purchase_request(shared, failures)
    acceptance = _run_acceptance(shared, request, failures)
    rfq = _run_rfq(shared, plan, request, failures)
    inbound = _run_inbound(shared, acceptance, failures)
    outbound = _run_outbound(shared, failures)
    settlement = _run_settlement(shared, failures)
    evidence = {
        "project": shared["project"].id,
        "plan": plan.id,
        "purchase_request": request.id,
        "acceptance": acceptance.id,
        "rfq": rfq.id,
        "inbound": inbound.id,
        "outbound": outbound.id,
        "settlement": settlement.id,
    }
except Exception as err:
    failures.append("unexpected error: %s" % err)
    failures.append(traceback.format_exc())

result = {
    "audit": "material_handling_evidence_audit",
    "status": "PASS" if not failures else "FAIL",
    "evidence": evidence,
    "failures": failures,
}
print("MATERIAL_HANDLING_EVIDENCE_AUDIT: %s" % json.dumps(result, ensure_ascii=False, sort_keys=True))
if failures:
    print("FAILURES:")
    for failure in failures:
        print("- %s" % failure)

sys.exit(0 if not failures else 1)
