# -*- coding: utf-8 -*-
import json
import sys
import traceback

from odoo import fields
from odoo.exceptions import AccessError, UserError, ValidationError


def _token():
    return env["ir.sequence"].sudo().next_by_code("sc.business.fact") or str(fields.Datetime.now())


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
        with env.cr.savepoint():
            func()
    except (AccessError, UserError, ValidationError):
        return True
    except Exception as err:
        failures.append("%s: expected permission/business exception, got %s: %s" % (label, type(err).__name__, err))
        return False
    failures.append("%s: expected permission/business exception, got success" % label)
    return False


def _set_validated(record, table):
    env.flush_all()
    env.cr.execute("UPDATE %s SET validation_status=%%s WHERE id=%%s" % table, ("validated", record.id))
    env.invalidate_all()
    record.invalidate_recordset()
    if "validation_status" in record._fields and record.validation_status != "validated":
        record.sudo().with_context(skip_validation_check=True).write({"validation_status": "validated"})
        env.flush_all()
        env.invalidate_all()
        record.invalidate_recordset()


def _group(xmlid):
    return env.ref(xmlid).id


def _audit_user(login, name, group_xmlids):
    User = env["res.users"].sudo().with_context(no_reset_password=True, tracking_disable=True)
    user = User.search([("login", "=", login)], limit=1)
    normalized_group_xmlids = ["smart_construction_core.group_sc_internal_user"] + list(group_xmlids)
    values = {
        "name": name,
        "login": login,
        "email": "%s@example.invalid" % login,
        "company_id": env.company.id,
        "company_ids": [(6, 0, [env.company.id])],
        "groups_id": [(6, 0, [_group(xmlid) for xmlid in normalized_group_xmlids])],
    }
    if user:
        user.write(values)
    else:
        user = User.create(values)
    return user


def _users():
    suffix = "material_role_audit"
    return {
        "material_read": _audit_user(
            "sc_%s_material_read" % suffix,
            "审计-物资只读",
            ["smart_construction_core.group_sc_cap_material_read"],
        ),
        "material_user": _audit_user(
            "sc_%s_material_user" % suffix,
            "审计-物资经办",
            ["smart_construction_core.group_sc_cap_material_user"],
        ),
        "material_manager": _audit_user(
            "sc_%s_material_manager" % suffix,
            "审计-物资审批",
            ["smart_construction_core.group_sc_cap_material_manager"],
        ),
        "purchase_user": _audit_user(
            "sc_%s_purchase_user" % suffix,
            "审计-采购经办",
            ["smart_construction_core.group_sc_cap_purchase_user"],
        ),
        "purchase_manager": _audit_user(
            "sc_%s_purchase_manager" % suffix,
            "审计-采购审批",
            ["smart_construction_core.group_sc_cap_purchase_manager"],
        ),
        "finance_user": _audit_user(
            "sc_%s_finance_user" % suffix,
            "审计-财务经办",
            ["smart_construction_core.group_sc_cap_finance_user"],
        ),
        "finance_manager": _audit_user(
            "sc_%s_finance_manager" % suffix,
            "审计-财务审批",
            ["smart_construction_core.group_sc_cap_finance_manager"],
        ),
    }


def _partner(name, supplier=False):
    return env["res.partner"].sudo().create(
        {
            "name": "%s %s" % (name, _token()),
            "supplier_rank": 1 if supplier else 0,
        }
    )


def _project(name):
    project = env["project.project"].sudo().create(
        {
            "name": "%s %s" % (name, _token()),
            "manager_id": env.user.id,
            "company_id": env.company.id,
        }
    )
    return project


def _grant_project_visibility(project, users):
    partner_ids = [user.partner_id.id for user in users.values() if user.partner_id]
    if partner_ids:
        project.sudo().message_subscribe(partner_ids=partner_ids)


def _material():
    uom = env.ref("uom.product_uom_unit", raise_if_not_found=False) or env["uom.uom"].sudo().search([], limit=1)
    product = env["product.product"].sudo().create(
        {
            "name": "MRPA Material %s" % _token(),
            "default_code": "MRPA-%s" % _token(),
            "type": "product",
            "uom_id": uom.id,
            "uom_po_id": uom.id,
        }
    )
    return product, uom


def _request_values(project, supplier, product, uom, qty=2.0, price=15.0):
    return {
        "project_id": project.id,
        "supplier_id": supplier.id,
        "line_ids": [
            (
                0,
                0,
                {
                    "product_id": product.id,
                    "product_uom_id": uom.id,
                    "qty": qty,
                    "estimated_unit_price": price,
                },
            )
        ],
    }


