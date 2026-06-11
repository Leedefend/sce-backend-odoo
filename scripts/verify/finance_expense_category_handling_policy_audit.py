# -*- coding: utf-8 -*-
"""Audit sc.expense.claim category handling policies.

This gate keeps expense/deposit/deduction/interfund-repayment entry categories
aligned with the current handling model:

* operating cash categories require a payment/receipt request and account fields;
* interfund repayment categories explicitly do not use payment.request;
* all categories keep user-facing action bindings, attachment policy, and
  downstream fact policy.
"""

from __future__ import annotations

import base64
import json
import sys
import traceback
import uuid

from odoo import fields


EXPENSE_CATEGORY_REQUIREMENTS = {
    "finance.expense.reimbursement": {
        "direction": "pay",
        "payment_request_policy": "required",
        "required_fields": [
            "payment_request_id",
            "project_id",
            "partner_id",
            "amount",
            "payee",
            "receipt_account_name",
            "payee_account",
            "payment_account_name",
            "payer_account",
        ],
        "ledger_facts": ["payment.ledger"],
        "terminal_action": "action_done",
    },
    "finance.expense.project": {
        "direction": "pay",
        "payment_request_policy": "required",
        "required_fields": [
            "payment_request_id",
            "project_id",
            "partner_id",
            "amount",
            "payee",
            "receipt_account_name",
            "payee_account",
            "payment_account_name",
            "payer_account",
        ],
        "ledger_facts": ["payment.ledger"],
        "terminal_action": "action_done",
    },
    "finance.deposit.bid.pay": {
        "direction": "pay",
        "payment_request_policy": "required",
        "required_fields": [
            "payment_request_id",
            "project_id",
            "partner_id",
            "amount",
            "payee",
            "receipt_account_name",
            "payee_account",
            "payment_account_name",
            "payer_account",
        ],
        "ledger_facts": ["payment.ledger", "sc.finance.business.fact"],
        "terminal_action": "action_done",
    },
    "finance.deposit.contract.pay": {
        "direction": "pay",
        "payment_request_policy": "required",
        "required_fields": [
            "payment_request_id",
            "project_id",
            "partner_id",
            "amount",
            "payee",
            "receipt_account_name",
            "payee_account",
            "payment_account_name",
            "payer_account",
        ],
        "ledger_facts": ["payment.ledger", "sc.finance.business.fact"],
        "terminal_action": "action_done",
    },
    "finance.deposit.bid.return": {
        "direction": "receive",
        "payment_request_policy": "required",
        "required_fields": [
            "payment_request_id",
            "project_id",
            "partner_id",
            "amount",
            "payment_account_name",
            "payer_account",
        ],
        "ledger_facts": ["sc.treasury.ledger", "sc.finance.business.fact"],
        "terminal_action": "action_done",
    },
    "finance.deposit.contract.return": {
        "direction": "receive",
        "payment_request_policy": "required",
        "required_fields": [
            "payment_request_id",
            "project_id",
            "partner_id",
            "amount",
            "payment_account_name",
            "payer_account",
        ],
        "ledger_facts": ["sc.treasury.ledger", "sc.finance.business.fact"],
        "terminal_action": "action_done",
    },
    "finance.deduction.bill": {
        "direction": "mixed",
        "payment_request_policy": "not_applicable",
        "required_fields": ["project_id", "partner_id", "amount", "expense_type"],
        "ledger_facts": ["sc.finance.business.fact"],
        "terminal_action": "action_done",
        "legacy_cashflow_required": False,
    },
    "finance.deduction.paid": {
        "direction": "pay",
        "payment_request_policy": "required",
        "required_fields": [
            "payment_request_id",
            "project_id",
            "partner_id",
            "amount",
            "expense_type",
            "payee",
            "receipt_account_name",
            "payee_account",
            "payment_account_name",
            "payer_account",
        ],
        "ledger_facts": ["payment.ledger", "sc.finance.business.fact"],
        "terminal_action": "action_done",
    },
    "finance.deduction.refund": {
        "direction": "receive",
        "payment_request_policy": "required",
        "required_fields": [
            "payment_request_id",
            "project_id",
            "partner_id",
            "amount",
            "expense_type",
            "payment_account_name",
            "payer_account",
        ],
        "ledger_facts": ["sc.treasury.ledger", "sc.finance.business.fact"],
        "terminal_action": "action_done",
    },
    "finance.repayment.registration": {
        "direction": "pay",
        "payment_request_policy": "not_applicable",
        "required_fields": ["project_id", "partner_id", "amount", "expense_type"],
        "ledger_facts": ["sc.interfund.movement.fact", "sc.treasury.ledger"],
        "terminal_action": "action_done",
    },
    "finance.repayment.contractor_project": {
        "direction": "receive",
        "payment_request_policy": "not_applicable",
        "required_fields": ["project_id", "partner_id", "amount", "expense_type"],
        "ledger_facts": ["sc.interfund.movement.fact", "sc.treasury.ledger"],
        "terminal_action": "action_done",
    },
    "finance.repayment.project_company": {
        "direction": "pay",
        "payment_request_policy": "not_applicable",
        "required_fields": ["project_id", "partner_id", "amount", "expense_type"],
        "ledger_facts": ["sc.interfund.movement.fact", "sc.treasury.ledger"],
        "terminal_action": "action_done",
    },
}


