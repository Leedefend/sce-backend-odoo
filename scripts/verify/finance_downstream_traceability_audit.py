# -*- coding: utf-8 -*-
import base64
import json
import sys
import traceback

from odoo import fields
from odoo.exceptions import UserError, ValidationError


def _token():
    return env["ir.sequence"].sudo().next_by_code("sc.business.fact") or str(fields.Datetime.now())


def _ensure_groups():
    user = env.user.sudo()
    for xmlid in (
        "smart_construction_core.group_sc_cap_business_initiator",
        "smart_construction_core.group_sc_cap_finance_user",
        "smart_construction_core.group_sc_cap_finance_manager",
    ):
        group = env.ref(xmlid, raise_if_not_found=False)
        if group and group.id not in user.groups_id.ids:
            user.write({"groups_id": [(4, group.id)]})


def _expect(condition, label, failures):
    if not condition:
        failures.append(label)
        return False
    return True


def _expect_action(label, action, model, res_id, failures):
    _expect(action.get("res_model") == model, "%s: expected res_model=%s, got %s" % (label, model, action.get("res_model")), failures)
    _expect(action.get("res_id") == res_id, "%s: expected res_id=%s, got %s" % (label, res_id, action.get("res_id")), failures)


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


def _approve_submitted(record, table):
    _set_validated(record, table)
    record.action_on_tier_approved()
    record.invalidate_recordset()
    if "validation_status" in record._fields and record.validation_status != "validated":
        _set_validated(record, table)


def _attachment(record, name):
    attachment = env["ir.attachment"].sudo().create(
        {
            "name": "%s %s.txt" % (name, _token()),
            "type": "binary",
            "datas": base64.b64encode(b"phase1 downstream traceability").decode("ascii"),
            "res_model": record._name,
            "res_id": record.id,
            "mimetype": "text/plain",
        }
    )
    if "attachment_ids" in record._fields:
        record.sudo().write({"attachment_ids": [(4, attachment.id)]})
    record.invalidate_recordset()
    return attachment


def _attachment_count(record):
    if "attachment_ids" in record._fields:
        return len(record.attachment_ids)
    return env["ir.attachment"].sudo().search_count([("res_model", "=", record._name), ("res_id", "=", record.id)])


def _audit_count(record, event_code, action=False):
    domain = [("model", "=", record._name), ("res_id", "=", record.id), ("event_code", "=", event_code)]
    if action:
        domain.append(("action", "=", action))
    return env["sc.audit.log"].sudo().search_count(domain)


def _partner(name):
    return env["res.partner"].sudo().create({"name": "%s %s" % (name, _token())})


def _project(name, funding=False):
    project = env["project.project"].sudo().create(
        {
            "name": "%s %s" % (name, _token()),
            "manager_id": env.user.id,
            "funding_enabled": bool(funding),
            "company_id": env.company.id,
        }
    )
    if funding:
        env["project.funding.baseline"].sudo().create(
            {
                "project_id": project.id,
                "total_amount": 100000.0,
                "state": "active",
            }
        )
    return project


def _tax(name, tax_use):
    return env["account.tax"].sudo().create(
        {
            "name": "%s %s" % (name, _token()),
            "amount": 0.0,
            "amount_type": "percent",
            "type_tax_use": tax_use,
            "price_include": False,
            "company_id": env.company.id,
        }
    )


def _contract(project, partner, direction):
    return env["construction.contract"].sudo().create(
        {
            "subject": "FDT Contract %s %s" % (direction, _token()),
            "type": direction,
            "project_id": project.id,
            "partner_id": partner.id,
            "company_id": env.company.id,
            "currency_id": env.company.currency_id.id,
            "tax_id": _tax("FDT Tax", "sale" if direction == "out" else "purchase").id,
        }
    )


