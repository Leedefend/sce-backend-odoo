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
    suffix = "invoice_tax_role_audit"
    return {
        "initiator": _audit_user(
            "sc_%s_initiator" % suffix,
            "审计-发票税务经办",
            ["smart_construction_core.group_sc_cap_business_initiator"],
        ),
        "finance_read": _audit_user(
            "sc_%s_read" % suffix,
            "审计-发票税务只读",
            ["smart_construction_core.group_sc_cap_finance_read"],
        ),
        "finance_user": _audit_user(
            "sc_%s_user" % suffix,
            "审计-发票税务财务经办",
            ["smart_construction_core.group_sc_cap_finance_user"],
        ),
        "finance_manager": _audit_user(
            "sc_%s_manager" % suffix,
            "审计-发票税务财务经理",
            ["smart_construction_core.group_sc_cap_finance_manager"],
        ),
    }


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


def _grant_project_visibility(project, users):
    partner_ids = [user.partner_id.id for user in users.values() if user.partner_id]
    if partner_ids:
        project.sudo().message_subscribe(partner_ids=partner_ids)


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
            "subject": "ITRP Contract %s %s" % (direction, _token()),
            "type": direction,
            "project_id": project.id,
            "partner_id": partner.id,
            "company_id": env.company.id,
            "currency_id": env.company.currency_id.id,
            "tax_id": _tax("ITRP Tax", "sale" if direction == "out" else "purchase").id,
        }
    )


def _invoice_vals(project, partner, contract):
    today = fields.Date.context_today(env.user)
    return {
        "source_kind": "output_invoice_tax",
        "direction": "output",
        "invoice_content": "销项开票登记",
        "project_id": project.id,
        "partner_id": partner.id,
        "contract_id": contract.id,
        "currency_id": env.company.currency_id.id,
        "document_no": "ITRP-INV-DOC-%s" % _token(),
        "document_date": today,
        "application_date": today,
        "invoice_date": today,
        "invoice_no": "ITRP-INV-%s" % _token(),
        "invoice_code": "ITRP-CODE",
        "invoice_type": "增值税专用发票",
        "amount_no_tax": 100.0,
        "tax_amount": 9.0,
        "amount_total": 109.0,
    }


def _tax_deduction_vals(project, partner):
    today = fields.Date.context_today(env.user)
    return {
        "project_id": project.id,
        "partner_id": partner.id,
        "currency_id": env.company.currency_id.id,
        "document_no": "ITRP-DED-%s" % _token(),
        "document_date": today,
        "deduction_confirm_date": today,
        "invoice_no": "ITRP-DED-INV-%s" % _token(),
        "invoice_code": "ITRP-DED-CODE",
        "invoice_date": today,
        "invoice_amount_untaxed": 100.0,
        "invoice_tax_amount": 9.0,
        "invoice_amount_total": 109.0,
        "deduction_amount": 100.0,
        "deduction_tax_amount": 9.0,
        "deduction_reason": "抵扣登记",
        "is_transfer_out": False,
    }


def _run_invoice_roles(users, failures):
    project = _project("ITRP Invoice Project")
    _grant_project_visibility(project, users)
    partner = _partner("ITRP Invoice Partner")
    contract = _contract(project, partner, "out")
    values = _invoice_vals(project, partner, contract)
    _expect_exception(
        "invoice_registration.read_user_create_blocked",
        lambda: env["sc.invoice.registration"].with_user(users["finance_read"]).create(values),
        failures,
    )
    invoice = env["sc.invoice.registration"].with_user(users["initiator"]).create(values)
    _expect(
        bool(invoice.with_user(users["finance_read"]).read(["name", "state"])),
        "invoice_registration.read_user_can_read",
        failures,
    )
    invoice.with_user(users["initiator"]).action_confirm()
    _expect_state("invoice_registration.initiator_confirm", invoice, "confirmed", failures)
    _expect_exception(
        "invoice_registration.initiator_register_blocked",
        invoice.with_user(users["initiator"]).action_register,
        failures,
    )
    _expect_exception(
        "invoice_registration.finance_user_register_blocked",
        invoice.with_user(users["finance_user"]).action_register,
        failures,
    )
    invoice.with_user(users["finance_manager"]).action_register()
    _expect_state("invoice_registration.finance_manager_register", invoice, "registered", failures)
    return {"invoice": invoice.id}


def _run_tax_deduction_roles(users, failures):
    project = _project("ITRP Tax Deduction Project")
    _grant_project_visibility(project, users)
    partner = _partner("ITRP Tax Deduction Partner")
    values = _tax_deduction_vals(project, partner)
    _expect_exception(
        "tax_deduction.read_user_create_blocked",
        lambda: env["sc.tax.deduction.registration"].with_user(users["finance_read"]).create(values),
        failures,
    )
    deduction = env["sc.tax.deduction.registration"].with_user(users["initiator"]).create(values)
    _expect(
        bool(deduction.with_user(users["finance_read"]).read(["name", "state"])),
        "tax_deduction.read_user_can_read",
        failures,
    )
    deduction.with_user(users["initiator"]).action_confirm()
    _expect_state("tax_deduction.initiator_confirm", deduction, "confirmed", failures)
    _expect_exception(
        "tax_deduction.initiator_deduct_blocked",
        deduction.with_user(users["initiator"]).action_deduct,
        failures,
    )
    _expect_exception(
        "tax_deduction.finance_user_deduct_blocked",
        deduction.with_user(users["finance_user"]).action_deduct,
        failures,
    )
    deduction.with_user(users["finance_manager"]).action_deduct()
    _expect_state("tax_deduction.finance_manager_deduct", deduction, "deducted", failures)
    return {"deduction": deduction.id}


failures = []
coverage = {}

try:
    users = _users()
    coverage.update(_run_invoice_roles(users, failures))
    coverage.update(_run_tax_deduction_roles(users, failures))
except Exception as err:
    failures.append("unexpected error: %s" % err)
    failures.append(traceback.format_exc())

result = {
    "audit": "invoice_tax_role_permission_audit",
    "status": "PASS" if not failures else "FAIL",
    "covered": ["invoice_registration", "tax_deduction_registration"],
    "roles": ["finance_read", "business_initiator", "finance_user", "finance_manager"],
    "coverage": coverage,
    "failures": failures,
}
print("INVOICE_TAX_ROLE_PERMISSION_AUDIT: %s" % json.dumps(result, ensure_ascii=False, sort_keys=True))
if failures:
    print("FAILURES:")
    for failure in failures:
        print("- %s" % failure)

sys.exit(0 if not failures else 1)