def _json_loads(raw, default):
    try:
        value = json.loads(raw or "")
    except (TypeError, ValueError):
        return default
    return value if isinstance(value, type(default)) else default


def _ensure_groups():
    user = env.user.sudo()  # noqa: F821
    for xmlid in (
        "smart_construction_core.group_sc_cap_business_initiator",
        "smart_construction_core.group_sc_cap_project_manager",
        "smart_construction_core.group_sc_cap_finance_user",
        "smart_construction_core.group_sc_cap_finance_manager",
    ):
        group = env.ref(xmlid, raise_if_not_found=False)  # noqa: F821
        if group and group.id not in user.groups_id.ids:
            user.write({"groups_id": [(4, group.id)]})
    env.invalidate_all()  # noqa: F821


def _force_validated(record, table_name):
    env.flush_all()  # noqa: F821
    env.cr.execute("UPDATE %s SET validation_status=%%s WHERE id=%%s" % table_name, ("validated", record.id))  # noqa: F821
    record.invalidate_recordset()
    if "validation_status" in record._fields and record.validation_status != "validated":
        record.write({"validation_status": "validated"})
        record.invalidate_recordset()


def _source_linked_ledger_counts():
    env.cr.execute(  # noqa: F821
        """
        SELECT
            COALESCE(category.code, '<empty>') AS category_code,
            COUNT(*)::integer AS claim_count,
            COUNT(ledger.id)::integer AS source_linked_ledger_count,
            COUNT(*) FILTER (WHERE ledger.id IS NULL)::integer AS missing_ledger_count
        FROM sc_expense_claim claim
        LEFT JOIN sc_business_category category ON category.id = claim.business_category_id
        LEFT JOIN sc_treasury_ledger ledger
          ON ledger.source_model = 'sc.expense.claim'
         AND ledger.source_res_id = claim.id
         AND ledger.project_id = claim.project_id
         AND ledger.direction = CASE WHEN claim.direction = 'inflow' THEN 'in' ELSE 'out' END
         AND ledger.source_kind = CASE WHEN claim.direction = 'inflow' THEN 'legacy_receipt' ELSE 'legacy_actual_outflow' END
         AND ledger.state != 'void'
        WHERE claim.source_origin = 'legacy'
          AND claim.state = 'legacy_confirmed'
          AND claim.project_id IS NOT NULL
          AND COALESCE(claim.approved_amount, claim.amount, 0.0) > 0
        GROUP BY COALESCE(category.code, '<empty>')
        ORDER BY category_code
        """
    )
    return env.cr.dictfetchall()  # noqa: F821


def _create_attachment(record):
    attachment = env["ir.attachment"].sudo().create(  # noqa: F821
        {
            "name": "finance-expense-category-policy-proof.txt",
            "datas": base64.b64encode(b"finance expense attachment policy proof").decode("ascii"),
            "res_model": record._name,
            "res_id": record.id,
            "mimetype": "text/plain",
        }
    )
    record.write({"attachment_ids": [(4, attachment.id)]})
    return attachment


