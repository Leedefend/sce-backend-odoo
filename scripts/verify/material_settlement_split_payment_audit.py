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


def _ensure_groups():
    user = env.user.sudo()
    for xmlid in (
        "smart_construction_core.group_sc_cap_business_initiator",
        "smart_construction_core.group_sc_cap_finance_user",
        "smart_construction_core.group_sc_cap_finance_manager",
        "smart_construction_core.group_sc_cap_material_user",
        "smart_construction_core.group_sc_cap_material_manager",
    ):
        group = env.ref(xmlid, raise_if_not_found=False)
        if group and group.id not in user.groups_id.ids:
            user.write({"groups_id": [(4, group.id)]})
    env.invalidate_all()


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


def _approve_payment_request(request):
    request.action_submit()
    request.invalidate_recordset()
    _set_validated(request, "payment_request")
    request.action_on_tier_approved()
    request.invalidate_recordset()
    if request.state == "approve":
        request.action_set_approved()
    request.invalidate_recordset()


def _pay_request(request):
    execution = env["sc.payment.execution"].sudo().create(
        {
            "payment_request_id": request.id,
            "payment_account_name": "MSSP付款户名",
            "payment_account_no": "MSSP-PAYER-%s" % _token(),
            "receipt_account_name": "MSSP收款户名",
            "receipt_account_no": "MSSP-PAYEE-%s" % _token(),
        }
    )
    execution.action_confirm()
    execution.action_paid()
    execution.invalidate_recordset()
    request.invalidate_recordset()
    return execution


def _project():
    return env["project.project"].sudo().create(
        {
            "name": "MSSP Project %s" % _token(),
            "manager_id": env.user.id,
            "company_id": env.company.id,
        }
    )


def _supplier():
    return env["res.partner"].sudo().create(
        {
            "name": "MSSP Supplier %s" % _token(),
            "supplier_rank": 1,
        }
    )


def _product():
    uom = env.ref("uom.product_uom_unit", raise_if_not_found=False) or env["uom.uom"].sudo().search([], limit=1)
    product = env["product.product"].sudo().create(
        {
            "name": "MSSP Material %s" % _token(),
            "default_code": "MSSP-%s" % _token(),
            "type": "product",
            "uom_id": uom.id,
            "uom_po_id": uom.id,
        }
    )
    return product


def _create_settlement():
    project = _project()
    supplier = _supplier()
    product = _product()
    settlement = env["sc.material.settlement"].sudo().create(
        {
            "project_id": project.id,
            "supplier_id": supplier.id,
            "settlement_date": fields.Date.context_today(env["sc.material.settlement"]),
            "line_ids": [
                (
                    0,
                    0,
                    {
                        "product_id": product.id,
                        "product_uom_id": product.uom_id.id,
                        "qty": 4.0,
                        "unit_price": 25.0,
                        "tax_rate": 0.0,
                        "note": "MSSP材料结算行",
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
    first_request = settlement.payment_request_id
    _expect(bool(first_request), "first_request: expected auto generated request", failures)
    if first_request:
        _expect(first_request.amount == 100.0, "first_request.amount: expected full settlement amount", failures)
        first_request.write({"amount": 60.0})
        _approve_payment_request(first_request)
        first_execution = _pay_request(first_request)
        _expect(first_request.state == "done", "first_request.state: expected done after first payment", failures)

        action = settlement.action_create_remaining_payment_request()
        second_request = env["payment.request"].sudo().browse(action.get("res_id"))
        _expect(bool(second_request), "second_request: expected remaining request", failures)
        if second_request:
            _expect(second_request.material_settlement_id == settlement, "second_request.material_settlement_id: expected settlement", failures)
            _expect(second_request.amount == 40.0, "second_request.amount: expected remaining amount 40", failures)
            _approve_payment_request(second_request)
            second_execution = _pay_request(second_request)
            _expect(second_request.state == "done", "second_request.state: expected done after second payment", failures)
        else:
            second_execution = False

        over_request = env["payment.request"].sudo().create(
            {
                "type": "pay",
                "project_id": settlement.project_id.id,
                "partner_id": settlement.supplier_id.id,
                "amount": 1.0,
                "currency_id": settlement.currency_id.id,
                "material_settlement_id": settlement.id,
            }
        )
        _expect_exception(
            "over_request.submit_blocked_after_full_split_payment",
            over_request.action_submit,
            failures,
        )
        settlement.invalidate_recordset()
        _expect(settlement.payment_request_count >= 2, "settlement.payment_request_count: expected at least two requests", failures)
        _expect(settlement.payment_paid_amount == 100.0, "settlement.payment_paid_amount: expected fully paid", failures)
        _expect(settlement.payment_remaining_amount == 0.0, "settlement.payment_remaining_amount: expected zero", failures)
    else:
        first_execution = False
        second_request = False
        second_execution = False

    evidence = {
        "settlement": settlement.id,
        "settlement_amount": settlement.amount_total,
        "first_request": first_request.id if first_request else False,
        "first_execution": first_execution.id if first_execution else False,
        "second_request": second_request.id if second_request else False,
        "second_execution": second_execution.id if second_execution else False,
        "payment_request_count": settlement.payment_request_count,
        "payment_paid_amount": settlement.payment_paid_amount,
        "payment_remaining_amount": settlement.payment_remaining_amount,
    }
except Exception as err:
    failures.append("unexpected error: %s" % err)
    failures.append(traceback.format_exc())

result = {
    "audit": "material_settlement_split_payment_audit",
    "status": "PASS" if not failures else "FAIL",
    "evidence": evidence,
    "failures": failures,
}
print("MATERIAL_SETTLEMENT_SPLIT_PAYMENT_AUDIT: %s" % json.dumps(result, ensure_ascii=False, sort_keys=True))
if failures:
    print("FAILURES:")
    for failure in failures:
        print("- %s" % failure)

sys.exit(0 if not failures else 1)
