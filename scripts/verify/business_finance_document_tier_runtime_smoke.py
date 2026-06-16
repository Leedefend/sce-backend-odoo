# -*- coding: utf-8 -*-
"""Rollback-only Odoo shell smoke for optional finance document approval flows."""

from base64 import b64encode

from odoo import fields
from odoo.exceptions import UserError


def _env():
    return globals()["env"]


def _active_user(group_xmlid, prefer_login=None, exclude=False):
    group = _env().ref(group_xmlid)
    users = group.users.filtered(
        lambda user: user.active
        and not user.share
        and user.login != "admin"
        and not str(user.login or "").startswith(("demo", "sc_fx"))
    ).sorted("login")
    if exclude:
        users = users.filtered(lambda user: user.id != exclude.id)
    if prefer_login:
        preferred = users.filtered(lambda user: user.login == prefer_login)[:1]
        if preferred:
            return preferred[0]
    if not users:
        raise UserError("No active real user in %s" % group_xmlid)
    return users[0]


def _ensure_policy(model_name, group_xmlid):
    env = _env()
    group = env.ref(group_xmlid)
    policy = env["sc.approval.policy"].sudo().search([("target_model", "=", model_name)], limit=1)
    if not policy:
        raise UserError("Missing approval policy for %s" % model_name)
    policy.write(
        {
            "active": True,
            "approval_required": True,
            "mode": "single",
            "runtime_state": "tier_validation",
            "manager_group_id": group.id,
        }
    )
    active_steps = policy.step_ids.sudo().sorted("sequence")
    if not active_steps:
        env["sc.approval.step"].sudo().create(
            {
                "policy_id": policy.id,
                "sequence": 10,
                "name": "运行时闭环审核",
                "approve_group_id": group.id,
            }
        )
    else:
        active_steps[0].sudo().write({"active": True, "approve_group_id": group.id, "sequence": 10})
        (active_steps - active_steps[0]).sudo().write({"active": False})
    policy.sync_tier_definitions()
    return policy


def _set_validated(record):
    env = _env()
    env.flush_all()
    env.cr.execute(
        "UPDATE %s SET validation_status=%%s WHERE id=%%s" % record._table,
        ("validated", record.id),
    )
    env.invalidate_all()
    record.invalidate_recordset()
    if record.validation_status != "validated":
        record.sudo().with_context(skip_validation_check=True).write({"validation_status": "validated"})
        env.flush_all()
        env.invalidate_all()
        record.invalidate_recordset()


def _base_project(submitter, code):
    env = _env()
    company = submitter.company_id or env.company
    project = env["project.project"].sudo().create(
        {
            "name": "Finance Document Tier Runtime %s" % code,
            "code": "FD-TIER-%s" % code,
            "company_id": company.id,
            "user_id": submitter.id,
        }
    )
    project.sudo().message_subscribe(partner_ids=[submitter.partner_id.id])
    return project, company


def _attach(record, name):
    attachment = _env()["ir.attachment"].sudo().create(
        {
            "name": name,
            "type": "binary",
            "datas": b64encode(b"finance-document-tier-runtime-evidence").decode("ascii"),
            "res_model": record._name,
            "res_id": record.id,
            "mimetype": "text/plain",
        }
    )
    if "attachment_ids" in record._fields:
        record.sudo().write({"attachment_ids": [(4, attachment.id)]})
    return attachment


def _tax(company, code):
    Tax = _env()["account.tax"].sudo()
    tax = Tax.search(
        [
            ("company_id", "=", company.id),
            ("type_tax_use", "in", ["sale", "all"]),
            ("amount_type", "=", "percent"),
            ("amount", "=", 0.0),
            ("price_include", "=", False),
        ],
        limit=1,
    )
    if tax:
        return tax
    return Tax.create(
        {
            "name": "FD Tier Sale Tax %s" % code,
            "amount_type": "percent",
            "amount": 0.0,
            "type_tax_use": "sale",
            "price_include": False,
            "company_id": company.id,
        }
    )


def _uom_product(code):
    env = _env()
    uom = env.ref("uom.product_uom_unit", raise_if_not_found=False) or env["uom.uom"].sudo().search([], limit=1)
    product = env["product.product"].sudo().create(
        {
            "name": "FD Tier Service %s" % code,
            "type": "service",
            "uom_id": uom.id,
            "uom_po_id": uom.id,
        }
    )
    return uom, product


