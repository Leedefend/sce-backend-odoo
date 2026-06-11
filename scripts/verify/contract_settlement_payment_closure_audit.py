# -*- coding: utf-8 -*-
import base64
import json
import re
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


def _guard_code(err):
    match = re.search(r"\[SC_GUARD:([A-Z0-9_]+)\]", str(err or ""))
    return match.group(1) if match else None


def _expect_guard(label, code, func, failures):
    try:
        with env.cr.savepoint():  # noqa: F821
            func()
    except Exception as err:
        actual = _guard_code(err)
        if actual != code:
            failures.append("%s: expected %s, got %s" % (label, code, actual or type(err).__name__))
            return False
        return True
    failures.append("%s: expected guard %s, got success" % (label, code))
    return False


def _ensure_groups():
    user = env.user.sudo()  # noqa: F821
    for xmlid in (
        "smart_construction_core.group_sc_cap_project_manager",
        "smart_construction_core.group_sc_cap_settlement_manager",
        "smart_construction_core.group_sc_cap_finance_user",
        "smart_construction_core.group_sc_cap_finance_manager",
    ):
        group = env.ref(xmlid, raise_if_not_found=False)  # noqa: F821
        if group and group.id not in user.groups_id.ids:
            user.write({"groups_id": [(4, group.id)]})
    env.invalidate_all()  # noqa: F821


def _set_validated(record):
    env.flush_all()  # noqa: F821
    table = record._table
    env.cr.execute(  # noqa: F821
        "UPDATE %s SET validation_status=%%s WHERE id=%%s" % table,
        ("validated", record.id),
    )
    env.invalidate_all()  # noqa: F821
    record.invalidate_recordset()
    if record.validation_status != "validated":
        record.sudo().with_context(skip_validation_check=True).write({"validation_status": "validated"})
        env.flush_all()  # noqa: F821
        env.invalidate_all()  # noqa: F821
        record.invalidate_recordset()


def _tax(company):
    Tax = env["account.tax"].sudo()  # noqa: F821
    tax = Tax.search(
        [
            ("company_id", "=", company.id),
            ("type_tax_use", "in", ["purchase", "all"]),
            ("amount_type", "=", "percent"),
            ("price_include", "=", False),
        ],
        limit=1,
    )
    if tax:
        return tax
    return Tax.create(
        {
            "name": "CSPC Purchase Tax %s" % _token(),
            "amount_type": "percent",
            "amount": 0.0,
            "type_tax_use": "purchase",
            "price_include": False,
            "company_id": company.id,
        }
    )


def _uom_product():
    uom = env.ref("uom.product_uom_unit", raise_if_not_found=False) or env["uom.uom"].sudo().search([], limit=1)  # noqa: F821
    product = env["product.product"].sudo().create(  # noqa: F821
        {
            "name": "CSPC Service %s" % _token(),
            "type": "service",
            "uom_id": uom.id,
            "uom_po_id": uom.id,
        }
    )
    return uom, product


