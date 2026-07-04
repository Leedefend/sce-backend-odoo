# -*- coding: utf-8 -*-
import base64
import json
import sys
import traceback

from odoo import fields
from odoo.exceptions import UserError, ValidationError
from odoo.tools.float_utils import float_compare


def _ensure_groups(env):
    user = env.user.sudo()
    for xmlid in (
        "smart_construction_core.group_sc_cap_project_manager",
        "smart_construction_core.group_sc_cap_finance_user",
        "smart_construction_core.group_sc_cap_finance_manager",
        "smart_construction_core.group_sc_cap_material_manager",
    ):
        group = env.ref(xmlid, raise_if_not_found=False)
        if group and group.id not in user.groups_id.ids:
            user.write({"groups_id": [(4, group.id)]})


def _expect_state(label, record, state, failures):
    record.invalidate_recordset()
    if record.state != state:
        failures.append("%s: expected state=%s, got %s" % (label, state, record.state))
        return False
    return True


def _expect_exception(label, func, failures, exception_types=(UserError, ValidationError)):
    try:
        with env.cr.savepoint():
            func()
    except exception_types:
        return True
    except Exception as err:
        failures.append("%s: expected business exception, got %s: %s" % (label, type(err).__name__, err))
        return False
    failures.append("%s: expected business exception, got success" % label)
    return False


def _assert_amount(label, actual, expected, currency, failures):
    rounding = currency.rounding if currency else 0.01
    if float_compare(actual or 0.0, expected or 0.0, precision_rounding=rounding) != 0:
        failures.append("%s: expected amount=%s, got %s" % (label, expected, actual))
        return False
    return True


def _create_partner(name):
    return env["res.partner"].create({"name": name})


def _create_project(name, code=None, funding=False, cap=100000.0):
    project = env["project.project"].create(
        {
            "name": name,
            "code": code or name.replace(" ", "-").upper(),
            "manager_id": env.user.id,
            "funding_enabled": bool(funding),
            "company_id": env.company.id,
        }
    )
    if funding:
        env["project.funding.baseline"].create(
            {
                "project_id": project.id,
                "total_amount": cap,
                "state": "active",
            }
        )
    return project


def _get_uom_unit():
    uom = env.ref("uom.product_uom_unit", raise_if_not_found=False)
    if uom:
        return uom
    return env["uom.uom"].sudo().search([], limit=1)


def _create_tax(name, tax_use):
    company = env.company
    return env["account.tax"].sudo().create(
        {
            "name": name,
            "amount": 0.0,
            "amount_type": "percent",
            "type_tax_use": tax_use,
            "price_include": False,
            "company_id": company.id,
        }
    )


def _create_contract(project, partner, direction="in"):
    tax_use = "purchase" if direction == "in" else "sale"
    tax = _create_tax("BFC Audit Tax %s" % direction, tax_use)
    return env["construction.contract"].create(
        {
            "subject": "BFC Audit Contract %s" % direction,
            "type": direction,
            "project_id": project.id,
            "partner_id": partner.id,
            "company_id": env.company.id,
            "currency_id": env.company.currency_id.id,
            "tax_id": tax.id,
        }
    )


def _create_purchase_order(partner, amount):
    uom = _get_uom_unit()
    product = env["product.product"].sudo().create(
        {
            "name": "BFC Audit PO Service",
            "type": "service",
            "uom_id": uom.id,
            "uom_po_id": uom.id,
        }
    )
    return env["purchase.order"].create(
        {
            "partner_id": partner.id,
            "company_id": env.company.id,
            "currency_id": env.company.currency_id.id,
            "state": "purchase",
            "order_line": [
                (
                    0,
                    0,
                    {
                        "name": product.name,
                        "product_id": product.id,
                        "product_qty": 1.0,
                        "product_uom": uom.id,
                        "price_unit": amount,
                        "date_planned": fields.Datetime.now(),
                    },
                )
            ],
        }
    )


