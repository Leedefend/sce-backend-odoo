# -*- coding: utf-8 -*-
import base64
import json
import sys
import traceback
import uuid

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


def _force_validated(record, table_name):
    env.flush_all()
    env.cr.execute("UPDATE %s SET validation_status=%%s WHERE id=%%s" % table_name, ("validated", record.id))
    record.invalidate_recordset()
    if record.validation_status != "validated":
        record.write({"validation_status": "validated"})
        record.invalidate_recordset()


def _attach_proof(record, label):
    attachment = env["ir.attachment"].sudo().create(
        {
            "name": "%s.txt" % label,
            "datas": base64.b64encode(("proof:%s" % label).encode("utf-8")).decode("ascii"),
            "res_model": record._name,
            "res_id": record.id,
            "mimetype": "text/plain",
        }
    )
    if "attachment_ids" in record._fields:
        record.sudo().write({"attachment_ids": [(4, attachment.id)]})
    return attachment


def _partner(name):
    return env["res.partner"].create({"name": name})


def _project(name, code, funding=False, cap=100000.0):
    project = env["project.project"].create(
        {
            "name": name,
            "code": code,
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


def _uom_unit():
    return env.ref("uom.product_uom_unit", raise_if_not_found=False) or env["uom.uom"].sudo().search([], limit=1)


RUN_TOKEN = uuid.uuid4().hex[:8]


def _name(prefix):
    return "%s %s" % (prefix, RUN_TOKEN)


def _tax(name, tax_use):
    return env["account.tax"].sudo().create(
        {
            "name": "%s %s" % (_name(name), uuid.uuid4().hex[:6]),
            "amount": 0.0,
            "amount_type": "percent",
            "type_tax_use": tax_use,
            "price_include": False,
            "company_id": env.company.id,
        }
    )


def _contract(project, partner, direction="in"):
    return env["construction.contract"].create(
        {
            "subject": _name("CDP Gate Contract %s" % direction),
            "type": direction,
            "project_id": project.id,
            "partner_id": partner.id,
            "company_id": env.company.id,
            "currency_id": env.company.currency_id.id,
            "tax_id": _tax("CDP Gate Tax %s" % direction, "purchase" if direction == "in" else "sale").id,
        }
    )


def _purchase_order(partner, amount):
    uom = _uom_unit()
    product = env["product.product"].sudo().create(
        {
            "name": _name("CDP Gate PO Service"),
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


def _settlement(project, partner, contract, amount, settlement_type="out"):
    purchase_order = _purchase_order(partner, amount)
    return env["sc.settlement.order"].create(
        {
            "project_id": project.id,
            "partner_id": partner.id,
            "contract_id": contract.id,
            "settlement_type": settlement_type,
            "purchase_order_ids": [(6, 0, purchase_order.ids)],
            "company_id": env.company.id,
            "currency_id": env.company.currency_id.id,
            "line_ids": [
                (
                    0,
                    0,
                    {
                        "name": _name("CDP Gate Settlement Line"),
                        "contract_id": contract.id,
                        "qty": 1.0,
                        "price_unit": amount,
                    },
                )
            ],
        }
    )


def _approve_settlement(settlement, failures, label):
    _expect_exception("%s.done_before_submit" % label, settlement.action_done, failures)
    settlement.action_submit()
    settlement.invalidate_recordset()
    if settlement.state == "submit":
        _force_validated(settlement, "sc_settlement_order")
        settlement.action_on_tier_approved()
    elif settlement.state != "approve":
        failures.append("%s.submit: expected state=submit or approve, got %s" % (label, settlement.state))
        return
    _expect_state("%s.approve" % label, settlement, "approve", failures)


def _attach_payment(payment):
    env["ir.attachment"].create(
        {
            "name": "core_document_processing_gate.txt",
            "datas": base64.b64encode(b"core document processing gate"),
            "res_model": "payment.request",
            "res_id": payment.id,
            "type": "binary",
            "mimetype": "text/plain",
        }
    )


def _payment_request(project, partner, contract, settlement, amount, request_type="pay"):
    payment = env["payment.request"].create(
        {
            "project_id": project.id,
            "partner_id": partner.id,
            "contract_id": contract.id,
            "settlement_id": settlement.id,
            "currency_id": env.company.currency_id.id,
            "amount": amount,
            "type": request_type,
        }
    )
    _attach_payment(payment)
    return payment


def _approve_payment(payment, failures, label):
    _expect_exception("%s.done_before_submit" % label, payment.action_done, failures)
    payment.action_submit()
    _expect_state("%s.submit" % label, payment, "submit", failures)
    _force_validated(payment, "payment_request")
    payment.action_on_tier_approved()
    _expect_state("%s.approved" % label, payment, "approved", failures)


def _run_settlement_payment(failures):
    project = _project(_name("CDP Gate Contract Project"), _name("CDP-CONTRACT"), funding=True)
    partner = _partner(_name("CDP Gate Contract Supplier"))
    contract = _contract(project, partner, "in")
    settlement = _settlement(project, partner, contract, 1200.0)

    _approve_settlement(settlement, failures, "settlement_payment.settlement")
    payment = _payment_request(project, partner, contract, settlement, 450.0)
    _approve_payment(payment, failures, "settlement_payment.payment")
    payment.action_done()
    _expect_state("settlement_payment.payment.done", payment, "done", failures)
    payment.invalidate_recordset()
    if not payment.is_fully_paid:
        failures.append("settlement_payment.payment.fully_paid: expected True")

    settlement.action_done()
    _expect_state("settlement_payment.settlement.done", settlement, "done", failures)
    _assert_amount("settlement_payment.amount_total", settlement.amount_total, 1200.0, env.company.currency_id, failures)

    cancel_settlement = _settlement(project, partner, contract, 100.0)
    cancel_settlement.action_cancel()
    _expect_state("settlement_payment.cancel", cancel_settlement, "cancel", failures)
    return {
        "settlement": settlement.id,
        "payment": payment.id,
        "cancel_settlement": cancel_settlement.id,
    }


def _run_expense_claims(failures):
    project = _project(_name("CDP Gate Expense Project"), _name("CDP-EXPENSE"), funding=True)
    partner = _partner(_name("CDP Gate Expense Partner"))
    claim_specs = [
        ("expense", "公司财务支出", "pay"),
        ("deposit_pay", "付款还保证金", "pay"),
        ("deposit_refund", "付款保证金退回", "receive"),
        ("deduction_refund", "扣款实缴退回", "pay"),
    ]
    interfund_claim_specs = [
        ("project_company_repay", "还款登记"),
        ("deposit_receive", "承包人还项目款"),
    ]
    claim_ids = {}
    payment_ids = {}

    for index, (claim_type, expense_type, payment_type) in enumerate(claim_specs, start=1):
        amount = 70.0 + index
        if claim_type == "deposit_refund":
            amount = 60.0
        contract = _contract(project, partner, "in" if payment_type == "pay" else "out")
        settlement = _settlement(
            project,
            partner,
            contract,
            amount,
            settlement_type="out" if payment_type == "pay" else "in",
        )
        _approve_settlement(settlement, failures, "expense_claim.%s.settlement" % claim_type)
        payment = _payment_request(project, partner, contract, settlement, amount, request_type=payment_type)
        _approve_payment(payment, failures, "expense_claim.%s.payment" % claim_type)
        claim = env["sc.expense.claim"].sudo().create(
            {
                "claim_type": claim_type,
                "expense_type": expense_type,
                "project_id": project.id,
                "partner_id": partner.id,
                "payment_request_id": payment.id,
                "amount": amount,
                "approved_amount": amount,
                "paid_amount": 0.0,
                "summary": _name("CDP Gate %s" % expense_type),
                "payee": _name("CDP Gate Payee"),
                "receipt_account_name": _name("CDP Gate Receipt Account"),
                "payee_account": _name("CDP-GATE-RECEIPT"),
                "payment_account_name": _name("CDP Gate Payment Account"),
                "payer_account": _name("CDP-GATE-PAYER"),
            }
        )
        _attach_proof(claim, "expense-claim-%s" % claim_type)
        _expect_exception("expense_claim.%s.done_before_submit" % claim_type, claim.action_done, failures)
        claim.action_submit()
        if claim.state == "submit":
            _force_validated(claim, "sc_expense_claim")
            claim.action_on_tier_approved()
        _expect_state("expense_claim.%s.approved" % claim_type, claim, "approved", failures)
        claim.action_done()
        _expect_state("expense_claim.%s.done" % claim_type, claim, "done", failures)
        payment.invalidate_recordset()
        if payment.state != "done":
            failures.append("expense_claim.%s.payment_done: expected done, got %s" % (claim_type, payment.state))
        claim_ids[claim_type] = claim.id
        payment_ids[claim_type] = payment.id

    for index, (claim_type, expense_type) in enumerate(interfund_claim_specs, start=1):
        amount = 90.0 + index
        claim = env["sc.expense.claim"].sudo().create(
            {
                "claim_type": claim_type,
                "expense_type": expense_type,
                "project_id": project.id,
                "partner_id": partner.id,
                "amount": amount,
                "approved_amount": amount,
                "paid_amount": 0.0,
                "summary": _name("CDP Gate %s" % expense_type),
                "payee": _name("CDP Gate Interfund Payee"),
                "receipt_account_name": _name("CDP Gate Interfund Receipt Account"),
                "payee_account": _name("CDP-GATE-INTERFUND-RECEIPT"),
                "payment_account_name": _name("CDP Gate Interfund Payment Account"),
                "payer_account": _name("CDP-GATE-INTERFUND-PAYER"),
            }
        )
        _attach_proof(claim, "expense-claim-%s" % expense_type)
        _expect_exception("expense_claim.%s.done_before_submit" % expense_type, claim.action_done, failures)
        claim.action_submit()
        if claim.state == "submit":
            _force_validated(claim, "sc_expense_claim")
            claim.action_on_tier_approved()
        _expect_state("expense_claim.%s.approved" % expense_type, claim, "approved", failures)
        claim.action_done()
        _expect_state("expense_claim.%s.done" % expense_type, claim, "done", failures)
        if claim.payment_request_id:
            failures.append("expense_claim.%s.payment_request: expected empty" % expense_type)
        claim_ids[expense_type] = claim.id

    cancel_claim = env["sc.expense.claim"].sudo().create(
        {
            "claim_type": "expense",
            "expense_type": "取消验证",
            "project_id": project.id,
            "partner_id": partner.id,
            "amount": 10.0,
            "approved_amount": 10.0,
        }
    )
    cancel_claim.action_cancel()
    _expect_state("expense_claim.cancel", cancel_claim, "cancel", failures)
    claim_ids["cancel"] = cancel_claim.id
    return {"claims": claim_ids, "payments": payment_ids}


def _run_material_inbound(failures):
    project = _project(_name("CDP Gate Material Project"), _name("CDP-MATERIAL"))
    supplier = _partner(_name("CDP Gate Material Supplier"))
    uom = _uom_unit()
    product = env["product.product"].sudo().create(
        {
            "name": _name("CDP Gate Material Product"),
            "type": "product",
            "uom_id": uom.id,
            "uom_po_id": uom.id,
        }
    )
    inbound = env["sc.material.inbound"].create(
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
                        "qty": 12.0,
                        "unit_price": 8.0,
                    },
                )
            ],
        }
    )
    _expect_exception("material_inbound.receive_before_submit", inbound.action_receive, failures)
    inbound.action_submit()
    _expect_state("material_inbound.submit", inbound, "submitted", failures)
    inbound.action_receive()
    _expect_state("material_inbound.received", inbound, "received", failures)
    inbound.invalidate_recordset()
    _assert_amount("material_inbound.amount_total", inbound.amount_total, 96.0, env.company.currency_id, failures)

    cancel_inbound = env["sc.material.inbound"].create(
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
                        "qty": 1.0,
                        "unit_price": 8.0,
                    },
                )
            ],
        }
    )
    cancel_inbound.action_cancel()
    _expect_state("material_inbound.cancel", cancel_inbound, "cancel", failures)
    cancel_inbound.action_reset_draft()
    _expect_state("material_inbound.reset_draft", cancel_inbound, "draft", failures)
    return {"inbound": inbound.id, "cancel_inbound": cancel_inbound.id}


failures = []
flows = {}

try:
    _ensure_groups(env)
    flows["settlement_payment"] = _run_settlement_payment(failures)
    flows["expense_claims"] = _run_expense_claims(failures)
    flows["material_inbound"] = _run_material_inbound(failures)
except Exception as err:
    failures.append("unexpected error: %s" % err)
    failures.append(traceback.format_exc())

result = {
    "audit": "core_document_processing_gate",
    "status": "PASS" if not failures else "FAIL",
    "flows": flows,
    "failures": failures,
}

print("CORE_DOCUMENT_PROCESSING_GATE: %s" % json.dumps(result, ensure_ascii=False, sort_keys=True))
if failures:
    print("FAILURES:")
    for failure in failures:
        print("- %s" % failure)

sys.exit(0 if not failures else 1)