def _accepted_acceptance(project, supplier, product, uom, users):
    acceptance = env["sc.material.acceptance"].sudo().create(
        {
            "project_id": project.id,
            "supplier_id": supplier.id,
            "line_ids": [
                (
                    0,
                    0,
                    {
                        "product_id": product.id,
                        "product_uom_id": uom.id,
                        "received_qty": 2.0,
                        "accepted_qty": 2.0,
                        "result": "accepted",
                    },
                )
            ],
        }
    )
    acceptance.with_user(users["material_user"]).action_submit()
    acceptance.with_user(users["material_manager"]).action_accept()
    return acceptance


def _run_purchase_request_roles(users, failures):
    project = _project("MRPA Purchase Request Project")
    _grant_project_visibility(project, users)
    supplier = _partner("MRPA Supplier", supplier=True)
    product, uom = _material()

    denied = env["sc.material.purchase.request"].sudo().create(_request_values(project, supplier, product, uom))
    _expect_exception(
        "material_purchase_request.read_submit_blocked",
        denied.with_user(users["material_read"]).action_submit,
        failures,
    )

    request = env["sc.material.purchase.request"].sudo().create(_request_values(project, supplier, product, uom))
    request.with_user(users["material_user"]).action_submit()
    _expect_state("material_purchase_request.material_user_submit", request, "submitted", failures)
    _expect_exception(
        "material_purchase_request.material_user_approve_blocked",
        request.with_user(users["material_user"]).action_approve,
        failures,
    )
    request.with_user(users["purchase_manager"]).action_approve()
    _expect_state("material_purchase_request.purchase_manager_approve", request, "approved", failures)

    _expect_exception(
        "material_purchase_request.read_generate_rfq_blocked",
        request.with_user(users["material_read"]).action_create_rfq,
        failures,
    )
    action = request.with_user(users["purchase_user"]).action_create_rfq()
    rfq = env["sc.material.rfq"].sudo().browse(action.get("res_id"))
    _expect(rfq and rfq.exists(), "material_purchase_request.purchase_user_generate_rfq", failures)
    _expect_exception(
        "material_purchase_request.purchase_user_direct_po_blocked",
        request.with_user(users["purchase_user"]).action_create_purchase_order,
        failures,
    )
    po_action = request.with_user(users["purchase_manager"]).action_create_purchase_order()
    _expect(bool(po_action.get("res_id")), "material_purchase_request.purchase_manager_generate_po", failures)
    return {"purchase_request": request.id, "rfq": rfq.id if rfq else False}


def _run_acceptance_stock_roles(users, failures):
    project = _project("MRPA Stock Project")
    _grant_project_visibility(project, users)
    supplier = _partner("MRPA Stock Supplier", supplier=True)
    product, uom = _material()

    acceptance = env["sc.material.acceptance"].sudo().create(
        {
            "project_id": project.id,
            "supplier_id": supplier.id,
            "line_ids": [
                (
                    0,
                    0,
                    {
                        "product_id": product.id,
                        "product_uom_id": uom.id,
                        "received_qty": 2.0,
                        "accepted_qty": 2.0,
                        "result": "accepted",
                    },
                )
            ],
        }
    )
    _expect_exception(
        "material_acceptance.read_submit_blocked",
        acceptance.with_user(users["material_read"]).action_submit,
        failures,
    )
    acceptance.with_user(users["material_user"]).action_submit()
    _expect_exception(
        "material_acceptance.material_user_accept_blocked",
        acceptance.with_user(users["material_user"]).action_accept,
        failures,
    )
    acceptance.with_user(users["material_manager"]).action_accept()
    _expect_state("material_acceptance.material_manager_accept", acceptance, "accepted", failures)

    inbound = env["sc.material.inbound"].sudo().create(
        {
            "project_id": project.id,
            "supplier_id": supplier.id,
            "acceptance_id": acceptance.id,
            "line_ids": [
                (
                    0,
                    0,
                    {
                        "product_id": product.id,
                        "product_uom_id": uom.id,
                        "qty": 2.0,
                        "unit_price": 15.0,
                    },
                )
            ],
        }
    )
    _expect_exception("material_inbound.read_submit_blocked", inbound.with_user(users["material_read"]).action_submit, failures)
    inbound.with_user(users["material_user"]).action_submit()
    _expect_exception("material_inbound.material_user_receive_blocked", inbound.with_user(users["material_user"]).action_receive, failures)
    inbound.with_user(users["material_manager"]).action_receive()
    _expect_state("material_inbound.material_manager_receive", inbound, "received", failures)

    outbound = env["sc.material.outbound"].sudo().create(
        {
            "project_id": project.id,
            "receiver_id": supplier.id,
            "line_ids": [
                (
                    0,
                    0,
                    {
                        "product_id": product.id,
                        "product_uom_id": uom.id,
                        "qty": 1.0,
                        "unit_price": 15.0,
                    },
                )
            ],
        }
    )
    _expect_exception("material_outbound.read_submit_blocked", outbound.with_user(users["material_read"]).action_submit, failures)
    outbound.with_user(users["material_user"]).action_submit()
    _expect_exception("material_outbound.material_user_issue_blocked", outbound.with_user(users["material_user"]).action_issue, failures)
    outbound.with_user(users["material_manager"]).action_issue()
    _expect_state("material_outbound.material_manager_issue", outbound, "issued", failures)

    return {"acceptance": acceptance.id, "inbound": inbound.id, "outbound": outbound.id}


