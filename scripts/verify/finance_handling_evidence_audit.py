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


def _expect_state(label, record, expected, failures):
    record.invalidate_recordset()
    return _expect(record.state == expected, "%s: expected state=%s, got %s" % (label, expected, record.state), failures)


def _expect_exception(label, func, failures):
    try:
        with env.cr.savepoint():
            func()
    except (UserError, ValidationError):
        return True
    except Exception as err:
        failures.append("%s: expected business exception, got %s: %s" % (label, type(err).__name__, err))
        return False
    failures.append("%s: expected business exception, got success" % label)
    return False


def _set_validated(record, table):
    env.flush_all()
    env.cr.execute("UPDATE %s SET validation_status=%%s WHERE id=%%s" % table, ("validated", record.id))
    record.invalidate_recordset()


def _approve_submitted(record, table):
    _set_validated(record, table)
    record.action_on_tier_approved()
    record.invalidate_recordset()
    if "validation_status" in record._fields and record.validation_status != "validated":
        _set_validated(record, table)


def _attach(record, name):
    attachment = env["ir.attachment"].sudo().create(
        {
            "name": "%s %s.txt" % (name, _token()),
            "type": "binary",
            "datas": base64.b64encode(b"phase1 finance handling evidence").decode("ascii"),
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
            "subject": "FHE Contract %s %s" % (direction, _token()),
            "type": direction,
            "project_id": project.id,
            "partner_id": partner.id,
            "company_id": env.company.id,
            "currency_id": env.company.currency_id.id,
            "tax_id": _tax("FHE Tax", "sale" if direction == "out" else "purchase").id,
        }
    )


