# -*- coding: utf-8 -*-
"""Prepare browser-verifiable finance handling records."""

import base64
import json
from pathlib import Path

from odoo import fields


ARTIFACT_DIR = Path("/mnt/artifacts/finance-browser-handling/current")
SETUP_JSON = ARTIFACT_DIR / "setup.json"
PREFIX = "FIN-BROWSER"
PASSWORD = "demo"


def _token():
    return env["ir.sequence"].sudo().next_by_code("sc.business.fact") or str(fields.Datetime.now())


def _group(xmlid):
    return env.ref(xmlid).id


def _ensure_browser_user():
    User = env["res.users"].sudo().with_context(no_reset_password=True, tracking_disable=True)
    login = "sc_browser_finance_manager"
    user = User.search([("login", "=", login)], limit=1)
    group_ids = [
        _group("smart_construction_core.group_sc_internal_user"),
        _group("smart_construction_core.group_sc_cap_business_initiator"),
        _group("smart_construction_core.group_sc_cap_finance_read"),
        _group("smart_construction_core.group_sc_cap_finance_user"),
        _group("smart_construction_core.group_sc_cap_finance_manager"),
    ]
    values = {
        "name": "浏览器财务闭环验收",
        "login": login,
        "email": "%s@example.invalid" % login,
        "company_id": env.company.id,
        "company_ids": [(6, 0, [env.company.id])],
        "groups_id": [(6, 0, group_ids)],
        "password": PASSWORD,
    }
    if user:
        user.write(values)
    else:
        user = User.create(values)
    return user


def _ref(xmlid):
    record = env.ref(xmlid, raise_if_not_found=False)
    return record.id if record else False


def _menu_ref(xmlid):
    menu = env.ref(xmlid, raise_if_not_found=False)
    action_id = False
    if menu and menu.action:
        action_id = int(str(menu.action).split(",")[-1])
    return {"xmlid": xmlid, "menu_id": menu.id if menu else False, "action_id": action_id}


def _attachment(record, name):
    attachment = env["ir.attachment"].sudo().create(
        {
            "name": "%s %s.txt" % (name, _token()),
            "type": "binary",
            "datas": base64.b64encode(b"finance browser handling acceptance").decode("ascii"),
            "res_model": record._name,
            "res_id": record.id,
            "mimetype": "text/plain",
        }
    )
    if "attachment_ids" in record._fields:
        record.sudo().write({"attachment_ids": [(4, attachment.id)]})
    return attachment


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


def _project(name, user, funding=False):
    project = env["project.project"].sudo().create(
        {
            "name": "%s %s %s" % (PREFIX, name, _token()),
            "manager_id": user.id,
            "company_id": env.company.id,
            "funding_enabled": bool(funding),
        }
    )
    project.message_subscribe(partner_ids=[user.partner_id.id])
    if funding:
        env["project.funding.baseline"].sudo().create(
            {
                "project_id": project.id,
                "total_amount": 100000.0,
                "state": "active",
            }
        )
    return project


def _partner(name):
    return env["res.partner"].sudo().create({"name": "%s %s %s" % (PREFIX, name, _token())})


def _contract(project, partner, direction):
    return env["construction.contract"].sudo().create(
        {
            "subject": "%s Contract %s %s" % (PREFIX, direction, _token()),
            "type": direction,
            "project_id": project.id,
            "partner_id": partner.id,
            "company_id": env.company.id,
            "currency_id": env.company.currency_id.id,
            "tax_id": _tax("%s Tax" % PREFIX, "sale" if direction == "out" else "purchase").id,
        }
    )


def _product(name):
    uom = env.ref("uom.product_uom_unit", raise_if_not_found=False) or env["uom.uom"].sudo().search([], limit=1)
    return env["product.product"].sudo().create(
        {
            "name": "%s %s %s" % (PREFIX, name, _token()),
            "type": "service",
            "uom_id": uom.id,
            "uom_po_id": uom.id,
        }
    )