def _attachment_policy_runtime_check(failures):
    Project = env["project.project"].sudo()  # noqa: F821
    Partner = env["res.partner"].sudo()  # noqa: F821
    Claim = env["sc.expense.claim"].sudo()  # noqa: F821
    project = Project.create(
        {
            "name": "费用附件策略门禁项目",
            "code": "FIN-EXP-ATTACH-POLICY",
            "company_id": env.company.id,  # noqa: F821
        }
    )
    partner = Partner.create({"name": "费用附件策略门禁往来单位"})
    claim = Claim.create(
        {
            "claim_type": "project_company_repay",
            "expense_type": "还款登记",
            "project_id": project.id,
            "partner_id": partner.id,
            "amount": 18.0,
            "approved_amount": 18.0,
            "paid_amount": 0.0,
            "summary": "附件策略门禁验证",
            "payment_account_name": "附件策略付款账户",
            "payer_account": "FIN-EXP-ATTACH-PAYER",
            "receipt_account_name": "附件策略收款账户",
            "payee_account": "FIN-EXP-ATTACH-RECEIPT",
        }
    )
    runtime = {
        "category_code": claim.business_category_id.code,
        "blocked_without_attachment": False,
        "submitted_after_attachment": False,
        "record_id": claim.id,
    }
    try:
        with env.cr.savepoint():  # noqa: F821
            claim.action_submit()
    except Exception as err:  # noqa: BLE001 - Odoo shell runtime check
        if "附件" not in str(err):
            failures.append("attachment_policy_runtime: expected attachment error, got %s" % err)
        else:
            runtime["blocked_without_attachment"] = True
    else:
        failures.append("attachment_policy_runtime: submit without attachment must fail")

    _create_attachment(claim)
    claim.action_submit()
    if claim.state not in ("submit", "approved"):
        failures.append("attachment_policy_runtime: expected submit/approved after attachment, got %s" % claim.state)
    else:
        runtime["submitted_after_attachment"] = True
        runtime["state_after_attachment"] = claim.state
    return runtime


