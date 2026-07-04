# -*- coding: utf-8 -*-
import base64
import json
import sys
import traceback

from odoo import fields
from odoo.exceptions import UserError, ValidationError


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


def _token():
    return env["ir.sequence"].sudo().next_by_code("sc.business.fact") or str(fields.Datetime.now())


def _expect_state(label, record, expected, failures):
    record.invalidate_recordset()
    if record.state != expected:
        failures.append("%s: expected state=%s, got %s" % (label, expected, record.state))
        return False
    return True


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


def _approve_if_needed(record, table_name):
    record.invalidate_recordset()
    if record.state != "draft":
        return
    if "validation_status" in record._fields:
        env.cr.execute(
            "UPDATE %s SET validation_status=%%s WHERE id=%%s" % table_name,
            ("validated", record.id),
        )
        record.invalidate_recordset()
    if hasattr(record, "action_on_tier_approved"):
        record.action_on_tier_approved()


def _partner(name):
    return env["res.partner"].create({"name": "%s %s" % (name, _token())})


def _project(name, funding=False):
    project = env["project.project"].create(
        {
            "name": "%s %s" % (name, _token()),
            "manager_id": env.user.id,
            "funding_enabled": bool(funding),
            "company_id": env.company.id,
        }
    )
    if funding:
        env["project.funding.baseline"].create(
            {
                "project_id": project.id,
                "total_amount": 100000.0,
                "state": "active",
            }
        )
    return project


def _department():
    return env["hr.department"].create({"name": "BAC Audit Dept %s" % _token()})


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
    return env["construction.contract"].create(
        {
            "subject": "BAC Audit Contract %s %s" % (direction, _token()),
            "type": direction,
            "project_id": project.id,
            "partner_id": partner.id,
            "company_id": env.company.id,
            "currency_id": env.company.currency_id.id,
            "tax_id": _tax("BAC Audit Tax", "sale" if direction == "out" else "purchase").id,
        }
    )


def _purchase_order(partner, amount):
    uom = env.ref("uom.product_uom_unit", raise_if_not_found=False) or env["uom.uom"].sudo().search([], limit=1)
    product = env["product.product"].sudo().create(
        {
            "name": "BAC Audit Service %s" % _token(),
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


def _settlement(project, partner, contract, amount):
    po = _purchase_order(partner, amount)
    settlement = env["sc.settlement.order"].create(
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
                        "name": "BAC Audit Settlement Line",
                        "contract_id": contract.id,
                        "qty": 1.0,
                        "price_unit": amount,
                    },
                )
            ],
        }
    )
    settlement.action_submit()
    settlement.invalidate_recordset()
    if settlement.state == "submit":
        env.flush_all()
        env.cr.execute(
            "UPDATE sc_settlement_order SET validation_status=%s WHERE id=%s",
            ("validated", settlement.id),
        )
        settlement.invalidate_recordset()
        if settlement.validation_status != "validated":
            settlement.write({"validation_status": "validated"})
            settlement.invalidate_recordset()
        settlement.action_on_tier_approved()
    settlement.invalidate_recordset()
    return settlement