def _purchase_order(partner, company, amount, code):
    env = _env()
    uom, product = _uom_product(code)
    po = env["purchase.order"].sudo().create(
        {
            "partner_id": partner.id,
            "company_id": company.id,
            "currency_id": company.currency_id.id,
            "order_line": [
                (
                    0,
                    0,
                    {
                        "name": "FD Tier PO Line",
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
    env.flush_all()
    env.cr.execute("UPDATE purchase_order SET state=%s WHERE id=%s", ("purchase", po.id))
    env.invalidate_all()
    po.invalidate_recordset()
    return po


def _prepare_approved_receipt_request(project, company, partner, code):
    env = _env()
    contract = env["construction.contract"].sudo().create(
        {
            "subject": "FD Tier Income Contract %s" % code,
            "type": "out",
            "project_id": project.id,
            "partner_id": partner.id,
            "company_id": company.id,
            "currency_id": company.currency_id.id,
            "tax_id": _tax(company, code).id,
        }
    )
    env["construction.contract.line"].sudo().create(
        {
            "contract_id": contract.id,
            "qty_contract": 1.0,
            "price_contract": 120.0,
        }
    )
    request = env["payment.request"].sudo().create(
        {
            "project_id": project.id,
            "partner_id": partner.id,
            "contract_id": contract.id,
            "currency_id": company.currency_id.id,
            "amount": 120.0,
            "type": "receive",
            "receipt_type": "审批运行收款申请",
        }
    )
    _attach(request, "receipt-request-tier-%s.txt" % code)
    request.action_submit()
    _set_validated(request)
    request.action_on_tier_approved()
    request.invalidate_recordset()
    if request.state != "approved":
        raise UserError("Receipt request did not reach approved state: %s" % request.state)
    return request, contract


def _prepare_approved_payment_request(project, company, partner, code):
    env = _env()
    contract = env["construction.contract"].sudo().create(
        {
            "subject": "FD Tier Pay Contract %s" % code,
            "type": "in",
            "project_id": project.id,
            "partner_id": partner.id,
            "company_id": company.id,
            "currency_id": company.currency_id.id,
            "tax_id": _tax(company, code).id,
        }
    )
    env["construction.contract.line"].sudo().create(
        {
            "contract_id": contract.id,
            "qty_contract": 1.0,
            "price_contract": 120.0,
        }
    )
    po = _purchase_order(partner, company, 120.0, code)
    settlement = env["sc.settlement.order"].sudo().create(
        {
            "project_id": project.id,
            "partner_id": partner.id,
            "contract_id": contract.id,
            "company_id": company.id,
            "currency_id": company.currency_id.id,
            "purchase_order_ids": [(6, 0, [po.id])],
        }
    )
    env["sc.settlement.order.line"].sudo().create(
        {
            "settlement_id": settlement.id,
            "contract_id": contract.id,
            "name": "FD Tier Settlement Line",
            "qty": 1.0,
            "price_unit": 120.0,
        }
    )
    settlement.action_submit()
    _set_validated(settlement)
    settlement.action_on_tier_approved()
    settlement.invalidate_recordset()
    if settlement.state != "approve":
        raise UserError("Settlement did not reach approve state: %s" % settlement.state)
    request = env["payment.request"].sudo().create(
        {
            "project_id": project.id,
            "partner_id": partner.id,
            "contract_id": contract.id,
            "settlement_id": settlement.id,
            "currency_id": company.currency_id.id,
            "amount": 120.0,
            "type": "pay",
            "actual_payee_unit": "审批运行收款单位",
            "payment_account_name": "审批运行收款账户",
            "payment_account_no": "FD-TIER-PAYEE-%s" % code,
        }
    )
    _attach(request, "payment-request-tier-%s.txt" % code)
    request.action_submit()
    _set_validated(request)
    request.action_on_tier_approved()
    request.invalidate_recordset()
    if request.state != "approved":
        raise UserError("Payment request did not reach approved state: %s" % request.state)
    return request, contract


def _create_record(model_name, submitter, code):
    env = _env()
    project, company = _base_project(submitter, code)
    partner = env["res.partner"].sudo().search([("name", "!=", False), ("is_company", "=", False)], limit=1)
    if not partner:
        partner = submitter.partner_id
    vals = {
        "project_id": project.id,
        "document_no": "FD-TIER-%s" % code,
    }
    if model_name == "sc.receipt.income":
        request, contract = _prepare_approved_receipt_request(project, company, partner, code)
        vals.update(
            {
                "amount": 120.0,
                "partner_id": partner.id,
                "contract_id": contract.id,
                "payment_request_id": request.id,
                "date_receipt": fields.Date.context_today(submitter),
                "receipt_type": "审批运行收款登记",
                "income_category": "审批运行收款登记",
                "receiving_account_name": "审批运行收款账户",
                "receiving_account_no": "FD-TIER-RECEIPT-%s" % code,
            }
        )
    elif model_name == "sc.payment.execution":
        request, contract = _prepare_approved_payment_request(project, company, partner, code)
        vals.update(
            {
                "payment_request_id": request.id,
                "partner_id": partner.id,
                "contract_id": contract.id,
                "paid_amount": 120.0,
                "planned_amount": 120.0,
                "payment_account_name": "审批运行付款账户",
                "payment_account_no": "FD-TIER-PAYER-%s" % code,
                "receipt_account_name": "审批运行收款账户",
                "receipt_account_no": "FD-TIER-PAYEE-%s" % code,
            }
        )
    elif model_name == "sc.invoice.registration":
        contract = env["construction.contract"].sudo().create(
            {
                "subject": "FD Tier Invoice Contract %s" % code,
                "type": "out",
                "project_id": project.id,
                "partner_id": partner.id,
                "company_id": company.id,
                "currency_id": company.currency_id.id,
                "tax_id": _tax(company, code).id,
            }
        )
        env["construction.contract.line"].sudo().create(
            {
                "contract_id": contract.id,
                "qty_contract": 1.0,
                "price_contract": 120.0,
            }
        )
        vals.update(
            {
                "partner_id": partner.id,
                "contract_id": contract.id,
                "invoice_date": fields.Date.context_today(submitter),
                "invoice_no": "FD-TIER-INV-%s" % code,
                "amount_no_tax": 100.0,
                "tax_amount": 20.0,
                "amount_total": 120.0,
            }
        )
    elif model_name == "sc.financing.loan":
        vals.update({"partner_id": partner.id, "amount": 120.0, "purpose": "审批运行融资借款"})
    elif model_name == "sc.treasury.reconciliation":
        ledger = env["sc.treasury.ledger"].sudo().with_context(allow_ledger_auto=True).create(
            {
                "date": fields.Date.context_today(submitter),
                "project_id": project.id,
                "partner_id": partner.id,
                "direction": "in",
                "amount": 120.0,
                "currency_id": company.currency_id.id,
                "source_kind": "runtime",
                "source_model": "sc.treasury.reconciliation",
                "source_res_id": 0,
                "state": "posted",
                "note": "审批运行资金对账台账",
            }
        )
        vals.update(
            {
                "treasury_ledger_id": ledger.id,
                "account_name": "审批运行资金账户",
                "bank_account_no": "FD-TIER-BANK-%s" % code,
                "confirmation_amount": 120.0,
                "account_balance": 120.0,
                "bank_balance": 120.0,
                "system_difference": 0.0,
            }
        )
    elif model_name == "sc.settlement.adjustment":
        contract = env["construction.contract"].sudo().create(
            {
                "subject": "FD Tier Adjustment Contract %s" % code,
                "type": "in",
                "project_id": project.id,
                "partner_id": partner.id,
                "company_id": company.id,
                "currency_id": company.currency_id.id,
                "tax_id": _tax(company, code).id,
            }
        )
        env["construction.contract.line"].sudo().create(
            {
                "contract_id": contract.id,
                "qty_contract": 1.0,
                "price_contract": 120.0,
            }
        )
        vals.pop("document_no", None)
        vals.update(
            {
                "contract_id": contract.id,
                "partner_id": partner.id,
                "amount": 120.0,
                "item_name": "运行时闭环调整",
            }
        )
    elif model_name == "sc.self.funding.registration":
        vals.update(
            {
                "funding_type": "income",
                "partner_id": partner.id,
                "amount": 120.0,
                "payment_account_name": "审批运行公司账户",
                "partner_account_name": "审批运行承包人账户",
                "summary": "审批运行自筹垫付",
            }
        )
    else:
        raise UserError("Unsupported model %s" % model_name)
    record = env[model_name].sudo().create(vals)
    if model_name == "sc.self.funding.registration":
        _attach(record, "self-funding-tier-%s.txt" % code)
    return record, company


def _reviews(record):
    return _env()["tier.review"].sudo().search([("model", "=", record._name), ("res_id", "=", record.id)])


def _assert_final_blocked(record, submitter, final_method):
    if not final_method:
        return
    try:
        getattr(record.with_user(submitter), final_method)()
    except UserError:
        return
    raise AssertionError("%s.%s should require validated approval" % (record._name, final_method))


def _check_model(spec, submitter):
    _ensure_policy(spec["model"], spec["review_group"])
    reviewer = _active_user(spec["review_group"], prefer_login=spec.get("reviewer_login"), exclude=submitter)
    print("FIN_DOC_TIER_ACTORS=%s:%s->%s" % (spec["model"], submitter.login, reviewer.login))

    record, company = _create_record(spec["model"], submitter, spec["code"])
    record.project_id.sudo().message_subscribe(partner_ids=[reviewer.partner_id.id])
    record.with_user(submitter).with_company(company).action_confirm()
    record.invalidate_recordset()
    reviews = _reviews(record)
    print("FIN_DOC_TIER_SUBMITTED=%s/%s/%s/%s" % (spec["model"], record.state, record.validation_status, reviews.mapped("status")))
    assert record.validation_status in ("pending", "waiting"), record.validation_status
    assert len(reviews) >= 1, len(reviews)
    assert all(status in ("waiting", "pending") for status in reviews.mapped("status")), reviews.mapped("status")
    assert record.state == "draft", record.state
    _assert_final_blocked(record, submitter, spec.get("final_method"))

    record.with_user(reviewer).with_company(company).validate_tier()
    record.invalidate_recordset()
    reviews = _reviews(record)
    print("FIN_DOC_TIER_APPROVED=%s/%s/%s/%s" % (spec["model"], record.state, record.validation_status, reviews.mapped("status")))
    assert record.validation_status == "validated", record.validation_status
    assert reviews and all(status == "approved" for status in reviews.mapped("status"))
    if spec.get("final_method"):
        final_actor = reviewer if spec.get("final_as_reviewer") else submitter
        getattr(record.with_user(final_actor).with_company(company), spec["final_method"])()
        record.invalidate_recordset()
        assert record.state == spec["final_state"], record.state
    else:
        assert record.state == spec["final_state"], record.state

    record, company = _create_record(spec["model"], submitter, spec["code"] + "-R")
    record.project_id.sudo().message_subscribe(partner_ids=[reviewer.partner_id.id])
    record.with_user(submitter).with_company(company).action_confirm()
    record.with_user(reviewer).with_company(company).reject_tier()
    record.invalidate_recordset()
    reviews = _reviews(record)
    print("FIN_DOC_TIER_REJECTED=%s/%s/%s/%s" % (spec["model"], record.state, record.validation_status, reviews.mapped("status")))
    assert record.validation_status == "rejected", record.validation_status
    assert reviews and all(status == "rejected" for status in reviews.mapped("status"))


def main():
    submitter = _active_user(
        "smart_construction_core.group_sc_cap_business_initiator",
        prefer_login="caisiqi",
    )
    specs = [
        {
            "model": "sc.receipt.income",
            "code": "RECEIPT",
            "review_group": "smart_construction_core.group_sc_cap_finance_manager",
            "reviewer_login": "chenshuai",
            "final_method": "action_received",
            "final_state": "received",
            "final_as_reviewer": True,
        },
        {
            "model": "sc.payment.execution",
            "code": "PAYEXEC",
            "review_group": "smart_construction_core.group_sc_cap_finance_manager",
            "reviewer_login": "chenshuai",
            "final_method": "action_paid",
            "final_state": "paid",
            "final_as_reviewer": True,
        },
        {
            "model": "sc.invoice.registration",
            "code": "INVOICE",
            "review_group": "smart_construction_core.group_sc_cap_finance_manager",
            "reviewer_login": "chenshuai",
            "final_method": "action_register",
            "final_state": "registered",
            "final_as_reviewer": True,
        },
        {
            "model": "sc.financing.loan",
            "code": "LOAN",
            "review_group": "smart_construction_core.group_sc_cap_finance_manager",
            "reviewer_login": "chenshuai",
            "final_method": "action_done",
            "final_state": "done",
        },
        {
            "model": "sc.treasury.reconciliation",
            "code": "TREASURY",
            "review_group": "smart_construction_core.group_sc_cap_finance_manager",
            "reviewer_login": "chenshuai",
            "final_method": "action_reconcile",
            "final_state": "reconciled",
        },
        {
            "model": "sc.settlement.adjustment",
            "code": "ADJUST",
            "review_group": "smart_construction_core.group_sc_cap_settlement_manager",
            "reviewer_login": "wutao",
            "final_state": "confirmed",
        },
        {
            "model": "sc.self.funding.registration",
            "code": "SELFUND",
            "review_group": "smart_construction_core.group_sc_cap_finance_manager",
            "reviewer_login": "chenshuai",
            "final_method": "action_done",
            "final_state": "done",
        },
    ]
    try:
        for spec in specs:
            _check_model(spec, submitter)
        print("BUSINESS_FINANCE_DOCUMENT_TIER_RUNTIME_SMOKE=PASS")
    finally:
        _env().cr.rollback()
        print("BUSINESS_FINANCE_DOCUMENT_TIER_RUNTIME_ROLLBACK=OK")


main()
