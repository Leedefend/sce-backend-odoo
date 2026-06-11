# -*- coding: utf-8 -*-
import base64
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


def _set_validated(record):
    env.flush_all()  # noqa: F821
    env.cr.execute(  # noqa: F821
        "UPDATE %s SET validation_status=%%s WHERE id=%%s" % record._table,
        ("validated", record.id),
    )
    env.invalidate_all()  # noqa: F821
    record.invalidate_recordset()
    if record.validation_status != "validated":
        record.sudo().with_context(skip_validation_check=True).write({"validation_status": "validated"})
        env.flush_all()  # noqa: F821
        env.invalidate_all()  # noqa: F821
        record.invalidate_recordset()


def _ensure_groups():
    user = env.user.sudo()  # noqa: F821
    for xmlid in (
        "smart_construction_core.group_sc_cap_business_initiator",
        "smart_construction_core.group_sc_cap_finance_user",
        "smart_construction_core.group_sc_cap_finance_manager",
    ):
        group = env.ref(xmlid, raise_if_not_found=False)  # noqa: F821
        if group and group.id not in user.groups_id.ids:
            user.write({"groups_id": [(4, group.id)]})
    env.invalidate_all()  # noqa: F821


def _tax(company):
    Tax = env["account.tax"].sudo()  # noqa: F821
    tax = Tax.search(
        [
            ("company_id", "=", company.id),
            ("type_tax_use", "in", ["sale", "all"]),
            ("amount_type", "=", "percent"),
            ("price_include", "=", False),
        ],
        limit=1,
    )
    if tax:
        return tax
    return Tax.create(
        {
            "name": "ICRI Sale Tax %s" % _token(),
            "amount_type": "percent",
            "amount": 0.0,
            "type_tax_use": "sale",
            "price_include": False,
            "company_id": company.id,
        }
    )


def _attachment(record):
    env["ir.attachment"].sudo().create(  # noqa: F821
        {
            "name": "income-contract-receipt-invoice-closure.txt",
            "datas": base64.b64encode(b"income contract receipt invoice closure"),
            "res_model": record._name,
            "res_id": record.id,
            "type": "binary",
            "mimetype": "text/plain",
        }
    )


def _audit_events(model, res_id):
    return sorted(
        {
            code
            for code in env["sc.audit.log"].sudo().search(  # noqa: F821
                [("model", "=", model), ("res_id", "=", res_id)],
                order="id asc",
            ).mapped("event_code")
            if code
        }
    )


failures = []
evidence = {}