def _purchase_order(partner, amount):
    uom = env.ref("uom.product_uom_unit", raise_if_not_found=False) or env["uom.uom"].sudo().search([], limit=1)
    product = env["product.product"].sudo().create(
        {
            "name": "FDT Service %s" % _token(),
            "type": "service",
            "uom_id": uom.id,
            "uom_po_id": uom.id,
        }
    )
    return env["purchase.order"].sudo().create(
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


def _settlement(project, partner, contract, amount):
    settlement = env["sc.settlement.order"].sudo().create(
        {
            "project_id": project.id,
            "partner_id": partner.id,
            "contract_id": contract.id,
            "settlement_type": "out",
            "purchase_order_ids": [(6, 0, _purchase_order(partner, amount).ids)],
            "company_id": env.company.id,
            "currency_id": env.company.currency_id.id,
            "line_ids": [
                (
                    0,
                    0,
                    {
                        "name": "FDT Settlement Line",
                        "contract_id": contract.id,
                        "qty": 1.0,
                        "price_unit": amount,
                    },
                )
            ],
        }
    )
    settlement.action_submit()
    _approve_submitted(settlement, "sc_settlement_order")
    return settlement


def _approved_request(project, partner, contract, amount, request_type, settlement=False):
    request = env["payment.request"].sudo().create(
        {
            "name": "FDT Approved Request %s" % _token(),
            "type": request_type,
            "project_id": project.id,
            "partner_id": partner.id,
            "contract_id": contract.id,
            "settlement_id": settlement.id if settlement else False,
            "currency_id": env.company.currency_id.id,
            "amount": amount,
        }
    )
    env.cr.execute(
        "UPDATE payment_request SET state=%s, validation_status=%s WHERE id=%s",
        ("approved", "validated", request.id),
    )
    env.invalidate_all()
    request.invalidate_recordset()
    return request


def _verify_request_trace(label, request, failures, done_action):
    _expect(request.exists(), "%s.request missing" % label, failures)
    _expect(request.state == "done", "%s.request expected done, got %s" % (label, request.state), failures)
    _expect(_attachment_count(request) >= 1, "%s.request attachment missing" % label, failures)
    _expect(_audit_count(request, "payment_submitted", "action_submit") >= 1, "%s.submit audit missing" % label, failures)
    _expect(_audit_count(request, "payment_approved") >= 1, "%s.approve audit missing" % label, failures)
    _expect(_audit_count(request, "payment_paid", done_action) >= 1, "%s.done audit missing" % label, failures)


def _run_direct_payment_trace(failures):
    project = _project("FDT Direct Payment Project", funding=True)
    partner = _partner("FDT Direct Payment Partner")
    contract = _contract(project, partner, "in")
    settlement = _settlement(project, partner, contract, 110.0)
    request = env["payment.request"].sudo().create(
        {
            "name": "FDT Direct Payment %s" % _token(),
            "type": "pay",
            "project_id": project.id,
            "partner_id": partner.id,
            "contract_id": contract.id,
            "settlement_id": settlement.id,
            "currency_id": env.company.currency_id.id,
            "amount": 110.0,
        }
    )
    _attachment(request, "direct-payment-request")
    request.action_submit()
    _approve_submitted(request, "payment_request")
    request.action_done()
    request.invalidate_recordset()
    ledger = env["payment.ledger"].sudo().search([("payment_request_id", "=", request.id)], limit=1)
    _expect(ledger, "direct_payment.payment_ledger missing", failures)
    if ledger:
        _expect_action("direct_payment.open_request", ledger.action_open_payment_request(), "payment.request", request.id, failures)
        _expect_action("direct_payment.open_settlement", ledger.action_open_settlement(), "sc.settlement.order", settlement.id, failures)
    _verify_request_trace("direct_payment", request, failures, "action_done")
    return {"payment_request": request.id, "ledger": ledger.id if ledger else False, "settlement": settlement.id}


def _run_direct_receive_trace(failures):
    project = _project("FDT Direct Receive Project")
    partner = _partner("FDT Direct Receive Partner")
    contract = _contract(project, partner, "out")
    request = env["payment.request"].sudo().create(
        {
            "name": "FDT Direct Receive %s" % _token(),
            "type": "receive",
            "project_id": project.id,
            "partner_id": partner.id,
            "contract_id": contract.id,
            "currency_id": env.company.currency_id.id,
            "amount": 120.0,
        }
    )
    _attachment(request, "direct-receive-request")
    request.action_submit()
    _approve_submitted(request, "payment_request")
    request.action_done()
    request.invalidate_recordset()
    ledger = env["sc.treasury.ledger"].sudo().search([("payment_request_id", "=", request.id)], limit=1)
    _expect(ledger, "direct_receive.treasury_ledger missing", failures)
    if ledger:
        _expect_action("direct_receive.open_request", ledger.action_open_payment_request(), "payment.request", request.id, failures)
    _verify_request_trace("direct_receive", request, failures, "action_done")
    return {"payment_request": request.id, "treasury_ledger": ledger.id if ledger else False}


def _run_payment_execution_trace(failures):
    project = _project("FDT Execution Project", funding=True)
    partner = _partner("FDT Execution Partner")
    contract = _contract(project, partner, "in")
    settlement = _settlement(project, partner, contract, 130.0)
    request = _approved_request(project, partner, contract, 130.0, "pay", settlement=settlement)
    _attachment(request, "execution-request")
    execution = env["sc.payment.execution"].sudo().create(
        {
            "payment_request_id": request.id,
            "project_id": project.id,
            "partner_id": partner.id,
            "contract_id": contract.id,
            "planned_amount": 130.0,
            "paid_amount": 130.0,
            "payment_account_name": "FDT付款户名",
            "payment_account_no": "FDT-PAYER-001",
            "receipt_account_name": "FDT收款户名",
            "receipt_account_no": "FDT-PAYEE-001",
        }
    )
    _attachment(execution, "payment-execution")
    execution.action_confirm()
    execution.action_paid()
    request.invalidate_recordset()
    ledger = env["payment.ledger"].sudo().search([("payment_request_id", "=", request.id)], limit=1)
    source = env["sc.payment.execution"].sudo().search([("payment_request_id", "=", request.id)], limit=1)
    _expect(source.id == execution.id, "payment_execution.source reverse lookup failed", failures)
    _expect(_attachment_count(source) >= 1, "payment_execution.source attachment missing", failures)
    if ledger:
        _expect_action("payment_execution.open_request", ledger.action_open_payment_request(), "payment.request", request.id, failures)
        _expect_action("payment_execution.open_settlement", ledger.action_open_settlement(), "sc.settlement.order", settlement.id, failures)
    else:
        failures.append("payment_execution.payment_ledger missing")
    _expect(_audit_count(request, "payment_paid", "payment_execution_paid") >= 1, "payment_execution.done audit missing", failures)
    return {"execution": execution.id, "payment_request": request.id, "ledger": ledger.id if ledger else False}


def _run_receipt_income_trace(failures):
    project = _project("FDT Receipt Project")
    partner = _partner("FDT Receipt Partner")
    contract = _contract(project, partner, "out")
    request = _approved_request(project, partner, contract, 140.0, "receive")
    _attachment(request, "receipt-request")
    receipt = env["sc.receipt.income"].sudo().create(
        {
            "project_id": project.id,
            "partner_id": partner.id,
            "contract_id": contract.id,
            "payment_request_id": request.id,
            "amount": 140.0,
            "income_category": "业务收入",
            "receiving_account_name": "FDT收款账户",
            "receiving_account_no": "FDT-RECEIVE-001",
        }
    )
    _attachment(receipt, "receipt-income")
    receipt.action_confirm()
    receipt.action_received()
    request.invalidate_recordset()
    ledger = env["sc.treasury.ledger"].sudo().search([("payment_request_id", "=", request.id)], limit=1)
    source = env["sc.receipt.income"].sudo().search([("payment_request_id", "=", request.id)], limit=1)
    _expect(source.id == receipt.id, "receipt_income.source reverse lookup failed", failures)
    _expect(_attachment_count(source) >= 1, "receipt_income.source attachment missing", failures)
    if ledger:
        _expect_action("receipt_income.open_request", ledger.action_open_payment_request(), "payment.request", request.id, failures)
    else:
        failures.append("receipt_income.treasury_ledger missing")
    _expect(_audit_count(request, "payment_paid", "receipt_income_received") >= 1, "receipt_income.done audit missing", failures)
    return {"receipt": receipt.id, "payment_request": request.id, "treasury_ledger": ledger.id if ledger else False}


def _run_expense_claim_trace(failures):
    project = _project("FDT Expense Project", funding=True)
    partner = _partner("FDT Expense Partner")
    contract = _contract(project, partner, "in")
    settlement = _settlement(project, partner, contract, 90.0)
    request = _approved_request(project, partner, contract, 90.0, "pay", settlement=settlement)
    _attachment(request, "expense-request")
    claim = env["sc.expense.claim"].sudo().create(
        {
            "claim_type": "expense",
            "expense_type": "项目费用报销单",
            "summary": "项目费用报销单",
            "project_id": project.id,
            "partner_id": partner.id,
            "payment_request_id": request.id,
            "amount": 90.0,
            "approved_amount": 90.0,
            "payee": "FDT费用收款人",
            "receipt_account_name": "FDT费用收款账户",
            "payee_account": "FDT-CLAIM-PAYEE-001",
            "payment_account_name": "FDT费用付款账户",
            "payer_account": "FDT-CLAIM-PAYER-001",
        }
    )
    _attachment(claim, "expense-claim")
    claim.action_submit()
    _approve_submitted(claim, "sc_expense_claim")
    claim.action_done()
    request.invalidate_recordset()
    ledger = env["payment.ledger"].sudo().search([("payment_request_id", "=", request.id)], limit=1)
    source = env["sc.expense.claim"].sudo().search([("payment_request_id", "=", request.id)], limit=1)
    _expect(source.id == claim.id, "expense_claim.source reverse lookup failed", failures)
    _expect(_attachment_count(source) >= 1, "expense_claim.source attachment missing", failures)
    if ledger:
        _expect_action("expense_claim.open_request", ledger.action_open_payment_request(), "payment.request", request.id, failures)
        _expect_action("expense_claim.open_settlement", ledger.action_open_settlement(), "sc.settlement.order", settlement.id, failures)
    else:
        failures.append("expense_claim.payment_ledger missing")
    _expect(_audit_count(request, "payment_paid", "expense_claim_done") >= 1, "expense_claim.done audit missing", failures)
    return {"claim": claim.id, "payment_request": request.id, "ledger": ledger.id if ledger else False}


failures = []
evidence = {}

try:
    _ensure_groups()
    evidence["direct_payment"] = _run_direct_payment_trace(failures)
    evidence["direct_receive"] = _run_direct_receive_trace(failures)
    evidence["payment_execution"] = _run_payment_execution_trace(failures)
    evidence["receipt_income"] = _run_receipt_income_trace(failures)
    evidence["expense_claim"] = _run_expense_claim_trace(failures)
except Exception as err:
    failures.append("unexpected error: %s" % err)
    failures.append(traceback.format_exc())

result = {
    "audit": "finance_downstream_traceability_audit",
    "status": "PASS" if not failures else "FAIL",
    "evidence": evidence,
    "failures": failures,
}
print("FINANCE_DOWNSTREAM_TRACEABILITY_AUDIT: %s" % json.dumps(result, ensure_ascii=False, sort_keys=True))
if failures:
    print("FAILURES:")
    for failure in failures:
        print("- %s" % failure)

sys.exit(0 if not failures else 1)