def _noncash_deduction_runtime_check(failures):
    Project = env["project.project"].sudo()  # noqa: F821
    Partner = env["res.partner"].sudo()  # noqa: F821
    Claim = env["sc.expense.claim"].sudo()  # noqa: F821
    PaymentRequest = env["payment.request"].sudo()  # noqa: F821
    policy = env.ref("smart_construction_core.approval_policy_expense_claim", raise_if_not_found=False)  # noqa: F821
    original_policy_values = {}
    project = Project.create(
        {
            "name": "扣款单非现金门禁项目",
            "code": "FIN-DEDUCTION-NONCASH",
            "company_id": env.company.id,  # noqa: F821
        }
    )
    partner = Partner.create({"name": "扣款单非现金门禁往来单位"})
    runtime = {
        "category_code": False,
        "record_id": False,
        "blocked_with_payment_request": False,
        "done_without_payment_request": False,
        "payment_request_id": False,
        "payment_ledger_count": 0,
        "treasury_ledger_count": 0,
    }
    try:
        if policy:
            policy = policy.sudo()
            original_policy_values = {
                "active": policy.active,
                "approval_required": policy.approval_required,
                "mode": policy.mode,
                "runtime_state": policy.runtime_state,
            }
            policy.write({"active": True, "approval_required": False, "mode": "none", "runtime_state": "tier_validation"})
            policy.sync_tier_definitions()
        request = PaymentRequest.create(
            {
                "name": "扣款单误挂收付款申请门禁",
                "type": "pay",
                "project_id": project.id,
                "partner_id": partner.id,
                "amount": 20.0,
                "currency_id": env.company.currency_id.id,  # noqa: F821
            }
        )
        blocked = Claim.create(
            {
                "claim_type": "expense",
                "expense_type": "扣款单",
                "project_id": project.id,
                "partner_id": partner.id,
                "amount": 20.0,
                "approved_amount": 20.0,
                "summary": "扣款单误挂收付款申请应被拦截",
                "payment_request_id": request.id,
            }
        )
        _create_attachment(blocked)
        try:
            with env.cr.savepoint():  # noqa: F821
                blocked.action_submit()
        except Exception as err:  # noqa: BLE001
            if "不应关联付款/收款申请" in str(err):
                runtime["blocked_with_payment_request"] = True
            else:
                failures.append("noncash_deduction_runtime: expected payment request boundary error, got %s" % err)
        else:
            failures.append("noncash_deduction_runtime: deduction bill with payment_request_id must fail")

        claim = Claim.create(
            {
                "claim_type": "expense",
                "expense_type": "扣款单",
                "project_id": project.id,
                "partner_id": partner.id,
                "amount": 21.0,
                "approved_amount": 21.0,
                "summary": "扣款单非现金办理门禁",
            }
        )
        _create_attachment(claim)
        claim.action_submit()
        claim.invalidate_recordset()
        if claim.state == "submit":
            claim.action_approve()
            claim.invalidate_recordset()
        claim.action_done()
        claim.invalidate_recordset()
        runtime.update(
            {
                "category_code": claim.business_category_id.code,
                "record_id": claim.id,
                "done_without_payment_request": claim.state == "done" and not bool(claim.payment_request_id),
                "payment_request_id": claim.payment_request_id.id,
                "payment_ledger_count": env["payment.ledger"].sudo().search_count([("payment_request_id", "=", request.id)]),  # noqa: F821
                "treasury_ledger_count": env["sc.treasury.ledger"].sudo().search_count(  # noqa: F821
                    [("source_model", "=", claim._name), ("source_res_id", "=", claim.id), ("state", "!=", "void")]
                ),
            }
        )
        if not runtime["done_without_payment_request"]:
            failures.append("noncash_deduction_runtime: expected done without payment_request_id, got %s" % claim.state)
        if runtime["payment_ledger_count"]:
            failures.append("noncash_deduction_runtime: noncash deduction bill must not create payment.ledger")
        if runtime["treasury_ledger_count"]:
            failures.append("noncash_deduction_runtime: noncash deduction bill must not create sc.treasury.ledger")
    finally:
        if policy and original_policy_values:
            policy.write(original_policy_values)
            policy.sync_tier_definitions()
    return runtime


def _approved_payment_request(project, partner, request_type, amount, label):
    vals = {
        "name": label,
        "type": request_type,
        "project_id": project.id,
        "partner_id": partner.id,
        "amount": amount,
        "currency_id": env.company.currency_id.id,  # noqa: F821
    }
    if request_type == "pay":
        contract = _deposit_contract(project, partner, "in", label)
        settlement = _approved_settlement(project, partner, contract, amount, label)
        vals.update({"contract_id": contract.id, "settlement_id": settlement.id})
    request = env["payment.request"].sudo().create(vals)  # noqa: F821
    request.write({"validation_status": "validated"})
    request.with_context(allow_transition=True, payment_soft_gate=True).write({"state": "approved"})
    request.invalidate_recordset()
    return request


def _deposit_contract(project, partner, direction, label):
    tax = env["account.tax"].sudo().create(  # noqa: F821
        {
            "name": "%s税率%s" % (label, uuid.uuid4().hex[:6]),
            "amount": 0.0,
            "amount_type": "percent",
            "type_tax_use": "purchase" if direction == "in" else "sale",
            "price_include": False,
            "company_id": env.company.id,  # noqa: F821
        }
    )
    return env["construction.contract"].sudo().create(  # noqa: F821
        {
            "subject": "%s合同%s" % (label, uuid.uuid4().hex[:6]),
            "type": direction,
            "project_id": project.id,
            "partner_id": partner.id,
            "company_id": env.company.id,  # noqa: F821
            "currency_id": env.company.currency_id.id,  # noqa: F821
            "tax_id": tax.id,
        }
    )


