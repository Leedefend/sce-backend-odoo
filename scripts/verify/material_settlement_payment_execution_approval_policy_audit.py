# -*- coding: utf-8 -*-
import json
import sys
import traceback

from odoo import fields
from odoo.exceptions import AccessError, UserError, ValidationError


def _token():
    return env["ir.sequence"].sudo().next_by_code("sc.business.fact") or str(fields.Datetime.now())  # noqa: F821


def _expect(condition, label, failures):
    if not condition:
        failures.append(label)
        return False
    return True


def _expect_exception(label, func, failures):
    try:
        with env.cr.savepoint():  # noqa: F821
            func()
    except (AccessError, UserError, ValidationError):
        return True
    except Exception as err:
        failures.append("%s: expected business exception, got %s: %s" % (label, type(err).__name__, err))
        return False
    failures.append("%s: expected business exception, got success" % label)
    return False


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


def _project():
    return env["project.project"].sudo().create(  # noqa: F821
        {
            "name": "MSPEAP Project %s" % _token(),
            "manager_id": env.user.id,  # noqa: F821
            "company_id": env.company.id,  # noqa: F821
        }
    )


def _supplier():
    return env["res.partner"].sudo().create(  # noqa: F821
        {
            "name": "MSPEAP Supplier %s" % _token(),
            "supplier_rank": 1,
        }
    )


def _product():
    uom = env.ref("uom.product_uom_unit", raise_if_not_found=False) or env["uom.uom"].sudo().search([], limit=1)  # noqa: F821
    return env["product.product"].sudo().create(  # noqa: F821
        {
            "name": "MSPEAP Material %s" % _token(),
            "default_code": "MSPEAP-%s" % _token(),
            "type": "product",
            "uom_id": uom.id,
            "uom_po_id": uom.id,
        }
    )


def _create_approved_material_payment_request(amount=100.0):
    product = _product()
    settlement = env["sc.material.settlement"].sudo().create(  # noqa: F821
        {
            "project_id": _project().id,
            "supplier_id": _supplier().id,
            "settlement_date": fields.Date.context_today(env["sc.material.settlement"]),  # noqa: F821
            "line_ids": [
                (
                    0,
                    0,
                    {
                        "product_id": product.id,
                        "product_uom_id": product.uom_id.id,
                        "qty": 1.0,
                        "unit_price": amount,
                        "tax_rate": 0.0,
                        "note": "MSPEAP材料结算行",
                    },
                )
            ],
        }
    )
    settlement.action_submit()
    settlement.action_confirm()
    settlement.invalidate_recordset()
    request = settlement.payment_request_id
    _approve_payment_request(request)
    return settlement, request


def _create_execution(request, suffix):
    return env["sc.payment.execution"].sudo().create(  # noqa: F821
        {
            "payment_request_id": request.id,
            "payment_account_name": "MSPEAP付款户名",
            "payment_account_no": "MSPEAP-PAYER-%s-%s" % (_token(), suffix),
            "receipt_account_name": "MSPEAP收款户名",
            "receipt_account_no": "MSPEAP-PAYEE-%s-%s" % (_token(), suffix),
        }
    )


def _payment_execution_policy():
    policy = env.ref("smart_construction_core.approval_policy_payment_execution", raise_if_not_found=False)  # noqa: F821
    if not policy:
        policy = env["sc.approval.policy"].sudo().search([("target_model", "=", "sc.payment.execution")], limit=1)  # noqa: F821
    return policy.sudo()


failures = []
evidence = {}
policy = False
original_policy_values = {}

try:
    _ensure_groups()
    policy = _payment_execution_policy()
    _expect(bool(policy), "payment_execution_policy: expected policy", failures)
    if policy:
        original_policy_values = {
            "approval_required": policy.approval_required,
            "mode": policy.mode,
            "active": policy.active,
        }

        policy.write({"active": True, "approval_required": False, "mode": "none"})
        optional_settlement, optional_request = _create_approved_material_payment_request()
        optional_execution = _create_execution(optional_request, "OPTIONAL")
        optional_execution.action_confirm()
        optional_execution.invalidate_recordset()
        _expect(optional_execution.state == "confirmed", "optional_execution.state: expected confirmed without approval", failures)
        optional_execution.action_paid()
        optional_execution.invalidate_recordset()
        optional_request.invalidate_recordset()
        optional_settlement.invalidate_recordset()
        _expect(optional_execution.state == "paid", "optional_execution.state: expected paid without approval", failures)
        _expect(optional_request.state == "done", "optional_request.state: expected done without execution approval", failures)
        _expect(optional_settlement.payment_paid_amount == 100.0, "optional_settlement.payment_paid_amount: expected paid", failures)

        policy.write({"active": True, "approval_required": True, "mode": "single"})
        required_settlement, required_request = _create_approved_material_payment_request()
        required_execution = _create_execution(required_request, "REQUIRED")
        required_execution.action_confirm()
        required_execution.invalidate_recordset()
        _expect(required_execution.validation_status in ("waiting", "pending", "no"), "required_execution.validation_status: expected approval requested", failures)
        _expect_exception(
            "required_execution.action_paid_before_approval",
            required_execution.action_paid,
            failures,
        )
        required_execution.invalidate_recordset()
        _set_validated(required_execution, "sc_payment_execution")
        required_execution.action_on_tier_approved()
        required_execution.invalidate_recordset()
        _expect(required_execution.state == "confirmed", "required_execution.state: expected confirmed after approval", failures)
        required_execution.action_paid()
        required_execution.invalidate_recordset()
        required_request.invalidate_recordset()
        required_settlement.invalidate_recordset()
        _expect(required_execution.state == "paid", "required_execution.state: expected paid after approval", failures)
        _expect(required_request.state == "done", "required_request.state: expected done after approved execution payment", failures)
        _expect(required_settlement.payment_paid_amount == 100.0, "required_settlement.payment_paid_amount: expected paid", failures)

        evidence = {
            "policy": policy.id,
            "optional_settlement": optional_settlement.id,
            "optional_execution": optional_execution.id,
            "required_settlement": required_settlement.id,
            "required_execution": required_execution.id,
            "required_execution_validation_status": required_execution.validation_status,
            "required_request_state": required_request.state,
        }
except Exception as err:
    failures.append("unexpected error: %s" % err)
    failures.append(traceback.format_exc())
finally:
    if policy and original_policy_values:
        try:
            policy.write(original_policy_values)
        except Exception as restore_err:
            failures.append("policy restore failed: %s" % restore_err)

result = {
    "audit": "material_settlement_payment_execution_approval_policy_audit",
    "status": "PASS" if not failures else "FAIL",
    "evidence": evidence,
    "failures": failures,
}
print("MATERIAL_SETTLEMENT_PAYMENT_EXECUTION_APPROVAL_POLICY_AUDIT: %s" % json.dumps(result, ensure_ascii=False, sort_keys=True))
if failures:
    print("FAILURES:")
    for failure in failures:
        print("- %s" % failure)

sys.exit(0 if not failures else 1)
