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


def _attach_evidence(record, name="role-permission-evidence.txt"):
    attachment = env["ir.attachment"].sudo().create(
        {
            "name": name,
            "res_model": record._name,
            "res_id": record.id,
            "type": "binary",
            "datas": "cm9sZS1wZXJtaXNzaW9uLWF1ZGl0Cg==",
            "mimetype": "text/plain",
        }
    )
    if "attachment_ids" in record._fields:
        record.sudo().write({"attachment_ids": [(4, attachment.id)]})
    return attachment


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
    suffix = "finance_role_audit"
    return {
        "initiator": _audit_user(
            "sc_%s_initiator" % suffix,
            "审计-业务经办",
            ["smart_construction_core.group_sc_cap_business_initiator"],
        ),
        "finance_read": _audit_user(
            "sc_%s_read" % suffix,
            "审计-财务只读",
            ["smart_construction_core.group_sc_cap_finance_read"],
        ),
        "finance_user": _audit_user(
            "sc_%s_user" % suffix,
            "审计-财务经办",
            ["smart_construction_core.group_sc_cap_finance_user"],
        ),
        "finance_manager": _audit_user(
            "sc_%s_manager" % suffix,
            "审计-财务审批",
            ["smart_construction_core.group_sc_cap_finance_manager"],
        ),
    }


def _partner(name):
    return env["res.partner"].sudo().create({"name": "%s %s" % (name, _token())})


def _project(name, funding=False):
    project = env["project.project"].sudo().create(
        {
            "name": "%s %s" % (name, _token()),
            "manager_id": env.user.id,
            "company_id": env.company.id,
            "funding_enabled": bool(funding),
        }
    )
    if funding:
        env["project.funding.baseline"].sudo().create(
            {
                "project_id": project.id,
                "total_amount": 100000.0,
                "state": "active",
            }
        )
    return project


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
            "subject": "FRP Contract %s %s" % (direction, _token()),
            "type": direction,
            "project_id": project.id,
            "partner_id": partner.id,
            "company_id": env.company.id,
            "currency_id": env.company.currency_id.id,
            "tax_id": _tax("FRP Tax", "sale" if direction == "out" else "purchase").id,
        }
    )


def _purchase_order(partner, amount):
    uom = env.ref("uom.product_uom_unit", raise_if_not_found=False) or env["uom.uom"].sudo().search([], limit=1)
    product = env["product.product"].sudo().create(
        {
            "name": "FRP Service %s" % _token(),
            "type": "service",
            "uom_id": uom.id,
            "uom_po_id": uom.id,
        }
    )
    return env["purchase.order"].sudo().create(
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
    settlement = env["sc.settlement.order"].sudo().create(
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
                        "name": "FRP Settlement Line",
                        "contract_id": contract.id,
                        "qty": 1.0,
                        "price_unit": amount,
                    },
                )
            ],
        }
    )
    settlement.action_submit()
    _set_validated(settlement, "sc_settlement_order")
    settlement.action_on_tier_approved()
    settlement.invalidate_recordset()
    return settlement