try:
    _ensure_groups()
    company = env.company  # noqa: F821
    token = _token()
    amount = 800.0
    invoice_tax = 72.0
    invoice_total = amount + invoice_tax

    partner = env["res.partner"].sudo().create({"name": "ICRI Customer %s" % token})  # noqa: F821
    project = env["project.project"].sudo().create(  # noqa: F821
        {
            "name": "ICRI Project %s" % token,
            "code": "ICRI-%s" % token,
            "funding_enabled": True,
            "company_id": company.id,
            "manager_id": env.user.id,  # noqa: F821
        }
    )
    env["project.funding.baseline"].sudo().create(  # noqa: F821
        {"project_id": project.id, "total_amount": 5000.0, "state": "active"}
    )
    contract = env["construction.contract"].sudo().create(  # noqa: F821
        {
            "subject": "ICRI Income Contract %s" % token,
            "type": "out",
            "project_id": project.id,
            "partner_id": partner.id,
            "company_id": company.id,
            "currency_id": company.currency_id.id,
            "tax_id": _tax(company).id,
        }
    )

    request = env["payment.request"].sudo().create(  # noqa: F821
        {
            "project_id": project.id,
            "partner_id": partner.id,
            "contract_id": contract.id,
            "currency_id": company.currency_id.id,
            "amount": amount,
            "type": "receive",
            "receipt_type": "工程进度款收款申请",
        }
    )
    _attachment(request)
    request.action_submit()
    request.invalidate_recordset()
    _expect(request.state == "submit", "receipt_request.state_after_submit: expected submit", failures)
    _set_validated(request)
    request.action_on_tier_approved()
    request.invalidate_recordset()
    _expect(request.state == "approved", "receipt_request.state_after_approval: expected approved", failures)

    receipt = env["sc.receipt.income"].sudo().create(  # noqa: F821
        {
            "source_kind": "receipt_income",
            "project_id": project.id,
            "partner_id": partner.id,
            "contract_id": contract.id,
            "payment_request_id": request.id,
            "currency_id": company.currency_id.id,
            "date_receipt": fields.Date.context_today(env.user),  # noqa: F821
            "receipt_type": "工程进度款收入",
            "income_category": "工程进度款收入",
            "receiving_account_name": "ICRI 收款账户",
            "receiving_account_no": "ICRI-RECEIPT-ACCOUNT",
            "amount": amount,
        }
    )
    _attachment(receipt)
    receipt.action_confirm()
    receipt.invalidate_recordset()
    if receipt.state == "draft":
        _set_validated(receipt)
        receipt.action_on_tier_approved()
        receipt.invalidate_recordset()
    _expect(receipt.state == "confirmed", "receipt.state_after_confirm: expected confirmed", failures)
    receipt.action_received()
    receipt.invalidate_recordset()
    request.invalidate_recordset()
    _expect(receipt.state == "received", "receipt.state_after_received: expected received", failures)
    _expect(request.state == "done", "receipt_request.state_after_receipt: expected done", failures)
    ledger = env["sc.treasury.ledger"].sudo().search([("payment_request_id", "=", request.id)], limit=1)  # noqa: F821
    _expect(bool(ledger), "treasury_ledger: expected ledger", failures)
    if ledger:
        _expect(ledger.direction == "in", "treasury_ledger.direction: expected in", failures)
        _expect(ledger.amount == amount, "treasury_ledger.amount: expected receipt amount", failures)
        _expect(receipt.treasury_ledger_id == ledger, "receipt.treasury_ledger_id: expected linked ledger", failures)

    invoice = env["sc.invoice.registration"].sudo().create(  # noqa: F821
        {
            "source_kind": "output_invoice_tax",
            "direction": "output",
            "invoice_content": "工程进度款销项开票",
            "project_id": project.id,
            "partner_id": partner.id,
            "contract_id": contract.id,
            "currency_id": company.currency_id.id,
            "document_no": "ICRI-INV-DOC-%s" % token,
            "document_date": fields.Date.context_today(env.user),  # noqa: F821
            "application_date": fields.Date.context_today(env.user),  # noqa: F821
            "invoice_date": fields.Date.context_today(env.user),  # noqa: F821
            "invoice_no": "ICRI-INV-%s" % token,
            "invoice_code": "ICRI-CODE",
            "invoice_type": "增值税专用发票",
            "tax_rate": "9%",
            "amount_no_tax": amount,
            "tax_amount": invoice_tax,
            "amount_total": invoice_total,
        }
    )
    _attachment(invoice)
    invoice.action_confirm()
    invoice.invalidate_recordset()
    if invoice.state == "draft":
        _set_validated(invoice)
        invoice.action_on_tier_approved()
        invoice.invalidate_recordset()
    _expect(invoice.state == "confirmed", "invoice.state_after_confirm: expected confirmed", failures)
    invoice.action_register()
    invoice.invalidate_recordset()
    _expect(invoice.state == "registered", "invoice.state_after_register: expected registered", failures)

    contract.invalidate_recordset()
    _expect(contract.received_amount == amount, "contract.received_amount: expected receipt amount", failures)
    _expect(contract.invoice_amount == invoice_total, "contract.invoice_amount: expected invoice total", failures)

    request_events = _audit_events("payment.request", request.id)
    receipt_events = _audit_events("sc.receipt.income", receipt.id)
    invoice_events = _audit_events("sc.invoice.registration", invoice.id)
    _expect("payment_submitted" in request_events, "receipt_request.audit: missing payment_submitted", failures)
    _expect("payment_approved" in request_events, "receipt_request.audit: missing payment_approved", failures)
    _expect("payment_paid" in request_events, "receipt_request.audit: missing payment_paid", failures)
    _expect("receipt_income_confirmed" in receipt_events, "receipt.audit: missing receipt_income_confirmed", failures)
    _expect("receipt_income_received" in receipt_events, "receipt.audit: missing receipt_income_received", failures)
    _expect("invoice_registered" in invoice_events, "invoice.audit: missing invoice_registered", failures)

    evidence = {
        "contract_id": contract.id,
        "receipt_request_id": request.id,
        "receipt_income_id": receipt.id,
        "treasury_ledger_id": ledger.id if ledger else False,
        "invoice_id": invoice.id,
        "receipt_amount": amount,
        "invoice_total": invoice_total,
        "contract_received_amount": contract.received_amount,
        "contract_invoice_amount": contract.invoice_amount,
        "request_events": request_events,
        "receipt_events": receipt_events,
        "invoice_events": invoice_events,
    }
except Exception as err:
    failures.append("unexpected error: %s" % err)
    failures.append(traceback.format_exc())

result = {
    "audit": "income_contract_receipt_invoice_closure_audit",
    "status": "PASS" if not failures else "FAIL",
    "evidence": evidence,
    "failures": failures,
}
print("INCOME_CONTRACT_RECEIPT_INVOICE_CLOSURE_AUDIT: %s" % json.dumps(result, ensure_ascii=False, sort_keys=True))
if failures:
    print("FAILURES:")
    for failure in failures:
        print("- %s" % failure)

sys.exit(0 if not failures else 1)