def _settlement(project, partner, contract, amount):
    product = _product("Settlement Service")
    uom = product.uom_id
    purchase = env["purchase.order"].sudo().create(
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
    settlement = env["sc.settlement.order"].sudo().create(
        {
            "project_id": project.id,
            "partner_id": partner.id,
            "contract_id": contract.id,
            "settlement_type": "out",
            "purchase_order_ids": [(6, 0, purchase.ids)],
            "company_id": env.company.id,
            "currency_id": env.company.currency_id.id,
            "line_ids": [
                (
                    0,
                    0,
                    {
                        "name": "%s Settlement Line" % PREFIX,
                        "contract_id": contract.id,
                        "qty": 1.0,
                        "price_unit": amount,
                    },
                )
            ],
        }
    )
    settlement.action_submit()
    env.cr.execute(
        "UPDATE sc_settlement_order SET state=%s, validation_status=%s WHERE id=%s",
        ("approve", "validated", settlement.id),
    )
    env.invalidate_all()
    return settlement


def _approved_request(project, partner, contract, amount, request_type, settlement=False):
    request = env["payment.request"].sudo().create(
        {
            "name": "%s Approved Request %s" % (PREFIX, _token()),
            "type": request_type,
            "project_id": project.id,
            "partner_id": partner.id,
            "contract_id": contract.id,
            "settlement_id": settlement.id if settlement else False,
            "currency_id": env.company.currency_id.id,
            "amount": amount,
            "payment_account_name": "浏览器付款户名",
            "payment_account_no": "FB-PAYER-001",
        }
    )
    env.cr.execute(
        "UPDATE payment_request SET state=%s, validation_status=%s WHERE id=%s",
        ("approved", "validated", request.id),
    )
    env.invalidate_all()
    request.invalidate_recordset()
    _attachment(request, "browser-approved-request")
    return request


def _draft_request(user, name, request_type, amount, funding=False, settlement_required=False):
    project = _project(name, user, funding=funding)
    partner = _partner(name)
    contract = _contract(project, partner, "out" if request_type == "receive" else "in")
    settlement = _settlement(project, partner, contract, amount) if settlement_required else False
    request = env["payment.request"].sudo().create(
        {
            "name": "%s %s %s" % (PREFIX, name, _token()),
            "type": request_type,
            "project_id": project.id,
            "partner_id": partner.id,
            "contract_id": contract.id,
            "settlement_id": settlement.id if settlement else False,
            "currency_id": env.company.currency_id.id,
            "amount": amount,
            "payment_account_name": "浏览器付款户名",
            "payment_account_no": "FB-PAYER-REQ",
        }
    )
    _attachment(request, "browser-draft-request")
    return project, partner, contract, settlement, request


def _payment_execution(user):
    project, partner, contract, _settlement_record, _request = _draft_request(
        user, "付款登记", "pay", 130.0, funding=True, settlement_required=False
    )
    request = _approved_request(project, partner, contract, 130.0, "pay")
    execution = env["sc.payment.execution"].sudo().create(
        {
            "payment_request_id": request.id,
            "project_id": project.id,
            "partner_id": partner.id,
            "contract_id": contract.id,
            "planned_amount": 130.0,
            "paid_amount": 130.0,
            "payment_account_name": "浏览器付款账户",
            "payment_account_no": "FB-PAYER-EXEC",
            "payment_bank_name": "浏览器付款开户行",
            "receipt_account_name": "浏览器收款账户",
            "receipt_account_no": "FB-PAYEE-EXEC",
            "receipt_bank_name": "浏览器收款开户行",
        }
    )
    _attachment(execution, "browser-payment-execution")
    return execution


def _receipt_income(user):
    project, partner, contract, _settlement_record, _request = _draft_request(
        user, "收款登记", "receive", 140.0, funding=False, settlement_required=False
    )
    request = _approved_request(project, partner, contract, 140.0, "receive")
    receipt = env["sc.receipt.income"].sudo().create(
        {
            "project_id": project.id,
            "partner_id": partner.id,
            "contract_id": contract.id,
            "payment_request_id": request.id,
            "amount": 140.0,
            "income_category": "浏览器收款收入",
            "receiving_account_name": "浏览器收款账户",
            "receiving_account_no": "FB-RECEIVE-001",
            "receiving_bank_name": "浏览器收款开户行",
        }
    )
    _attachment(receipt, "browser-receipt-income")
    return receipt


def _expense_claim(user):
    project, partner, contract, _settlement_record, _request = _draft_request(
        user, "费用报销", "pay", 90.0, funding=True, settlement_required=False
    )
    request = _approved_request(project, partner, contract, 90.0, "pay")
    claim = env["sc.expense.claim"].sudo().create(
        {
            "claim_type": "expense",
            "expense_type": "项目费用报销单",
            "summary": "%s 项目费用报销 %s" % (PREFIX, _token()),
            "project_id": project.id,
            "partner_id": partner.id,
            "payment_request_id": request.id,
            "amount": 90.0,
            "approved_amount": 90.0,
            "payee": "浏览器费用收款人",
            "receipt_account_name": "浏览器费用收款账户",
            "payee_account": "FB-CLAIM-PAYEE",
            "payee_bank": "浏览器费用收款开户行",
            "payment_account_name": "浏览器费用付款账户",
            "payer_account": "FB-CLAIM-PAYER",
            "payer_bank": "浏览器费用付款开户行",
        }
    )
    _attachment(claim, "browser-expense-claim")
    return claim


def _case(key, label, model, record, menu_xmlid, steps, expected_state, ledger_model=False):
    ref = _menu_ref(menu_xmlid)
    return {
        "key": key,
        "label": label,
        "model": model,
        "record_id": record.id,
        "display_name": record.display_name,
        "menu": ref,
        "steps": steps,
        "expected_state": expected_state,
        "ledger_model": ledger_model,
    }


def main():
    ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)
    user = _ensure_browser_user()
    pay_project, _pay_partner, _pay_contract, _pay_settlement, pay_request = _draft_request(
        user, "付款申请", "pay", 110.0, funding=True, settlement_required=False
    )
    receive_project, _receive_partner, _receive_contract, _receive_settlement, receive_request = _draft_request(
        user, "收款申请", "receive", 120.0, funding=False, settlement_required=False
    )
    execution = _payment_execution(user)
    receipt = _receipt_income(user)
    claim = _expense_claim(user)
    payload = {
        "login": user.login,
        "password": PASSWORD,
        "db_name": env.cr.dbname,
        "company": env.company.name,
        "currency": env.company.currency_id.name,
        "actions": {
            "payment_request": _ref("smart_construction_core.action_payment_request_user_payment_apply"),
            "payment_execution": _ref("smart_construction_core.action_sc_payment_execution_company_finance_expense"),
            "receipt_income": _ref("smart_construction_core.action_sc_receipt_income_user_income"),
            "expense_claim": _ref("smart_construction_core.action_sc_expense_claim_reimbursement_request"),
        },
        "projects": [pay_project.id, receive_project.id],
        "cases": [
            _case(
                "payment_request_pay",
                "付款申请",
                "payment.request",
                pay_request,
                "smart_construction_core.menu_payment_request_user_payment_apply",
                ["提交审批", "审批通过", "批准", "完成"],
                "done",
                "payment.ledger",
            ),
            _case(
                "payment_request_receive",
                "收款申请",
                "payment.request",
                receive_request,
                "smart_construction_core.menu_payment_request_receive_apply",
                ["提交审批", "审批通过", "批准", "完成"],
                "done",
                "sc.treasury.ledger",
            ),
            _case(
                "payment_execution",
                "付款登记",
                "sc.payment.execution",
                execution,
                "smart_construction_core.menu_sc_payment_execution_company_finance_expense",
                ["提交审批", "审批通过", "已付款"],
                "paid",
                "payment.ledger",
            ),
            _case(
                "receipt_income",
                "收款登记",
                "sc.receipt.income",
                receipt,
                "smart_construction_core.menu_sc_receipt_income_user_income",
                ["提交审批", "审批通过", "已收款"],
                "received",
                "sc.treasury.ledger",
            ),
            _case(
                "expense_claim",
                "费用申请",
                "sc.expense.claim",
                claim,
                "smart_construction_core.menu_sc_expense_claim_reimbursement_request",
                ["提交审批", "审批通过", "批准", "完成"],
                "done",
                "payment.ledger",
            ),
        ],
    }
    SETUP_JSON.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print("FINANCE_HANDLING_BROWSER_SETUP: %s" % json.dumps(payload, ensure_ascii=False, sort_keys=True))


main()