def _approved_request(project, partner, contract, amount, request_type):
    settlement = _settlement(project, partner, contract, amount) if request_type == "pay" else False
    request = env["payment.request"].sudo().create(
        {
            "name": "FRP Approved Request %s" % _token(),
            "type": request_type,
            "project_id": project.id,
            "partner_id": partner.id,
            "contract_id": contract.id,
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


def _payment_request_values(project, partner, contract, amount, request_type):
    return {
        "name": "FRP Request %s" % _token(),
        "type": request_type,
        "project_id": project.id,
        "partner_id": partner.id,
        "contract_id": contract.id,
        "currency_id": env.company.currency_id.id,
        "amount": amount,
    }


def _run_payment_request_roles(users, failures):
    project = _project("FRP Request Project")
    _grant_project_visibility(project, users)
    partner = _partner("FRP Request Partner")
    contract = _contract(project, partner, "out")
    values = _payment_request_values(project, partner, contract, 100.0, "receive")
    _expect_exception(
        "payment_request.read_user_create_blocked",
        lambda: env["payment.request"].with_user(users["finance_read"]).create(values),
        failures,
    )
    request = env["payment.request"].sudo().create(values)
    _expect(
        bool(request.with_user(users["finance_read"]).read(["name"])),
        "payment_request.read_user_can_read",
        failures,
    )
    request.with_user(users["initiator"]).action_submit()
    _expect_state("payment_request.initiator_submit", request, "submit", failures)
    _set_validated(request, "payment_request")
    _expect_exception(
        "payment_request.finance_user_approve_blocked",
        request.with_user(users["finance_user"]).action_approval_decision,
        failures,
    )
    env["payment.request"].with_user(users["finance_manager"]).browse(request.id).action_approval_decision()
    _set_validated(request, "payment_request")
    env["payment.request"].with_user(users["finance_manager"]).browse(request.id).action_set_approved()
    _expect_state("payment_request.finance_manager_approved", request, "approved", failures)
    _set_validated(request, "payment_request")
    _expect_exception(
        "payment_request.finance_user_done_blocked",
        request.with_user(users["finance_user"]).action_done,
        failures,
    )
    request.with_user(users["finance_manager"]).action_done()
    _expect_state("payment_request.finance_manager_done", request, "done", failures)
    return {"payment_request": request.id}


def _run_payment_execution_roles(users, failures):
    project = _project("FRP Execution Project", funding=True)
    _grant_project_visibility(project, users)
    partner = _partner("FRP Execution Partner")
    contract = _contract(project, partner, "in")
    request = _approved_request(project, partner, contract, 120.0, "pay")
    execution = env["sc.payment.execution"].sudo().create(
        {
            "payment_request_id": request.id,
            "project_id": project.id,
            "partner_id": partner.id,
            "contract_id": contract.id,
            "planned_amount": 120.0,
            "paid_amount": 120.0,
            "payment_account_name": "FRP付款户名",
            "payment_account_no": "FRP-PAYER-001",
            "receipt_account_name": "FRP收款户名",
            "receipt_account_no": "FRP-PAYEE-001",
        }
    )
    execution.with_user(users["finance_user"]).action_confirm()
    _expect_state("payment_execution.finance_user_confirm", execution, "confirmed", failures)
    _expect_exception(
        "payment_execution.finance_user_paid_blocked",
        execution.with_user(users["finance_user"]).action_paid,
        failures,
    )
    execution.with_user(users["finance_manager"]).action_paid()
    _expect_state("payment_execution.finance_manager_paid", execution, "paid", failures)
    return {"execution": execution.id, "payment_request": request.id}


def _run_receipt_income_roles(users, failures):
    project = _project("FRP Receipt Project")
    _grant_project_visibility(project, users)
    partner = _partner("FRP Receipt Partner")
    contract = _contract(project, partner, "out")
    request = _approved_request(project, partner, contract, 130.0, "receive")
    receipt = env["sc.receipt.income"].sudo().create(
        {
            "project_id": project.id,
            "partner_id": partner.id,
            "contract_id": contract.id,
            "payment_request_id": request.id,
            "amount": 130.0,
            "income_category": "业务收入",
            "receiving_account_name": "FRP收款账户",
            "receiving_account_no": "FRP-RECEIVE-001",
        }
    )
    receipt.with_user(users["finance_user"]).action_confirm()
    _expect_state("receipt_income.finance_user_confirm", receipt, "confirmed", failures)
    _expect_exception(
        "receipt_income.finance_user_received_blocked",
        receipt.with_user(users["finance_user"]).action_received,
        failures,
    )
    receipt.with_user(users["finance_manager"]).action_received()
    _expect_state("receipt_income.finance_manager_received", receipt, "received", failures)
    return {"receipt": receipt.id, "payment_request": request.id}


def _run_expense_claim_roles(users, failures):
    project = _project("FRP Expense Project", funding=True)
    _grant_project_visibility(project, users)
    partner = _partner("FRP Expense Partner")
    contract = _contract(project, partner, "in")
    request = _approved_request(project, partner, contract, 90.0, "pay")
    claim = env["sc.expense.claim"].sudo().create(
        {
            "claim_type": "expense",
            "expense_type": "项目费用报销单",
            "summary": "项目费用报销单",
            "project_id": project.id,
            "partner_id": partner.id,
            "payment_request_id": request.id,
            "amount": 90.0,
            "approved_amount": 90.0,
            "payee": "FRP费用收款人",
            "receipt_account_name": "FRP费用收款账户",
            "payee_account": "FRP-CLAIM-PAYEE-001",
            "payment_account_name": "FRP费用付款账户",
            "payer_account": "FRP-CLAIM-PAYER-001",
        }
    )
    _attach_evidence(claim, "expense-claim-role-permission-evidence.txt")
    claim.with_user(users["initiator"]).action_submit()
    _expect_state("expense_claim.initiator_submit", claim, "submit", failures)
    _set_validated(claim, "sc_expense_claim")
    _expect_exception(
        "expense_claim.finance_user_approve_blocked",
        claim.with_user(users["finance_user"]).action_approve,
        failures,
    )
    env["sc.expense.claim"].with_user(users["finance_manager"]).browse(claim.id).action_approve()
    _expect_state("expense_claim.finance_manager_approved", claim, "approved", failures)
    _expect_exception(
        "expense_claim.finance_user_done_blocked",
        claim.with_user(users["finance_user"]).action_done,
        failures,
    )
    claim.with_user(users["finance_manager"]).action_done()
    _expect_state("expense_claim.finance_manager_done", claim, "done", failures)
    return {"claim": claim.id, "payment_request": request.id}


failures = []
evidence = {}

try:
    users = _users()
    evidence["users"] = {key: user.login for key, user in users.items()}
    evidence["payment_request"] = _run_payment_request_roles(users, failures)
    evidence["payment_execution"] = _run_payment_execution_roles(users, failures)
    evidence["receipt_income"] = _run_receipt_income_roles(users, failures)
    evidence["expense_claim"] = _run_expense_claim_roles(users, failures)
except Exception as err:
    failures.append("unexpected error: %s" % err)
    failures.append(traceback.format_exc())

result = {
    "audit": "finance_role_permission_audit",
    "status": "PASS" if not failures else "FAIL",
    "evidence": evidence,
    "failures": failures,
}
print("FINANCE_ROLE_PERMISSION_AUDIT: %s" % json.dumps(result, ensure_ascii=False, sort_keys=True))
if failures:
    print("FAILURES:")
    for failure in failures:
        print("- %s" % failure)

sys.exit(0 if not failures else 1)