def _attach_payment(payment):
    env["ir.attachment"].create(
        {
            "name": "business_flow_closure_audit.txt",
            "datas": base64.b64encode(b"business flow closure audit"),
            "res_model": "payment.request",
            "res_id": payment.id,
            "type": "binary",
            "mimetype": "text/plain",
        }
    )


def _run_contract_payment_flow(failures):
    company = env.company
    partner = _create_partner("BFC Audit Contract Supplier")
    project = _create_project("BFC Audit Contract Project", code="BFC-CONTRACT", funding=True)
    contract = _create_contract(project, partner, "in")
    purchase_order = _create_purchase_order(partner, 1000.0)

    settlement = env["sc.settlement.order"].create(
        {
            "project_id": project.id,
            "partner_id": partner.id,
            "contract_id": contract.id,
            "settlement_type": "out",
            "purchase_order_ids": [(6, 0, purchase_order.ids)],
            "company_id": company.id,
            "currency_id": company.currency_id.id,
            "line_ids": [
                (
                    0,
                    0,
                    {
                        "name": "BFC Audit Settlement Line",
                        "contract_id": contract.id,
                        "qty": 1.0,
                        "price_unit": 1000.0,
                    },
                )
            ],
        }
    )

    _expect_exception("contract_payment.settlement_done_before_submit", settlement.action_done, failures)
    settlement.action_submit()
    settlement.invalidate_recordset()
    if settlement.state == "submit":
        env.cr.execute(
            "UPDATE sc_settlement_order SET validation_status=%s WHERE id=%s",
            ("validated", settlement.id),
        )
        settlement.invalidate_recordset()
        settlement.action_on_tier_approved()
    elif settlement.state != "approve":
        failures.append("contract_payment.settlement_submit: expected state=submit or approve, got %s" % settlement.state)
        return {}
    _expect_state("contract_payment.settlement_approve", settlement, "approve", failures)

    payment = env["payment.request"].create(
        {
            "project_id": project.id,
            "partner_id": partner.id,
            "contract_id": contract.id,
            "settlement_id": settlement.id,
            "currency_id": company.currency_id.id,
            "amount": 400.0,
            "type": "pay",
        }
    )
    _attach_payment(payment)
    _expect_exception("contract_payment.payment_done_before_submit", payment.action_done, failures)
    payment.action_submit()
    _expect_state("contract_payment.payment_submit", payment, "submit", failures)
    payment.write({"validation_status": "validated"})
    payment.action_on_tier_approved()
    _expect_state("contract_payment.payment_approved", payment, "approved", failures)
    ledger = payment._ensure_payment_ledger(amount=payment.amount)
    payment.action_done()
    _expect_state("contract_payment.payment_done", payment, "done", failures)
    payment.invalidate_recordset()
    if not payment.is_fully_paid:
        failures.append("contract_payment.payment_fully_paid: expected True")

    settlement.action_done()
    _expect_state("contract_payment.settlement_done", settlement, "done", failures)

    summary = env["sc.contract.recon.summary"].create({"contract_id": contract.id})
    summary.invalidate_recordset()
    _assert_amount("contract_payment.recon_settlement_total", summary.settlement_total, 1000.0, company.currency_id, failures)
    _assert_amount("contract_payment.recon_payment_total", summary.payment_total, 400.0, company.currency_id, failures)
    _assert_amount("contract_payment.recon_delta", summary.delta, 600.0, company.currency_id, failures)
    if summary.settlement_ids_count != 1:
        failures.append("contract_payment.recon_settlement_count: expected 1, got %s" % summary.settlement_ids_count)
    if summary.payment_ids_count != 1:
        failures.append("contract_payment.recon_payment_count: expected 1, got %s" % summary.payment_ids_count)

    return {
        "contract": contract.id,
        "settlement": settlement.id,
        "payment": payment.id,
        "ledger": ledger.id,
        "recon_summary": summary.id,
    }