def _purchase_order(partner, company, amount):
    uom, product = _uom_product()
    po = env["purchase.order"].sudo().create(  # noqa: F821
        {
            "partner_id": partner.id,
            "company_id": company.id,
            "currency_id": company.currency_id.id,
            "order_line": [
                (
                    0,
                    0,
                    {
                        "name": "CSPC PO Line",
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
    env.flush_all()  # noqa: F821
    env.cr.execute("UPDATE purchase_order SET state=%s WHERE id=%s", ("purchase", po.id))  # noqa: F821
    env.invalidate_all()  # noqa: F821
    po.invalidate_recordset()
    return po


def _attachment(record):
    env["ir.attachment"].sudo().create(  # noqa: F821
        {
            "name": "contract-settlement-payment-closure.txt",
            "datas": base64.b64encode(b"contract settlement payment closure"),
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
    partner = env["res.partner"].sudo().create({"name": "CSPC Partner %s" % token})  # noqa: F821
    project = env["project.project"].sudo().create(  # noqa: F821
        {
            "name": "CSPC Project %s" % token,
            "code": "CSPC-%s" % token,
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
            "subject": "CSPC Expense Contract %s" % token,
            "type": "in",
            "project_id": project.id,
            "partner_id": partner.id,
            "company_id": company.id,
            "currency_id": company.currency_id.id,
            "tax_id": _tax(company).id,
        }
    )

    settlement_amount = 1200.0
    payment_amount = 450.0
    po = _purchase_order(partner, company, settlement_amount)
    settlement = env["sc.settlement.order"].sudo().create(  # noqa: F821
        {
            "project_id": project.id,
            "partner_id": partner.id,
            "contract_id": contract.id,
            "company_id": company.id,
            "currency_id": company.currency_id.id,
            "purchase_order_ids": [(6, 0, [po.id])],
        }
    )
    env["sc.settlement.order.line"].sudo().create(  # noqa: F821
        {
            "settlement_id": settlement.id,
            "contract_id": contract.id,
            "name": "CSPC Settlement Line",
            "qty": 1.0,
            "price_unit": settlement_amount,
        }
    )
    settlement.action_submit()
    settlement.invalidate_recordset()
    _expect(settlement.state == "submit", "settlement.state_after_submit: expected submit", failures)
    _set_validated(settlement)
    settlement.action_on_tier_approved()
    settlement.invalidate_recordset()
    _expect(settlement.state == "approve", "settlement.state_after_approval: expected approve", failures)

    payment = env["payment.request"].sudo().create(  # noqa: F821
        {
            "project_id": project.id,
            "partner_id": partner.id,
            "contract_id": contract.id,
            "settlement_id": settlement.id,
            "currency_id": company.currency_id.id,
            "amount": payment_amount,
            "type": "pay",
        }
    )
    _attachment(payment)
    payment.action_submit()
    payment.invalidate_recordset()
    _expect(payment.state == "submit", "payment.state_after_submit: expected submit", failures)
    _set_validated(payment)
    payment.action_on_tier_approved()
    payment.invalidate_recordset()
    _expect(payment.state == "approved", "payment.state_after_approval: expected approved", failures)
    payment.action_done()
    payment.invalidate_recordset()
    settlement.invalidate_recordset()
    _expect(payment.state == "done", "payment.state_after_done: expected done", failures)

    ledger_count = env["payment.ledger"].sudo().search_count([("payment_request_id", "=", payment.id)])  # noqa: F821
    _expect(ledger_count == 1, "payment.ledger_count: expected 1", failures)
    _expect(settlement.paid_amount == payment_amount, "settlement.paid_amount: expected payment amount", failures)
    _expect(settlement.amount_payable == settlement_amount - payment_amount, "settlement.amount_payable: expected balance", failures)

    summary = env["sc.contract.recon.summary"].sudo().create({"contract_id": contract.id})  # noqa: F821
    _expect(summary.settlement_total == settlement_amount, "summary.settlement_total: expected settlement amount", failures)
    _expect(summary.payment_total == payment_amount, "summary.payment_total: expected payment amount", failures)
    _expect(summary.delta == settlement_amount - payment_amount, "summary.delta: expected balance", failures)

    _expect_guard(
        "settlement direct cancel with paid payment",
        "P0_SETTLEMENT_CANCEL_BLOCKED",
        lambda: settlement.write({"state": "cancel"}),
        failures,
    )

    overpay = env["payment.request"].sudo().create(  # noqa: F821
        {
            "project_id": project.id,
            "partner_id": partner.id,
            "contract_id": contract.id,
            "settlement_id": settlement.id,
            "currency_id": company.currency_id.id,
            "amount": settlement_amount,
            "type": "pay",
        }
    )
    _attachment(overpay)
    _expect_guard(
        "settlement overpay submit blocked",
        "P0_PAYMENT_OVER_BALANCE",
        overpay.action_submit,
        failures,
    )

    payment_events = _audit_events("payment.request", payment.id)
    _expect("payment_submitted" in payment_events, "payment.audit: missing payment_submitted", failures)
    _expect("payment_approved" in payment_events, "payment.audit: missing payment_approved", failures)
    _expect("payment_paid" in payment_events, "payment.audit: missing payment_paid", failures)

    evidence = {
        "contract_id": contract.id,
        "settlement_id": settlement.id,
        "payment_request_id": payment.id,
        "payment_ledger_count": ledger_count,
        "settlement_total": summary.settlement_total,
        "payment_total": summary.payment_total,
        "delta": summary.delta,
        "overpay_request_id": overpay.id,
        "payment_events": payment_events,
    }
except Exception as err:
    failures.append("unexpected error: %s" % err)
    failures.append(traceback.format_exc())

result = {
    "audit": "contract_settlement_payment_closure_audit",
    "status": "PASS" if not failures else "FAIL",
    "evidence": evidence,
    "failures": failures,
}
print("CONTRACT_SETTLEMENT_PAYMENT_CLOSURE_AUDIT: %s" % json.dumps(result, ensure_ascii=False, sort_keys=True))
if failures:
    print("FAILURES:")
    for failure in failures:
        print("- %s" % failure)

sys.exit(0 if not failures else 1)