def _purchase_order(partner, amount):
    uom = env.ref("uom.product_uom_unit", raise_if_not_found=False) or env["uom.uom"].sudo().search([], limit=1)
    product = env["product.product"].sudo().create(
        {
            "name": "FHE Service %s" % _token(),
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
    po = _purchase_order(partner, amount)
    settlement = env["sc.settlement.order"].sudo().create(
        {
            "project_id": project.id,
            "partner_id": partner.id,
            "contract_id": contract.id,
            "settlement_type": "out",
            "purchase_order_ids": [(6, 0, po.ids)],
            "company_id": env.company.id,
            "currency_id": env.company.currency_id.id,
            "line_ids": [
                (
                    0,
                    0,
                    {
                        "name": "FHE Settlement Line",
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
            "name": "FHE Payment Request %s" % _token(),
            "type": request_type,
            "project_id": project.id,
            "partner_id": partner.id,
            "contract_id": contract.id if contract else False,
            "settlement_id": settlement.id if settlement else False,
            "currency_id": env.company.currency_id.id,
            "amount": amount,
        }
    )
    env.cr.execute(
        "UPDATE payment_request SET state=%s, validation_status=%s WHERE id=%s",
        ("approved", "validated", request.id),
    )
    request.invalidate_recordset()
    return request


def _run_direct_payment_request(failures):
    project = _project("FHE Direct Payment Project", funding=True)
    partner = _partner("FHE Direct Payment Partner")
    contract = _contract(project, partner, "in")
    settlement = _settlement(project, partner, contract, 130.0)
    request = env["payment.request"].sudo().create(
        {
            "name": "FHE Direct Payment %s" % _token(),
            "type": "pay",
            "project_id": project.id,
            "partner_id": partner.id,
            "contract_id": contract.id,
            "settlement_id": settlement.id,
            "currency_id": env.company.currency_id.id,
            "amount": 130.0,
        }
    )
    _attach(request, "direct-payment")
    _expect(_attachment_count(request) >= 1, "direct_payment.attachment: expected attachment", failures)
    request.action_submit()
    _expect_state("direct_payment.submit", request, "submit", failures)
    _approve_submitted(request, "payment_request")
    _expect_state("direct_payment.approved", request, "approved", failures)
    request.action_done()
    _expect_state("direct_payment.done", request, "done", failures)
    _expect(_audit_count(request, "payment_submitted", "action_submit") >= 1, "direct_payment.audit_submit missing", failures)
    _expect(_audit_count(request, "payment_approved", "action_on_tier_approved") >= 1, "direct_payment.audit_approve missing", failures)
    _expect(_audit_count(request, "payment_paid", "action_done") >= 1, "direct_payment.audit_done missing", failures)
    ledger_count = env["payment.ledger"].sudo().search_count([("payment_request_id", "=", request.id)])
    _expect(ledger_count >= 1, "direct_payment.ledger missing", failures)
    return {"payment_request": request.id, "ledger_count": ledger_count, "attachment_count": _attachment_count(request)}


def _run_direct_receive_request(failures):
    project = _project("FHE Direct Receive Project")
    partner = _partner("FHE Direct Receive Partner")
    contract = _contract(project, partner, "out")
    request = env["payment.request"].sudo().create(
        {
            "name": "FHE Direct Receive %s" % _token(),
            "type": "receive",
            "project_id": project.id,
            "partner_id": partner.id,
            "contract_id": contract.id,
            "currency_id": env.company.currency_id.id,
            "amount": 150.0,
        }
    )
    _attach(request, "direct-receive")
    request.action_submit()
    _approve_submitted(request, "payment_request")
    request.action_done()
    _expect_state("direct_receive.done", request, "done", failures)
    _expect(_audit_count(request, "payment_paid", "action_done") >= 1, "direct_receive.audit_done missing", failures)
    ledger_count = env["sc.treasury.ledger"].sudo().search_count([("payment_request_id", "=", request.id)])
    _expect(ledger_count >= 1, "direct_receive.treasury_ledger missing", failures)
    return {"payment_request": request.id, "treasury_ledger_count": ledger_count, "attachment_count": _attachment_count(request)}


def _run_payment_execution(failures):
    project = _project("FHE Execution Project", funding=True)
    partner = _partner("FHE Execution Partner")
    contract = _contract(project, partner, "in")
    settlement = _settlement(project, partner, contract, 120.0)
    request = _approved_request(project, partner, contract, 120.0, "pay", settlement=settlement)
    execution = env["sc.payment.execution"].sudo().create(
        {
            "payment_request_id": request.id,
            "project_id": project.id,
            "partner_id": partner.id,
            "contract_id": contract.id,
            "planned_amount": 120.0,
            "paid_amount": 120.0,
            "payment_account_name": "FHE付款户名",
            "payment_account_no": "FHE-PAYER-001",
            "receipt_account_name": "FHE收款户名",
            "receipt_account_no": "FHE-PAYEE-001",
        }
    )
    _attach(execution, "payment-execution")
    execution.action_confirm()
    if execution.validation_status not in ("no", "validated"):
        _set_validated(execution, "sc_payment_execution")
    execution.action_paid()
    _expect_state("payment_execution.paid", execution, "paid", failures)
    request.invalidate_recordset()
    _expect_state("payment_execution.request_done", request, "done", failures)
    _expect(_audit_count(request, "payment_paid", "payment_execution_paid") >= 1, "payment_execution.audit_done missing", failures)
    ledger_count = env["payment.ledger"].sudo().search_count([("payment_request_id", "=", request.id)])
    _expect(ledger_count >= 1, "payment_execution.ledger missing", failures)
    return {"execution": execution.id, "payment_request": request.id, "ledger_count": ledger_count, "attachment_count": _attachment_count(execution)}


def _run_payment_cancel_and_reversal(failures):
    project = _project("FHE Cancel Reversal Project", funding=True)
    partner = _partner("FHE Cancel Reversal Partner")
    contract = _contract(project, partner, "in")
    settlement = _settlement(project, partner, contract, 170.0)

    cancellable = _approved_request(project, partner, contract, 50.0, "pay", settlement=settlement)
    cancellable.action_cancel()
    _expect_state("payment_cancel.approved_without_ledger", cancellable, "cancel", failures)
    _expect(_audit_count(cancellable, "payment_cancelled", "action_cancel") >= 1, "payment_cancel.audit_cancel missing", failures)
    cancelled_ledger_count = env["payment.ledger"].sudo().search_count([("payment_request_id", "=", cancellable.id)])
    _expect(cancelled_ledger_count == 0, "payment_cancel.cancelled request must not create payment ledger", failures)

    request = _approved_request(project, partner, contract, 120.0, "pay", settlement=settlement)
    execution = env["sc.payment.execution"].sudo().create(
        {
            "payment_request_id": request.id,
            "project_id": project.id,
            "partner_id": partner.id,
            "contract_id": contract.id,
            "planned_amount": 120.0,
            "paid_amount": 120.0,
            "payment_account_name": "FHE撤销付款户名",
            "payment_account_no": "FHE-REVERSAL-PAYER",
            "receipt_account_name": "FHE撤销收款户名",
            "receipt_account_no": "FHE-REVERSAL-PAYEE",
        }
    )
    _attach(execution, "payment-reversal")
    execution.action_confirm()
    if execution.validation_status not in ("no", "validated"):
        _set_validated(execution, "sc_payment_execution")
    execution.action_paid()
    request.invalidate_recordset()
    _expect_state("payment_reversal.request_done", request, "done", failures)
    paid_ledger_count = env["payment.ledger"].sudo().search_count([("payment_request_id", "=", request.id)])
    _expect(paid_ledger_count == 1, "payment_reversal.expected_one_ledger_before_cancel", failures)
    _expect_exception("payment_reversal.done_request_direct_cancel_blocked", request.action_cancel, failures)

    execution.action_cancel()
    execution.invalidate_recordset()
    request.invalidate_recordset()
    _expect_state("payment_reversal.execution_cancel", execution, "cancel", failures)
    _expect_state("payment_reversal.request_back_to_approved", request, "approved", failures)
    reversed_ledger_count = env["payment.ledger"].sudo().search_count([("payment_request_id", "=", request.id)])
    _expect(reversed_ledger_count == 0, "payment_reversal.ledger_removed_after_execution_cancel", failures)
    _expect(
        _audit_count(request, "payment_reversed", "payment_execution_cancel") >= 1,
        "payment_reversal.audit_reversed missing",
        failures,
    )
    return {
        "cancelled_request": cancellable.id,
        "cancelled_ledger_count": cancelled_ledger_count,
        "reversal_execution": execution.id,
        "reversal_request": request.id,
        "reversal_ledger_count": reversed_ledger_count,
    }


def _run_receipt_income(failures):
    project = _project("FHE Receipt Project")
    partner = _partner("FHE Receipt Partner")
    contract = _contract(project, partner, "out")
    request = _approved_request(project, partner, contract, 160.0, "receive")
    receipt = env["sc.receipt.income"].sudo().create(
        {
            "project_id": project.id,
            "partner_id": partner.id,
            "contract_id": contract.id,
            "payment_request_id": request.id,
            "amount": 160.0,
            "income_category": "业务收入",
            "receiving_account_name": "FHE收款账户",
            "receiving_account_no": "FHE-RECEIVE-001",
        }
    )
    _attach(receipt, "receipt-income")
    receipt.action_confirm()
    if receipt.validation_status not in ("no", "validated"):
        _set_validated(receipt, "sc_receipt_income")
    receipt.action_received()
    _expect_state("receipt_income.received", receipt, "received", failures)
    request.invalidate_recordset()
    _expect_state("receipt_income.request_done", request, "done", failures)
    _expect(_audit_count(request, "payment_paid", "receipt_income_received") >= 1, "receipt_income.audit_done missing", failures)
    ledger_count = env["sc.treasury.ledger"].sudo().search_count([("payment_request_id", "=", request.id)])
    _expect(ledger_count >= 1, "receipt_income.treasury_ledger missing", failures)
    return {"receipt": receipt.id, "payment_request": request.id, "treasury_ledger_count": ledger_count, "attachment_count": _attachment_count(receipt)}


def _run_expense_claim(failures):
    project = _project("FHE Expense Project", funding=True)
    partner = _partner("FHE Expense Partner")
    contract = _contract(project, partner, "in")
    settlement = _settlement(project, partner, contract, 90.0)
    request = _approved_request(project, partner, contract, 90.0, "pay", settlement=settlement)
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
            "payee": "FHE费用收款人",
            "receipt_account_name": "FHE费用收款账户",
            "payee_account": "FHE-CLAIM-PAYEE-001",
            "payment_account_name": "FHE费用付款账户",
            "payer_account": "FHE-CLAIM-PAYER-001",
        }
    )
    _attach(claim, "expense-claim")
    _expect_exception("expense_claim.done_before_submit", claim.action_done, failures)
    claim.action_submit()
    _approve_submitted(claim, "sc_expense_claim")
    claim.action_done()
    _expect_state("expense_claim.done", claim, "done", failures)
    request.invalidate_recordset()
    _expect_state("expense_claim.request_done", request, "done", failures)
    _expect(_audit_count(request, "payment_paid", "expense_claim_done") >= 1, "expense_claim.audit_done missing", failures)
    ledger_count = env["payment.ledger"].sudo().search_count([("payment_request_id", "=", request.id)])
    _expect(ledger_count >= 1, "expense_claim.ledger missing", failures)
    return {"claim": claim.id, "payment_request": request.id, "ledger_count": ledger_count, "attachment_count": _attachment_count(claim)}


failures = []
evidence = {}

try:
    _ensure_groups()
    evidence["direct_payment_request"] = _run_direct_payment_request(failures)
    evidence["direct_receive_request"] = _run_direct_receive_request(failures)
    evidence["payment_execution"] = _run_payment_execution(failures)
    evidence["payment_cancel_and_reversal"] = _run_payment_cancel_and_reversal(failures)
    evidence["receipt_income"] = _run_receipt_income(failures)
    evidence["expense_claim"] = _run_expense_claim(failures)
except Exception as err:
    failures.append("unexpected error: %s" % err)
    failures.append(traceback.format_exc())

result = {
    "audit": "finance_handling_evidence_audit",
    "status": "PASS" if not failures else "FAIL",
    "evidence": evidence,
    "failures": failures,
}
print("FINANCE_HANDLING_EVIDENCE_AUDIT: %s" % json.dumps(result, ensure_ascii=False, sort_keys=True))
if failures:
    print("FAILURES:")
    for failure in failures:
        print("- %s" % failure)

sys.exit(0 if not failures else 1)