def _run_rfq_roles(users, failures):
    project = _project("MRPA RFQ Project")
    _grant_project_visibility(project, users)
    supplier = _partner("MRPA RFQ Supplier", supplier=True)
    product, uom = _material()
    rfq = env["sc.material.rfq"].sudo().create(
        {
            "project_id": project.id,
            "line_ids": [
                (
                    0,
                    0,
                    {
                        "supplier_id": supplier.id,
                        "product_id": product.id,
                        "product_uom_id": uom.id,
                        "qty": 2.0,
                        "unit_price": 15.0,
                        "selected": True,
                    },
                )
            ],
        }
    )
    _expect_exception("material_rfq.read_submit_blocked", rfq.with_user(users["material_read"]).action_submit, failures)
    rfq.with_user(users["purchase_user"]).action_submit()
    _expect_state("material_rfq.purchase_user_submit", rfq, "submitted", failures)
    _expect_exception("material_rfq.purchase_user_select_blocked", rfq.with_user(users["purchase_user"]).action_select, failures)
    rfq.with_user(users["purchase_manager"]).action_select()
    _expect_state("material_rfq.purchase_manager_select", rfq, "selected", failures)
    po_action = rfq.with_user(users["purchase_manager"]).action_create_purchase_order()
    _expect(bool(po_action.get("res_id")), "material_rfq.purchase_manager_generate_po", failures)
    return {"rfq_direct": rfq.id}


def _run_settlement_finance_roles(users, failures):
    project = _project("MRPA Settlement Project")
    _grant_project_visibility(project, users)
    supplier = _partner("MRPA Settlement Supplier", supplier=True)
    product, uom = _material()
    settlement = env["sc.material.settlement"].sudo().create(
        {
            "project_id": project.id,
            "supplier_id": supplier.id,
            "line_ids": [
                (
                    0,
                    0,
                    {
                        "product_id": product.id,
                        "product_uom_id": uom.id,
                        "qty": 2.0,
                        "unit_price": 15.0,
                    },
                )
            ],
        }
    )
    _expect_exception(
        "material_settlement.read_submit_blocked",
        settlement.with_user(users["material_read"]).action_submit,
        failures,
    )
    settlement.with_user(users["material_user"]).action_submit()
    _expect_exception(
        "material_settlement.material_user_confirm_blocked",
        settlement.with_user(users["material_user"]).action_confirm,
        failures,
    )
    settlement.with_user(users["material_manager"]).action_confirm()
    _expect_state("material_settlement.material_manager_confirm", settlement, "confirmed", failures)
    settlement.invalidate_recordset()
    request = settlement.payment_request_id
    _expect(request and request.exists(), "material_settlement.confirm_generates_payment_request", failures)
    if request:
        _expect_exception(
            "material_settlement_payment.material_user_submit_blocked",
            request.with_user(users["material_user"]).action_submit,
            failures,
        )
        request.with_user(users["finance_user"]).action_submit()
        _expect_state("material_settlement_payment.finance_user_submit", request, "submit", failures)
        _set_validated(request, "payment_request")
        request.with_user(users["finance_manager"]).action_on_tier_approved()
        _expect_state("material_settlement_payment.finance_manager_approve", request, "approved", failures)
    return {"settlement": settlement.id, "payment_request": request.id if request else False}


failures = []
coverage = {}

try:
    users = _users()
    coverage.update(_run_purchase_request_roles(users, failures))
    coverage.update(_run_acceptance_stock_roles(users, failures))
    coverage.update(_run_rfq_roles(users, failures))
    coverage.update(_run_settlement_finance_roles(users, failures))
except Exception as err:
    failures.append("unexpected error: %s" % err)
    failures.append(traceback.format_exc())

result = {
    "audit": "material_role_permission_audit",
    "status": "PASS" if not failures else "FAIL",
    "coverage": coverage,
    "failures": failures,
}
print("MATERIAL_ROLE_PERMISSION_AUDIT: %s" % json.dumps(result, ensure_ascii=False, sort_keys=True))
if failures:
    sys.exit(1)
