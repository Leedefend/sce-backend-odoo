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


def _expect_category(label, record, expected_code, failures):
    record.invalidate_recordset()
    actual = record.business_category_id.code
    return _expect(
        actual == expected_code,
        "%s: expected business_category=%s, got %s" % (label, expected_code, actual),
        failures,
    )


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


def _audit_count(record, event_code, action=False):
    domain = [("model", "=", record._name), ("res_id", "=", record.id), ("event_code", "=", event_code)]
    if action:
        domain.append(("action", "=", action))
    return env["sc.audit.log"].sudo().search_count(domain)


def _attach(record, name):
    attachment = env["ir.attachment"].sudo().create(
        {
            "name": "%s %s.txt" % (name, _token()),
            "type": "binary",
            "datas": base64.b64encode(b"invoice tax handling evidence").decode("ascii"),
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


def _partner(name):
    return env["res.partner"].sudo().create({"name": "%s %s" % (name, _token())})


def _project(name):
    return env["project.project"].sudo().create(
        {
            "name": "%s %s" % (name, _token()),
            "manager_id": env.user.id,
            "company_id": env.company.id,
        }
    )


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
            "subject": "ITHE Contract %s %s" % (direction, _token()),
            "type": direction,
            "project_id": project.id,
            "partner_id": partner.id,
            "company_id": env.company.id,
            "currency_id": env.company.currency_id.id,
            "tax_id": _tax("ITHE Tax", "sale" if direction == "out" else "purchase").id,
        }
    )


def _invoice_vals(project, partner, contract, direction, content, amount=109.0):
    today = fields.Date.context_today(env.user)
    source_kind = "output_invoice_tax" if direction == "output" else "input_invoice_tax"
    return {
        "source_kind": source_kind,
        "direction": direction,
        "invoice_content": content,
        "project_id": project.id,
        "partner_id": partner.id,
        "contract_id": contract.id,
        "currency_id": env.company.currency_id.id,
        "document_no": "ITHE-INV-DOC-%s" % _token(),
        "document_date": today,
        "application_date": today,
        "invoice_date": today,
        "invoice_no": "ITHE-INV-%s" % _token(),
        "invoice_code": "ITHE-CODE",
        "invoice_type": "增值税专用发票",
        "amount_no_tax": amount - 9.0,
        "tax_amount": 9.0,
        "amount_total": amount,
    }


def _prepaid_invoice_vals(project, partner, contract):
    vals = _invoice_vals(project, partner, contract, "prepaid", "预缴税款")
    vals.update(
        {
            "source_kind": "prepaid_tax",
            "direction": "prepaid",
            "invoice_no": False,
            "tax_certificate_no": "ITHE-TAXCERT-%s" % _token(),
        }
    )
    return vals


def _tax_deduction_vals(project, partner):
    today = fields.Date.context_today(env.user)
    return {
        "project_id": project.id,
        "partner_id": partner.id,
        "currency_id": env.company.currency_id.id,
        "document_no": "ITHE-DED-%s" % _token(),
        "document_date": today,
        "invoice_no": "ITHE-DED-INV-%s" % _token(),
        "invoice_code": "ITHE-DED-CODE",
        "invoice_date": today,
        "invoice_amount_untaxed": 100.0,
        "invoice_tax_amount": 9.0,
        "invoice_amount_total": 109.0,
        "deduction_amount": 100.0,
        "deduction_tax_amount": 9.0,
        "deduction_confirm_date": today,
        "deduction_reason": "抵扣登记",
        "is_transfer_out": False,
    }