def _run_material_flow(failures):
    company = env.company
    project = _create_project("BFC Audit Material Project", code="BFC-MATERIAL")
    supplier = _create_partner("BFC Audit Material Supplier")
    uom = _get_uom_unit()
    product = env["product.product"].sudo().create(
        {
            "name": "BFC Audit Material Product",
            "type": "product",
            "uom_id": uom.id,
            "uom_po_id": uom.id,
        }
    )

    request = env["sc.material.purchase.request"].create(
        {
            "project_id": project.id,
            "line_ids": [
                (
                    0,
                    0,
                    {
                        "product_id": product.id,
                        "product_uom_id": uom.id,
                        "qty": 10.0,
                        "estimated_unit_price": 5.0,
                    },
                )
            ],
        }
    )
    _expect_exception("material.request_approve_before_submit", request.action_approve, failures)
    request.action_submit()
    _expect_state("material.request_submit", request, "submitted", failures)
    request.action_approve()
    _expect_state("material.request_approve", request, "approved", failures)

    acceptance = env["sc.material.acceptance"].create(
        {
            "project_id": project.id,
            "supplier_id": supplier.id,
            "purchase_request_id": request.id,
        }
    )
    acceptance.action_submit()
    _expect_state("material.acceptance_submit", acceptance, "submitted", failures)
    acceptance.action_accept()
    _expect_state("material.acceptance_accept", acceptance, "accepted", failures)

    inbound = env["sc.material.inbound"].create(
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
                        "qty": 10.0,
                        "unit_price": 5.0,
                    },
                )
            ],
        }
    )
    _expect_exception("material.inbound_receive_before_submit", inbound.action_receive, failures)
    inbound.action_submit()
    _expect_state("material.inbound_submit", inbound, "submitted", failures)
    inbound.action_receive()
    _expect_state("material.inbound_receive", inbound, "received", failures)
    inbound.invalidate_recordset()
    _assert_amount("material.inbound_tax_included_amount", inbound.tax_included_amount, 50.0, company.currency_id, failures)

    outbound = env["sc.material.outbound"].create(
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
                        "qty": 3.0,
                    },
                )
            ],
        }
    )
    outbound.action_submit()
    _expect_state("material.outbound_submit", outbound, "submitted", failures)
    outbound.action_issue()
    _expect_state("material.outbound_issue", outbound, "issued", failures)

    rfq = env["sc.material.rfq"].create(
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
                        "qty": 10.0,
                        "unit_price": 5.0,
                        "selected": True,
                    },
                )
            ],
        }
    )
    rfq.action_submit()
    _expect_state("material.rfq_submit", rfq, "submitted", failures)
    rfq.action_select()
    _expect_state("material.rfq_select", rfq, "selected", failures)
    if rfq.selected_supplier_id != supplier:
        failures.append("material.rfq_selected_supplier: expected %s, got %s" % (supplier.id, rfq.selected_supplier_id.id))

    settlement = env["sc.material.settlement"].create(
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
                        "qty": 10.0,
                        "unit_price": 5.0,
                    },
                )
            ],
        }
    )
    _expect_exception("material.settlement_confirm_before_submit", settlement.action_confirm, failures)
    settlement.action_submit()
    _expect_state("material.settlement_submit", settlement, "submitted", failures)
    settlement.action_confirm()
    _expect_state("material.settlement_confirm", settlement, "confirmed", failures)

    return {
        "request": request.id,
        "acceptance": acceptance.id,
        "inbound": inbound.id,
        "outbound": outbound.id,
        "rfq": rfq.id,
        "settlement": settlement.id,
    }


failures = []
flows = {}

try:
    _ensure_groups(env)
    flows["contract_payment"] = _run_contract_payment_flow(failures)
    flows["material_stock_settlement"] = _run_material_flow(failures)
except Exception as err:
    failures.append("unexpected error: %s" % err)
    failures.append(traceback.format_exc())

result = {
    "audit": "business_flow_closure_audit",
    "status": "PASS" if not failures else "FAIL",
    "flows": flows,
    "failures": failures,
}

print("BUSINESS_FLOW_CLOSURE_AUDIT: %s" % json.dumps(result, ensure_ascii=False, sort_keys=True))
if failures:
    print("FAILURES:")
    for failure in failures:
        print("- %s" % failure)

sys.exit(0 if not failures else 1)
