# -*- coding: utf-8 -*-
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


def _ensure_groups():
    user = env.user.sudo()  # noqa: F821
    for xmlid in (
        "smart_construction_core.group_sc_cap_business_initiator",
        "smart_construction_core.group_sc_cap_finance_user",
        "smart_construction_core.group_sc_cap_finance_manager",
        "smart_construction_core.group_sc_cap_material_user",
        "smart_construction_core.group_sc_cap_material_manager",
    ):
        group = env.ref(xmlid, raise_if_not_found=False)  # noqa: F821
        if group and group.id not in user.groups_id.ids:
            user.write({"groups_id": [(4, group.id)]})
    env.invalidate_all()  # noqa: F821


def _set_validated(record, table):
    env.flush_all()  # noqa: F821
    env.cr.execute("UPDATE %s SET validation_status=%%s WHERE id=%%s" % table, ("validated", record.id))  # noqa: F821
    env.invalidate_all()  # noqa: F821
    record.invalidate_recordset()
    if "validation_status" in record._fields and record.validation_status != "validated":
        record.sudo().with_context(skip_validation_check=True).write({"validation_status": "validated"})
        env.flush_all()  # noqa: F821
        env.invalidate_all()  # noqa: F821
        record.invalidate_recordset()


def _approve_payment_request(request):
    request.action_submit()
    request.invalidate_recordset()
    _set_validated(request, "payment_request")
    request.action_on_tier_approved()
    request.invalidate_recordset()
    if request.state == "approve":
        request.action_set_approved()
    request.invalidate_recordset()


def _pay_request(request, suffix):
    execution = env["sc.payment.execution"].sudo().create(  # noqa: F821
        {
            "payment_request_id": request.id,
            "payment_account_name": "MSPR付款户名",
            "payment_account_no": "MSPR-PAYER-%s-%s" % (_token(), suffix),
            "receipt_account_name": "MSPR收款户名",
            "receipt_account_no": "MSPR-PAYEE-%s-%s" % (_token(), suffix),
        }
    )
    execution.action_confirm()
    execution.action_paid()
    execution.invalidate_recordset()
    request.invalidate_recordset()
    return execution


def _project():
    return env["project.project"].sudo().create(  # noqa: F821
        {
            "name": "MSPR Project %s" % _token(),
            "manager_id": env.user.id,  # noqa: F821
            "company_id": env.company.id,  # noqa: F821
        }
    )


def _supplier():
    return env["res.partner"].sudo().create(  # noqa: F821
        {
            "name": "MSPR Supplier %s" % _token(),
            "supplier_rank": 1,
        }
    )


def _product():
    uom = env.ref("uom.product_uom_unit", raise_if_not_found=False) or env["uom.uom"].sudo().search([], limit=1)  # noqa: F821
    return env["product.product"].sudo().create(  # noqa: F821
        {
            "name": "MSPR Material %s" % _token(),
            "default_code": "MSPR-%s" % _token(),
            "type": "product",
            "uom_id": uom.id,
            "uom_po_id": uom.id,
        }
    )


def _create_settlement():
    project = _project()
    supplier = _supplier()
    product = _product()
    settlement = env["sc.material.settlement"].sudo().create(  # noqa: F821
        {
            "project_id": project.id,
            "supplier_id": supplier.id,
            "settlement_date": fields.Date.context_today(env["sc.material.settlement"]),  # noqa: F821
            "line_ids": [
                (
                    0,
                    0,
                    {
                        "product_id": product.id,
                        "product_uom_id": product.uom_id.id,
                        "qty": 2.0,
                        "unit_price": 50.0,
                        "tax_rate": 0.0,
                        "note": "MSPR材料结算行",
                    },
                )
            ],
        }
    )
    settlement.action_submit()
    settlement.action_confirm()
    settlement.invalidate_recordset()
    return settlement


failures = []
evidence = {}

try:
    _ensure_groups()
    settlement = _create_settlement()
    request = settlement.payment_request_id
    _expect(bool(request), "payment_request: expected auto generated request", failures)
    if request:
        _approve_payment_request(request)
        first_execution = _pay_request(request, "FIRST")
        ledger_before = env["payment.ledger"].sudo().search([("payment_request_id", "=", request.id)], limit=1)  # noqa: F821
        settlement.invalidate_recordset()
        _expect(request.state == "done", "request.state: expected done after first payment", failures)
        _expect(first_execution.state == "paid", "first_execution.state: expected paid", failures)
        _expect(bool(ledger_before), "ledger_before: expected payment ledger", failures)
        _expect(settlement.payment_paid_amount == 100.0, "settlement.payment_paid_amount: expected 100 before reversal", failures)
        _expect(settlement.payment_remaining_amount == 0.0, "settlement.payment_remaining_amount: expected 0 before reversal", failures)

        first_execution.action_cancel()
        first_execution.invalidate_recordset()
        request.invalidate_recordset()
        settlement.invalidate_recordset()
        ledger_after_reversal = env["payment.ledger"].sudo().search([("payment_request_id", "=", request.id)], limit=1)  # noqa: F821
        _expect(first_execution.state == "cancel", "first_execution.state: expected cancel after reversal", failures)
        _expect(request.state == "approved", "request.state: expected approved after reversal", failures)
        _expect(not ledger_after_reversal, "ledger_after_reversal: expected ledger removed", failures)
        _expect(settlement.payment_paid_amount == 0.0, "settlement.payment_paid_amount: expected 0 after reversal", failures)
        _expect(settlement.payment_remaining_amount == 100.0, "settlement.payment_remaining_amount: expected 100 after reversal", failures)

        second_execution = _pay_request(request, "SECOND")
        second_execution.invalidate_recordset()
        request.invalidate_recordset()
        settlement.invalidate_recordset()
        ledger_after_repay = env["payment.ledger"].sudo().search([("payment_request_id", "=", request.id)], limit=1)  # noqa: F821
        _expect(second_execution.state == "paid", "second_execution.state: expected paid", failures)
        _expect(request.state == "done", "request.state: expected done after repay", failures)
        _expect(bool(ledger_after_repay), "ledger_after_repay: expected payment ledger", failures)
        _expect(settlement.payment_paid_amount == 100.0, "settlement.payment_paid_amount: expected 100 after repay", failures)
        _expect(settlement.payment_remaining_amount == 0.0, "settlement.payment_remaining_amount: expected 0 after repay", failures)
    else:
        first_execution = False
        second_execution = False

    evidence = {
        "settlement": settlement.id,
        "payment_request": request.id if request else False,
        "first_execution": first_execution.id if first_execution else False,
        "second_execution": second_execution.id if second_execution else False,
        "request_state": request.state if request else False,
        "payment_paid_amount": settlement.payment_paid_amount,
        "payment_remaining_amount": settlement.payment_remaining_amount,
    }
except Exception as err:
    failures.append("unexpected error: %s" % err)
    failures.append(traceback.format_exc())

result = {
    "audit": "material_settlement_payment_reversal_audit",
    "status": "PASS" if not failures else "FAIL",
    "evidence": evidence,
    "failures": failures,
}
print("MATERIAL_SETTLEMENT_PAYMENT_REVERSAL_AUDIT: %s" % json.dumps(result, ensure_ascii=False, sort_keys=True))
if failures:
    print("FAILURES:")
    for failure in failures:
        print("- %s" % failure)

sys.exit(0 if not failures else 1)