def _payment_request(project, partner, contract, amount, request_type, settlement=False):
    request = env["payment.request"].sudo().create(
        {
            "name": "BAC Audit Payment Request %s" % _token(),
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


def _run_payment_execution(failures):
    project = _project("BAC Payment Execution Project", funding=True)
    partner = _partner("BAC Payment Execution Partner")
    contract = _contract(project, partner, "in")
    settlement = _settlement(project, partner, contract, 120.0)
    request = _payment_request(project, partner, contract, 120.0, "pay", settlement=settlement)
    execution = env["sc.payment.execution"].sudo().create(
        {
            "payment_request_id": request.id,
            "project_id": project.id,
            "partner_id": partner.id,
            "contract_id": contract.id,
            "planned_amount": 120.0,
            "paid_amount": 120.0,
            "payment_account_name": "BAC付款户名",
            "payment_account_no": "BAC-PAYER-001",
            "receipt_account_name": "BAC收款户名",
            "receipt_account_no": "BAC-PAYEE-001",
        }
    )
    execution.action_confirm()
    _approve_if_needed(execution, "sc_payment_execution")
    _expect_state("payment_execution.confirm", execution, "confirmed", failures)
    _expect_exception("payment_execution.confirm_again", execution.action_confirm, failures)
    execution.action_paid()
    _expect_state("payment_execution.paid", execution, "paid", failures)
    request.invalidate_recordset()
    if request.state != "done":
        failures.append("payment_execution.request_done: expected done, got %s" % request.state)
    ledger_count = env["payment.ledger"].search_count([("payment_request_id", "=", request.id)])
    if ledger_count < 1:
        failures.append("payment_execution.ledger: expected payment ledger")
    return {"execution": execution.id, "payment_request": request.id, "settlement": settlement.id}


def _run_receipt_income(failures):
    project = _project("BAC Receipt Income Project")
    partner = _partner("BAC Receipt Income Partner")
    contract = _contract(project, partner, "out")
    request = _payment_request(project, partner, contract, 160.0, "receive")
    receipt = env["sc.receipt.income"].sudo().create(
        {
            "project_id": project.id,
            "partner_id": partner.id,
            "contract_id": contract.id,
            "payment_request_id": request.id,
            "amount": 160.0,
            "income_category": "业务收入",
            "receiving_account_name": "BAC收款账户",
            "receiving_account_no": "BAC-RECEIVE-001",
        }
    )
    _expect_exception(
        "receipt_income.received_bad_partner",
        lambda: (receipt.write({"partner_id": False}), receipt.action_received()),
        failures,
    )
    receipt.write({"partner_id": partner.id})
    receipt.action_confirm()
    _approve_if_needed(receipt, "sc_receipt_income")
    _expect_state("receipt_income.confirm", receipt, "confirmed", failures)
    receipt.action_received()
    _expect_state("receipt_income.received", receipt, "received", failures)
    request.invalidate_recordset()
    if request.state != "done":
        failures.append("receipt_income.request_done: expected done, got %s" % request.state)
    return {"receipt": receipt.id, "payment_request": request.id}


def _run_expense_claim(failures):
    project = _project("BAC Expense Claim Project", funding=True)
    partner = _partner("BAC Expense Claim Partner")
    contract = _contract(project, partner, "in")
    settlement = _settlement(project, partner, contract, 80.0)
    request = _payment_request(project, partner, contract, 80.0, "pay", settlement=settlement)
    claim = env["sc.expense.claim"].sudo().create(
        {
            "claim_type": "expense",
            "expense_type": "公司财务支出",
            "project_id": project.id,
            "partner_id": partner.id,
            "payment_request_id": request.id,
            "amount": 80.0,
            "approved_amount": 80.0,
            "payee": "BAC费用收款人",
            "receipt_account_name": "BAC费用收款账户",
            "payee_account": "BAC-CLAIM-PAYEE-001",
            "payment_account_name": "BAC费用付款账户",
            "payer_account": "BAC-CLAIM-PAYER-001",
        }
    )
    _attach_proof(claim, "business-action-coverage-expense-claim")
    _expect_exception("expense_claim.done_before_submit", claim.action_done, failures)
    claim.action_submit()
    if claim.state == "submit":
        env.flush_all()
        env.cr.execute(
            "UPDATE sc_expense_claim SET validation_status=%s WHERE id=%s",
            ("validated", claim.id),
        )
        claim.invalidate_recordset()
        if claim.validation_status != "validated":
            claim.write({"validation_status": "validated"})
            claim.invalidate_recordset()
        claim.action_on_tier_approved()
    _expect_state("expense_claim.approved", claim, "approved", failures)
    claim.action_done()
    _expect_state("expense_claim.done", claim, "done", failures)
    request.invalidate_recordset()
    if request.state != "done":
        failures.append("expense_claim.request_done: expected done, got %s" % request.state)
    return {"claim": claim.id, "payment_request": request.id, "settlement": settlement.id}


def _run_invoice_registration(failures):
    project = _project("BAC Invoice Project")
    partner = _partner("BAC Invoice Partner")
    contract = _contract(project, partner, "in")
    invoice = env["sc.invoice.registration"].create(
        {
            "project_id": project.id,
            "partner_id": partner.id,
            "contract_id": contract.id,
            "direction": "input",
            "source_kind": "invoice_registration",
            "invoice_no": "BAC-INV-%s" % _token(),
            "invoice_date": fields.Date.today(),
            "amount_total": 109.0,
            "tax_amount": 9.0,
        }
    )
    _expect_exception("invoice.register_before_confirm", invoice.action_register, failures)
    invoice.action_confirm()
    _approve_if_needed(invoice, "sc_invoice_registration")
    _expect_state("invoice.confirm", invoice, "confirmed", failures)
    invoice.action_register()
    _expect_state("invoice.register", invoice, "registered", failures)
    return {"invoice": invoice.id}


def _run_tax_deduction(failures):
    project = _project("BAC Tax Deduction Project")
    partner = _partner("BAC Tax Deduction Partner")
    deduction = env["sc.tax.deduction.registration"].create(
        {
            "project_id": project.id,
            "partner_id": partner.id,
            "invoice_no": "BAC-TAX-%s" % _token(),
            "invoice_amount_untaxed": 100.0,
            "invoice_tax_amount": 9.0,
            "invoice_amount_total": 109.0,
        }
    )
    deduction.action_confirm()
    _expect_state("tax_deduction.confirm", deduction, "confirmed", failures)
    deduction.action_deduct()
    _expect_state("tax_deduction.deduct", deduction, "deducted", failures)
    if not deduction.deduction_confirm_date:
        failures.append("tax_deduction.confirm_date: expected value")
    return {"deduction": deduction.id}


def _run_hr_payroll(failures):
    department = _department()
    payroll = env["sc.hr.payroll.document"].create(
        {
            "name": "BAC Payroll %s" % _token(),
            "fact_type": "salary_registration",
            "employee_name": "BAC Payroll Employee",
            "department_id": department.id,
            "period_year": 2026,
            "period_month": 6,
            "gross_amount": 9000.0,
            "net_salary": 8000.0,
        }
    )
    bad_payroll = env["sc.hr.payroll.document"].create(
        {
            "name": "BAC Payroll Bad %s" % _token(),
            "fact_type": "salary_registration",
            "employee_name": "BAC Payroll Bad",
            "department_id": department.id,
            "period_year": 2026,
            "period_month": 13,
            "gross_amount": 1.0,
            "net_salary": 1.0,
        }
    )
    _expect_exception("hr_payroll.invalid_month", bad_payroll.action_submit, failures)
    payroll.action_submit()
    _expect_state("hr_payroll.submit", payroll, "in_progress", failures)
    payroll.action_done()
    _expect_state("hr_payroll.done", payroll, "done", failures)
    return {"payroll": payroll.id}


def _run_fund_account_operation(failures):
    project = _project("BAC Fund Operation Project")
    Account = env["sc.fund.account"]
    source = Account.create(
        {
            "name": "BAC Source Account %s" % _token(),
            "account_no": "SRC-%s" % _token(),
            "project_id": project.id,
            "state": "active",
        }
    )
    target = Account.create(
        {
            "name": "BAC Target Account %s" % _token(),
            "account_no": "TGT-%s" % _token(),
            "project_id": project.id,
            "state": "active",
        }
    )
    operation = env["sc.fund.account.operation"].create(
        {
            "operation_type": "transfer_between",
            "project_id": project.id,
            "source_account_id": source.id,
            "target_account_id": target.id,
            "amount": 200.0,
            "operation_reason": "业务动作覆盖审计",
        }
    )
    _expect_exception("fund_operation.done_before_confirm", operation.action_done, failures)
    operation.action_confirm()
    _expect_state("fund_operation.confirm", operation, "confirmed", failures)
    operation.action_done()
    _expect_state("fund_operation.done", operation, "done", failures)
    return {"operation": operation.id, "source_account": source.id, "target_account": target.id}


failures = []
coverage = {}

try:
    _ensure_groups(env)
    coverage["payment_execution"] = _run_payment_execution(failures)
    coverage["receipt_income"] = _run_receipt_income(failures)
    coverage["expense_claim"] = _run_expense_claim(failures)
    coverage["invoice_registration"] = _run_invoice_registration(failures)
    coverage["tax_deduction"] = _run_tax_deduction(failures)
    coverage["hr_payroll"] = _run_hr_payroll(failures)
    coverage["fund_account_operation"] = _run_fund_account_operation(failures)
except Exception as err:
    failures.append("unexpected error: %s" % err)
    failures.append(traceback.format_exc())

result = {
    "audit": "business_action_coverage_audit",
    "status": "PASS" if not failures else "FAIL",
    "coverage": coverage,
    "failures": failures,
}
print("BUSINESS_ACTION_COVERAGE_AUDIT: %s" % json.dumps(result, ensure_ascii=False, sort_keys=True))
if failures:
    print("FAILURES:")
    for failure in failures:
        print("- %s" % failure)

sys.exit(0 if not failures else 1)