def _approved_settlement(project, partner, contract, amount, label):
    uom = env.ref("uom.product_uom_unit", raise_if_not_found=False) or env["uom.uom"].sudo().search([], limit=1)  # noqa: F821
    product = env["product.product"].sudo().create(  # noqa: F821
        {
            "name": "%s服务%s" % (label, uuid.uuid4().hex[:6]),
            "type": "service",
            "uom_id": uom.id,
            "uom_po_id": uom.id,
        }
    )
    purchase_order = env["purchase.order"].sudo().create(  # noqa: F821
        {
            "partner_id": partner.id,
            "company_id": env.company.id,  # noqa: F821
            "currency_id": env.company.currency_id.id,  # noqa: F821
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
    settlement = env["sc.settlement.order"].sudo().create(  # noqa: F821
        {
            "project_id": project.id,
            "partner_id": partner.id,
            "contract_id": contract.id,
            "settlement_type": "out",
            "purchase_order_ids": [(6, 0, purchase_order.ids)],
            "company_id": env.company.id,  # noqa: F821
            "currency_id": env.company.currency_id.id,  # noqa: F821
            "line_ids": [
                (
                    0,
                    0,
                    {
                        "name": "%s结算行" % label,
                        "contract_id": contract.id,
                        "qty": 1.0,
                        "price_unit": amount,
                    },
                )
            ],
        }
    )
    settlement.action_submit()
    _force_validated(settlement, "sc_settlement_order")
    settlement.action_on_tier_approved()
    settlement.invalidate_recordset()
    return settlement


def _deposit_claim(project, partner, request, claim_type, guarantee_type, amount, label):
    claim = env["sc.expense.claim"].sudo().create(  # noqa: F821
        {
            "claim_type": claim_type,
            "guarantee_type": guarantee_type,
            "expense_type": label,
            "project_id": project.id,
            "partner_id": partner.id,
            "payment_request_id": request.id,
            "amount": amount,
            "approved_amount": amount,
            "paid_amount": 0.0,
            "summary": label,
            "payee": "%s收款人" % label,
            "receipt_account_name": "%s收款账户" % label,
            "payee_account": "%s-PAYEE" % label,
            "payment_account_name": "%s付款账户" % label,
            "payer_account": "%s-PAYER" % label,
        }
    )
    _create_attachment(claim)
    return claim


def _complete_claim(claim):
    claim.action_submit()
    claim.invalidate_recordset()
    if claim.state == "submit":
        claim.action_approve()
        claim.invalidate_recordset()
    claim.action_done()
    claim.invalidate_recordset()


def _deposit_cashflow_runtime_check(failures):
    Project = env["project.project"].sudo()  # noqa: F821
    Partner = env["res.partner"].sudo()  # noqa: F821
    project = Project.create(
        {
            "name": "保证金收付边界门禁项目",
            "code": "FIN-DEPOSIT-CASHFLOW",
            "funding_enabled": True,
            "company_id": env.company.id,  # noqa: F821
        }
    )
    env["project.funding.baseline"].sudo().create(  # noqa: F821
        {
            "project_id": project.id,
            "total_amount": 100000.0,
            "state": "active",
        }
    )
    partner = Partner.create({"name": "保证金收付边界门禁往来单位"})
    policy = env.ref("smart_construction_core.approval_policy_expense_claim", raise_if_not_found=False)  # noqa: F821
    original_policy_values = {}
    runtime = {
        "pay_claim_id": False,
        "pay_request_id": False,
        "pay_request_state": False,
        "payment_ledger_count": 0,
        "return_claim_id": False,
        "return_request_id": False,
        "return_request_state": False,
        "treasury_ledger_count": 0,
        "direction_mismatch_blocked": False,
        "over_refund_blocked": False,
    }
    try:
        if policy:
            policy = policy.sudo()
            original_policy_values = {
                "active": policy.active,
                "approval_required": policy.approval_required,
                "mode": policy.mode,
                "runtime_state": policy.runtime_state,
            }
            policy.write({"active": True, "approval_required": False, "mode": "none", "runtime_state": "tier_validation"})
            policy.sync_tier_definitions()

        pay_request = _approved_payment_request(project, partner, "pay", 31.0, "保证金支付付款申请")
        pay_claim = _deposit_claim(project, partner, pay_request, "deposit_pay", "bid", 31.0, "投标保证金支付")
        _complete_claim(pay_claim)
        pay_request.invalidate_recordset()
        runtime.update(
            {
                "pay_claim_id": pay_claim.id,
                "pay_request_id": pay_request.id,
                "pay_request_state": pay_request.state,
                "payment_ledger_count": env["payment.ledger"].sudo().search_count([("payment_request_id", "=", pay_request.id)]),  # noqa: F821
            }
        )
        if pay_request.state != "done":
            failures.append("deposit_cashflow_runtime: pay request expected done, got %s" % pay_request.state)
        if runtime["payment_ledger_count"] != 1:
            failures.append("deposit_cashflow_runtime: pay request expected one payment.ledger")

        return_request = _approved_payment_request(project, partner, "receive", 30.0, "保证金退回收款申请")
        return_claim = _deposit_claim(project, partner, return_request, "deposit_refund", "bid", 30.0, "投标保证金退回")
        _complete_claim(return_claim)
        return_request.invalidate_recordset()
        runtime.update(
            {
                "return_claim_id": return_claim.id,
                "return_request_id": return_request.id,
                "return_request_state": return_request.state,
                "treasury_ledger_count": env["sc.treasury.ledger"].sudo().search_count([("payment_request_id", "=", return_request.id)]),  # noqa: F821
            }
        )
        if return_request.state != "done":
            failures.append("deposit_cashflow_runtime: return request expected done, got %s" % return_request.state)
        if runtime["treasury_ledger_count"] != 1:
            failures.append("deposit_cashflow_runtime: return request expected one sc.treasury.ledger")

        over_request = _approved_payment_request(project, partner, "receive", 2.0, "保证金超额退回收款申请")
        over_claim = _deposit_claim(project, partner, over_request, "deposit_refund", "bid", 2.0, "投标保证金超额退回")
        try:
            with env.cr.savepoint():  # noqa: F821
                over_claim.action_submit()
        except Exception as err:  # noqa: BLE001
            if "可退余额" in str(err) or "已缴未退余额" in str(err):
                runtime["over_refund_blocked"] = True
            else:
                failures.append("deposit_cashflow_runtime: expected over-refund balance error, got %s" % err)
        else:
            failures.append("deposit_cashflow_runtime: deposit refund over paid balance must fail")

        mismatch_request = _approved_payment_request(project, partner, "receive", 33.0, "保证金支付错配收款申请")
        mismatch_claim = _deposit_claim(project, partner, mismatch_request, "deposit_pay", "bid", 33.0, "保证金支付方向错配")
        try:
            with env.cr.savepoint():  # noqa: F821
                mismatch_claim.action_submit()
        except Exception as err:  # noqa: BLE001
            if "资金方向" in str(err) or "申请类型" in str(err):
                runtime["direction_mismatch_blocked"] = True
            else:
                failures.append("deposit_cashflow_runtime: expected direction mismatch error, got %s" % err)
        else:
            failures.append("deposit_cashflow_runtime: deposit pay with receive request must fail")
    finally:
        if policy and original_policy_values:
            policy.write(original_policy_values)
            policy.sync_tier_definitions()
    return runtime


failures = []
rows = []
ledger_counts = []
attachment_policy_runtime = {}
noncash_deduction_runtime = {}
deposit_cashflow_runtime = {}

try:
    _ensure_groups()
    Category = env["sc.business.category"].sudo()  # noqa: F821
    for code, expected in EXPENSE_CATEGORY_REQUIREMENTS.items():
        category = Category.search([("code", "=", code)], limit=1)
        if not category:
            failures.append("%s: missing business category" % code)
            continue
        required_fields = _json_loads(category.required_fields_json, [])
        ledger_policy = _json_loads(category.ledger_policy_json, {})
        facts = ledger_policy.get("facts") if isinstance(ledger_policy.get("facts"), list) else []
        missing_required = [field for field in expected["required_fields"] if field not in required_fields]
        missing_facts = [fact for fact in expected["ledger_facts"] if fact not in facts]
        if not category.active:
            failures.append("%s: category inactive" % code)
        if category.target_model != "sc.expense.claim":
            failures.append("%s: expected target_model=sc.expense.claim, got %s" % (code, category.target_model))
        if category.direction != expected["direction"]:
            failures.append("%s: expected direction=%s, got %s" % (code, expected["direction"], category.direction))
        if not category.action_xmlid:
            failures.append("%s: missing action_xmlid" % code)
        elif not env.ref(category.action_xmlid, raise_if_not_found=False):  # noqa: F821
            failures.append("%s: action_xmlid not found: %s" % (code, category.action_xmlid))
        if category.attachment_policy != "required":
            failures.append("%s: attachment_policy must be required, got %s" % (code, category.attachment_policy))
        if missing_required:
            failures.append("%s: missing required_fields %s" % (code, ",".join(missing_required)))
        if missing_facts:
            failures.append("%s: missing ledger_policy facts %s" % (code, ",".join(missing_facts)))
        if ledger_policy.get("terminal_action") != expected["terminal_action"]:
            failures.append(
                "%s: expected terminal_action=%s, got %s"
                % (code, expected["terminal_action"], ledger_policy.get("terminal_action"))
            )
        actual_payment_policy = ledger_policy.get("payment_request_policy")
        if expected["payment_request_policy"] == "not_applicable":
            if actual_payment_policy != "not_applicable":
                failures.append("%s: expected payment_request_policy=not_applicable" % code)
            if "payment_request_id" in required_fields:
                failures.append("%s: not_applicable category must not require payment_request_id" % code)
            if "payment.ledger" in facts:
                failures.append("%s: not_applicable category must not write payment.ledger" % code)
        elif "payment_request_id" not in required_fields:
            failures.append("%s: operating cash category must require payment_request_id" % code)
        rows.append(
            {
                "code": code,
                "direction": category.direction,
                "action_xmlid": category.action_xmlid,
                "required_fields": required_fields,
                "attachment_policy": category.attachment_policy,
                "ledger_policy": ledger_policy,
                "missing_required": missing_required,
                "missing_facts": missing_facts,
            }
        )
    ledger_counts = _source_linked_ledger_counts()
    for row in ledger_counts:
        expected = EXPENSE_CATEGORY_REQUIREMENTS.get(row["category_code"])
        if expected and expected.get("legacy_cashflow_required", True) and row["missing_ledger_count"]:
            failures.append(
                "%s: %s legacy expense claims missing source-linked treasury ledger"
                % (row["category_code"], row["missing_ledger_count"])
            )
    attachment_policy_runtime = _attachment_policy_runtime_check(failures)
    noncash_deduction_runtime = _noncash_deduction_runtime_check(failures)
    deposit_cashflow_runtime = _deposit_cashflow_runtime_check(failures)
except Exception as err:
    failures.append("unexpected error: %s" % err)
    failures.append(traceback.format_exc())

result = {
    "audit": "finance_expense_category_handling_policy_audit",
    "status": "PASS" if not failures else "FAIL",
    "category_count": len(EXPENSE_CATEGORY_REQUIREMENTS),
    "rows": rows,
    "legacy_source_linked_ledger_counts": ledger_counts,
    "attachment_policy_runtime": attachment_policy_runtime,
    "noncash_deduction_runtime": noncash_deduction_runtime,
    "deposit_cashflow_runtime": deposit_cashflow_runtime,
    "failures": failures,
    "policy": {
        "operating_cash": "requires payment_request_id and account fields",
        "noncash_deduction": "deduction bills do not use payment.request and must not create cash ledgers",
        "not_applicable": "must keep payment_request_id out of required fields and ledger policy",
        "legacy_cashflow": "legacy confirmed expense claims must have sc.treasury.ledger source_model/source_res_id coverage",
    },
}
print("FINANCE_EXPENSE_CATEGORY_HANDLING_POLICY_AUDIT: %s" % json.dumps(result, ensure_ascii=False, sort_keys=True, default=str))
if failures:
    print("FAILURES:")
    for failure in failures:
        print("- %s" % failure)

sys.exit(0 if not failures else 1)
