# -*- coding: utf-8 -*-
import json
import sys
import traceback

from odoo import fields


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


def _expect_close(actual, expected, label, failures, tolerance=0.01):
    return _expect(abs((actual or 0.0) - expected) <= tolerance, "%s: expected %s, got %s" % (label, expected, actual), failures)


def _expect_action(label, action, model, res_id, failures):
    _expect(action.get("res_model") == model, "%s: expected res_model=%s, got %s" % (label, model, action.get("res_model")), failures)
    _expect(action.get("res_id") == res_id, "%s: expected res_id=%s, got %s" % (label, res_id, action.get("res_id")), failures)


def _expect_category(label, record, expected_code, failures):
    record.invalidate_recordset()
    actual = record.business_category_id.code
    _expect(
        actual == expected_code,
        "%s: expected business_category=%s, got %s" % (label, expected_code, actual),
        failures,
    )


def _expect_action_domain_contains(label, action, record, failures):
    model = action.get("res_model")
    domain = action.get("domain") or []
    _expect(model == record._name, "%s: expected domain model=%s, got %s" % (label, record._name, model), failures)
    if model == record._name:
        found = env[model].sudo().search(domain)
        _expect(record.id in found.ids, "%s: action domain did not include source record %s" % (label, record.id), failures)


def _set_validated(record, table):
    if "validation_status" not in record._fields:
        return
    env.flush_all()
    env.cr.execute("UPDATE %s SET validation_status=%%s WHERE id=%%s" % table, ("validated", record.id))
    env.invalidate_all()
    record.invalidate_recordset()


def _approve_if_submitted(record, table):
    record.invalidate_recordset()
    if record.state == "draft" and "validation_status" in record._fields:
        _set_validated(record, table)
        record.action_on_tier_approved()
        record.invalidate_recordset()


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
            "subject": "ITDT Contract %s %s" % (direction, _token()),
            "type": direction,
            "project_id": project.id,
            "partner_id": partner.id,
            "company_id": env.company.id,
            "currency_id": env.company.currency_id.id,
            "tax_id": _tax("ITDT Tax", "sale" if direction == "out" else "purchase").id,
        }
    )


def _invoice_vals(project, partner, contract, direction, content, amount_no_tax, tax_amount):
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
        "document_no": "ITDT-INV-DOC-%s" % _token(),
        "document_date": today,
        "application_date": today,
        "invoice_date": today,
        "invoice_no": "ITDT-INV-%s" % _token(),
        "invoice_code": "ITDT-CODE",
        "invoice_type": "增值税专用发票",
        "tax_rate": "9%",
        "amount_no_tax": amount_no_tax,
        "tax_amount": tax_amount,
        "amount_total": amount_no_tax + tax_amount,
    }


def _tax_deduction_vals(project, partner):
    today = fields.Date.context_today(env.user)
    return {
        "project_id": project.id,
        "partner_id": partner.id,
        "currency_id": env.company.currency_id.id,
        "document_no": "ITDT-DED-%s" % _token(),
        "document_date": today,
        "invoice_no": "ITDT-DED-INV-%s" % _token(),
        "invoice_code": "ITDT-DED-CODE",
        "invoice_date": today,
        "invoice_amount_untaxed": 300.0,
        "invoice_tax_amount": 27.0,
        "invoice_amount_total": 327.0,
        "deduction_amount": 300.0,
        "deduction_tax_amount": 27.0,
        "deduction_confirm_date": today,
        "deduction_reason": "抵扣登记",
        "is_transfer_out": False,
    }


def _register_invoice(vals):
    invoice = env["sc.invoice.registration"].sudo().create(vals)
    invoice.action_confirm()
    _approve_if_submitted(invoice, "sc_invoice_registration")
    invoice.invalidate_recordset()
    invoice.action_register()
    invoice.invalidate_recordset()
    return invoice


def _deduct_tax(vals):
    deduction = env["sc.tax.deduction.registration"].sudo().create(vals)
    deduction.action_confirm()
    deduction.action_deduct()
    deduction.invalidate_recordset()
    return deduction


def _invoice_summary(invoice, failures):
    env.flush_all()
    env.invalidate_all()
    summary = env["sc.invoice.category.summary"].sudo().search(
        [
            ("project_id", "=", invoice.project_id.id),
            ("partner_id", "=", invoice.partner_id.id),
            ("source_kind", "=", invoice.source_kind),
            ("direction", "=", invoice.direction),
            ("invoice_content", "=", invoice.invoice_content),
            ("state", "=", "registered"),
            ("invoice_type", "=", invoice.invoice_type),
            ("tax_rate", "=", invoice.tax_rate),
        ],
        limit=1,
    )
    _expect(summary, "invoice_summary.%s missing" % invoice.source_kind, failures)
    if summary:
        _expect(summary.manual_invoice_count >= 1, "invoice_summary.%s manual count missing" % invoice.source_kind, failures)
        _expect_close(summary.amount_no_tax, invoice.amount_no_tax, "invoice_summary.%s amount_no_tax" % invoice.source_kind, failures)
        _expect_close(summary.tax_amount, invoice.tax_amount, "invoice_summary.%s tax_amount" % invoice.source_kind, failures)
        _expect_close(summary.amount_total, invoice.amount_total, "invoice_summary.%s amount_total" % invoice.source_kind, failures)
        _expect_action_domain_contains("invoice_summary.%s.open_invoices" % invoice.source_kind, summary.action_open_invoices(), invoice, failures)
    return summary