def _run_invoice_registration(failures):
    project = _project("ITHE Invoice Project")
    partner = _partner("ITHE Invoice Partner")
    contract = _contract(project, partner, "out")
    invoice = env["sc.invoice.registration"].sudo().create(
        _invoice_vals(project, partner, contract, "output", "销项开票登记")
    )
    _expect_category("invoice_registration.category", invoice, "invoice.output.registration", failures)
    _attach(invoice, "invoice-registration")
    _expect(_attachment_count(invoice) >= 1, "invoice_registration.attachment: expected attachment", failures)
    invoice.action_confirm()
    _expect_state("invoice_registration.confirm", invoice, "confirmed", failures)
    invoice.action_register()
    _expect_state("invoice_registration.register", invoice, "registered", failures)
    _expect(
        _audit_count(invoice, "invoice_confirmed", "action_confirm") >= 1,
        "invoice_registration.audit_confirm missing",
        failures,
    )
    _expect(
        _audit_count(invoice, "invoice_registered", "action_register") >= 1,
        "invoice_registration.audit_register missing",
        failures,
    )

    missing_no = env["sc.invoice.registration"].sudo().create(
        dict(_invoice_vals(project, partner, contract, "output", "销项开票登记"), invoice_no=False)
    )
    _expect_exception("invoice_registration.missing_invoice_no", missing_no.action_confirm, failures)

    other_partner = _partner("ITHE Other Invoice Partner")
    mismatch = env["sc.invoice.registration"].sudo().create(
        dict(_invoice_vals(project, other_partner, contract, "output", "销项开票登记"), partner_id=other_partner.id)
    )
    _expect_exception("invoice_registration.contract_partner_mismatch", mismatch.action_confirm, failures)

    prepaid = env["sc.invoice.registration"].sudo().create(_prepaid_invoice_vals(project, partner, contract))
    _expect_category("invoice_registration.prepaid_category", prepaid, "invoice.prepaid_tax", failures)
    prepaid.action_confirm()
    prepaid.action_register()
    _expect_state("invoice_registration.prepaid_register", prepaid, "registered", failures)

    cancellable = env["sc.invoice.registration"].sudo().create(
        _invoice_vals(project, partner, contract, "output", "销项开票申请")
    )
    cancellable.action_cancel()
    _expect_state("invoice_registration.cancel", cancellable, "cancel", failures)
    _expect(
        _audit_count(cancellable, "invoice_cancelled", "action_cancel") >= 1,
        "invoice_registration.audit_cancel missing",
        failures,
    )


def _run_tax_deduction(failures):
    project = _project("ITHE Tax Deduction Project")
    partner = _partner("ITHE Tax Deduction Partner")
    deduction = env["sc.tax.deduction.registration"].sudo().create(_tax_deduction_vals(project, partner))
    _expect_category("tax_deduction.category", deduction, "tax.deduction.registration", failures)
    _attach(deduction, "tax-deduction")
    _expect(_attachment_count(deduction) >= 1, "tax_deduction.attachment: expected attachment", failures)
    deduction.action_confirm()
    _expect_state("tax_deduction.confirm", deduction, "confirmed", failures)
    deduction.action_deduct()
    _expect_state("tax_deduction.deduct", deduction, "deducted", failures)
    _expect(
        _audit_count(deduction, "tax_deduction_confirmed", "action_confirm") >= 1,
        "tax_deduction.audit_confirm missing",
        failures,
    )
    _expect(
        _audit_count(deduction, "tax_deduction_deducted", "action_deduct") >= 1,
        "tax_deduction.audit_deduct missing",
        failures,
    )

    missing_invoice = env["sc.tax.deduction.registration"].sudo().create(
        dict(_tax_deduction_vals(project, partner), invoice_no=False)
    )
    _expect_exception("tax_deduction.missing_invoice_no", missing_invoice.action_deduct, failures)

    excessive_tax = env["sc.tax.deduction.registration"].sudo().create(
        dict(_tax_deduction_vals(project, partner), deduction_tax_amount=99.0)
    )
    _expect_exception("tax_deduction.excessive_tax", excessive_tax.action_deduct, failures)

    cancellable = env["sc.tax.deduction.registration"].sudo().create(_tax_deduction_vals(project, partner))
    cancellable.action_cancel()
    _expect_state("tax_deduction.cancel", cancellable, "cancel", failures)
    _expect(
        _audit_count(cancellable, "tax_deduction_cancelled", "action_cancel") >= 1,
        "tax_deduction.audit_cancel missing",
        failures,
    )


failures = []

try:
    _ensure_groups()
    with env.cr.savepoint():
        _run_invoice_registration(failures)
    with env.cr.savepoint():
        _run_tax_deduction(failures)
except Exception as err:
    failures.append("unexpected error: %s" % err)
    failures.append(traceback.format_exc())

result = {
    "audit": "invoice_tax_handling_evidence_audit",
    "status": "PASS" if not failures else "FAIL",
    "covered": ["invoice_registration", "tax_deduction_registration"],
    "evidence": [
        "attachment",
        "state closure",
        "business anchor blocking",
        "audit event",
    ],
    "failures": failures,
}
print("INVOICE_TAX_HANDLING_EVIDENCE_AUDIT: %s" % json.dumps(result, ensure_ascii=False, sort_keys=True))
if failures:
    print("FAILURES:")
    for failure in failures:
        print("- %s" % failure)

sys.exit(0 if not failures else 1)
