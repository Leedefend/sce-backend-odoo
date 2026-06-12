# -*- coding: utf-8 -*-
import json
import sys
import traceback

from odoo import fields
from odoo.tools.safe_eval import safe_eval


CATEGORIES = [
    ("invoice.output.application", "smart_construction_core.action_sc_invoice_application_user"),
    ("invoice.output.registration", "smart_construction_core.action_sc_invoice_registration_user"),
    ("invoice.prepaid_tax", "smart_construction_core.action_sc_invoice_prepaid_tax_user"),
    ("invoice.input.report", "smart_construction_core.action_sc_invoice_input_report_user"),
    ("tax.deduction.registration", "smart_construction_core.action_sc_tax_deduction_registration_user"),
]


def _token():
    return env["ir.sequence"].sudo().next_by_code("sc.business.fact") or str(fields.Datetime.now())


def _parse(value, default):
    if not value:
        return default
    if isinstance(value, (dict, list, tuple)):
        return value
    return safe_eval(value)


def _context_defaults(context):
    return {
        key[len("default_") :]: value
        for key, value in (context or {}).items()
        if isinstance(key, str) and key.startswith("default_")
        and key not in {"default_business_category_code"}
    }


def _project():
    return env["project.project"].sudo().create(
        {
            "name": "ITBCR Project %s" % _token(),
            "manager_id": env.user.id,
            "company_id": env.company.id,
        }
    )


def _partner():
    return env["res.partner"].sudo().create({"name": "ITBCR Partner %s" % _token()})


def _tax(tax_use):
    return env["account.tax"].sudo().create(
        {
            "name": "ITBCR Tax %s %s" % (tax_use, _token()),
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
            "subject": "ITBCR Contract %s %s" % (direction, _token()),
            "type": direction,
            "project_id": project.id,
            "partner_id": partner.id,
            "company_id": env.company.id,
            "currency_id": env.company.currency_id.id,
            "tax_id": _tax("sale" if direction == "out" else "purchase").id,
        }
    )


def _shared_records():
    project = _project()
    partner = _partner()
    return {
        "project": project,
        "partner": partner,
        "contract_in": _contract(project, partner, "in"),
        "contract_out": _contract(project, partner, "out"),
    }


def _base_vals(model_name, context, shared):
    vals = _context_defaults(context)
    project = shared["project"]
    partner = shared["partner"]
    currency = env.company.currency_id
    today = fields.Date.context_today(env.user)

    if model_name == "sc.invoice.registration":
        direction = vals.get("direction") or "input"
        contract = shared["contract_out"] if direction == "output" else shared["contract_in"]
        vals.update(
            {
                "project_id": project.id,
                "partner_id": partner.id,
                "contract_id": contract.id,
                "currency_id": currency.id,
                "document_no": "ITBCR-DOC-%s" % _token(),
                "document_date": today,
                "application_date": today,
                "invoice_date": today,
                "invoice_no": "ITBCR-INV-%s" % _token(),
                "invoice_code": "ITBCR-CODE",
                "invoice_type": "增值税专用发票",
                "tax_rate": "9%",
                "amount_no_tax": 100.0,
                "tax_amount": 9.0,
                "amount_total": 109.0,
                "actual_invoice_amount": 109.0,
                "invoice_content": vals.get("invoice_content") or "发票税务办理",
            }
        )
    elif model_name == "sc.tax.deduction.registration":
        vals.update(
            {
                "project_id": project.id,
                "partner_id": partner.id,
                "currency_id": currency.id,
                "document_no": "ITBCR-TAX-%s" % _token(),
                "document_date": today,
                "deduction_confirm_date": today,
                "invoice_no": "ITBCR-TAXINV-%s" % _token(),
                "invoice_code": "ITBCR-TAXCODE",
                "invoice_date": today,
                "invoice_amount_untaxed": 100.0,
                "invoice_tax_amount": 9.0,
                "invoice_amount_total": 109.0,
                "deduction_amount": 100.0,
                "deduction_tax_amount": 9.0,
                "is_transfer_out": vals.get("is_transfer_out", False),
                "deduction_reason": vals.get("deduction_reason") or "抵扣登记",
            }
        )
    else:
        raise AssertionError("unsupported category model: %s" % model_name)
    return vals


def _run_category(code, action_xmlid, shared, failures):
    action = env.ref(action_xmlid, raise_if_not_found=False)
    if not action:
        failures.append("%s: missing action %s" % (code, action_xmlid))
        return {}
    context = _parse(action.context, {})
    domain = _parse(action.domain, [])
    model_name = action.res_model
    vals = _base_vals(model_name, context, shared)
    record = env[model_name].sudo().with_context(**context).create(vals)
    if record.business_category_id.code != code:
        failures.append(
            "%s: expected business_category_id.code=%s, got %s"
            % (code, code, record.business_category_id.code)
        )
    domain_with_record = ["&", ("id", "=", record.id)] + list(domain)
    matched = env[model_name].sudo().search(domain_with_record, limit=1)
    if matched.id != record.id:
        failures.append(
            "%s: created %s/%s is not visible through action domain %s"
            % (code, model_name, record.id, action.domain)
        )
    return {
        "code": code,
        "action": action_xmlid,
        "model": model_name,
        "record_id": record.id,
        "business_category": record.business_category_id.code,
        "visible": matched.id == record.id,
    }


failures = []
rows = []

try:
    shared = _shared_records()
    for code, action_xmlid in CATEGORIES:
        with env.cr.savepoint():
            rows.append(_run_category(code, action_xmlid, shared, failures))
except Exception as err:
    failures.append("unexpected error: %s" % err)
    failures.append(traceback.format_exc())

result = {
    "audit": "invoice_tax_business_category_runtime_audit",
    "status": "PASS" if not failures else "FAIL",
    "category_count": len(CATEGORIES),
    "rows": rows,
    "failures": failures,
}
print("INVOICE_TAX_BUSINESS_CATEGORY_RUNTIME_AUDIT: %s" % json.dumps(result, ensure_ascii=False, sort_keys=True))
if failures:
    print("FAILURES:")
    for failure in failures:
        print("- %s" % failure)

sys.exit(0 if not failures else 1)