def _tax_fact(deduction, failures):
    env.flush_all()
    env.invalidate_all()
    fact = env["sc.finance.business.fact"].sudo().search(
        [
            ("source_model", "=", "sc.tax.deduction.registration"),
            ("source_res_id", "=", deduction.id),
            ("business_domain", "=", "tax_deduction"),
            ("fact_type", "=", "tax_deducted"),
        ],
        limit=1,
    )
    _expect(fact, "tax_deduction.fact missing", failures)
    if fact:
        _expect(fact.balance_policy == "noncash_tax", "tax_deduction.fact expected noncash_tax, got %s" % fact.balance_policy, failures)
        _expect_close(fact.amount, deduction.deduction_amount, "tax_deduction.fact amount", failures)
        _expect_close(fact.tax_amount, deduction.deduction_tax_amount, "tax_deduction.fact tax_amount", failures)
        _expect_close(fact.balance_effect, 0.0, "tax_deduction.fact balance_effect", failures)
        _expect_action("tax_deduction.fact.open_source", fact.action_open_source_record(), "sc.tax.deduction.registration", deduction.id, failures)
        _expect_action_domain_contains("tax_deduction.fact.open_business_entry", fact.action_open_business_entry(), deduction, failures)
    return fact


def _tax_project_summary(project, deduction, fact, failures):
    env.flush_all()
    env.invalidate_all()
    summary = env["sc.finance.business.project.summary"].sudo().search(
        [
            ("project_id", "=", project.id),
            ("business_domain", "=", "tax_deduction"),
        ],
        limit=1,
    )
    _expect(summary, "tax_deduction.project_summary missing", failures)
    if summary:
        _expect_close(summary.tax_deduction_amount, deduction.deduction_amount, "tax_deduction.project_summary amount", failures)
        _expect_close(summary.tax_deduction_tax_amount, deduction.deduction_tax_amount, "tax_deduction.project_summary tax_amount", failures)
        _expect_close(summary.balance_effect, 0.0, "tax_deduction.project_summary balance_effect", failures)
        action = summary.action_open_finance_facts()
        _expect(action.get("res_model") == "sc.finance.business.fact", "tax_deduction.project_summary facts model mismatch", failures)
        if fact and action.get("res_model") == "sc.finance.business.fact":
            found = env["sc.finance.business.fact"].sudo().search(action.get("domain") or [])
            _expect(fact.id in found.ids, "tax_deduction.project_summary facts domain missing fact", failures)
        _expect_action_domain_contains("tax_deduction.project_summary.business_entry", summary.action_open_business_entry(), deduction, failures)
    return summary


def _capital_position(project, fact, failures):
    env.flush_all()
    env.invalidate_all()
    position = env["sc.finance.project.capital.position"].sudo().search([("project_id", "=", project.id)], limit=1)
    _expect(position, "tax_deduction.capital_position missing", failures)
    if position:
        _expect_close(position.tax_deduction_amount, 300.0, "tax_deduction.capital_position amount", failures)
        _expect_close(position.tax_deduction_tax_amount, 27.0, "tax_deduction.capital_position tax_amount", failures)
        action = position.action_open_finance_facts()
        _expect(action.get("res_model") == "sc.finance.business.fact", "tax_deduction.capital_position facts model mismatch", failures)
        if fact and action.get("res_model") == "sc.finance.business.fact":
            found = env["sc.finance.business.fact"].sudo().search(action.get("domain") or [])
            _expect(fact.id in found.ids, "tax_deduction.capital_position facts domain missing fact", failures)
    return position


def _run(failures):
    project = _project("ITDT Project")
    output_partner = _partner("ITDT Output Partner")
    input_partner = _partner("ITDT Input Partner")
    deduction_partner = _partner("ITDT Deduction Partner")
    output_contract = _contract(project, output_partner, "out")
    input_contract = _contract(project, input_partner, "in")

    output_invoice = _register_invoice(
        _invoice_vals(project, output_partner, output_contract, "output", "销项开票登记", 100.0, 9.0)
    )
    input_invoice = _register_invoice(
        _invoice_vals(project, input_partner, input_contract, "input", "进项税额上报", 200.0, 18.0)
    )
    deduction = _deduct_tax(_tax_deduction_vals(project, deduction_partner))
    _expect_category("output_invoice.category", output_invoice, "invoice.output.registration", failures)
    _expect_category("input_invoice.category", input_invoice, "invoice.input.report", failures)
    _expect_category("tax_deduction.category", deduction, "tax.deduction.registration", failures)

    output_summary = _invoice_summary(output_invoice, failures)
    input_summary = _invoice_summary(input_invoice, failures)
    fact = _tax_fact(deduction, failures)
    project_summary = _tax_project_summary(project, deduction, fact, failures)
    position = _capital_position(project, fact, failures)

    return {
        "project": project.id,
        "output_invoice": output_invoice.id,
        "input_invoice": input_invoice.id,
        "tax_deduction": deduction.id,
        "output_summary": output_summary.id if output_summary else False,
        "input_summary": input_summary.id if input_summary else False,
        "tax_fact": fact.id if fact else False,
        "project_summary": project_summary.id if project_summary else False,
        "capital_position": position.id if position else False,
    }


failures = []
evidence = {}

try:
    _ensure_groups()
    evidence = _run(failures)
except Exception as err:
    failures.append("unexpected error: %s" % err)
    failures.append(traceback.format_exc())

result = {
    "audit": "invoice_tax_downstream_traceability_audit",
    "status": "PASS" if not failures else "FAIL",
    "evidence": evidence,
    "failures": failures,
}
print("INVOICE_TAX_DOWNSTREAM_TRACEABILITY_AUDIT: %s" % json.dumps(result, ensure_ascii=False, sort_keys=True))
if failures:
    print("FAILURES:")
    for failure in failures:
        print("- %s" % failure)

sys.exit(0 if not failures else 1)
