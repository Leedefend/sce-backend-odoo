# -*- coding: utf-8 -*-
"""Rollback-only Odoo shell smoke for optional finance document approval flows."""

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
    if not policy.step_ids:
        env["sc.approval.step"].sudo().create(
            {
                "policy_id": policy.id,
                "sequence": 10,
                "name": "运行时闭环审核",
                "approve_group_id": group.id,
            }
        )
    else:
        policy.step_ids.sudo().write({"active": True, "approve_group_id": group.id})
    policy.sync_tier_definitions()
    return policy


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


def _create_record(model_name, submitter, code):
    env = _env()
    project, company = _base_project(submitter, code)
    vals = {
        "project_id": project.id,
        "document_no": "FD-TIER-%s" % code,
    }
    if model_name == "sc.receipt.income":
        vals.update({"amount": 120.0})
    elif model_name == "sc.payment.execution":
        vals.update({"paid_amount": 120.0, "planned_amount": 120.0})
    elif model_name == "sc.invoice.registration":
        vals.update({"amount_no_tax": 100.0, "tax_amount": 20.0, "amount_total": 120.0})
    elif model_name == "sc.financing.loan":
        vals.update({"amount": 120.0})
    elif model_name == "sc.treasury.reconciliation":
        vals.update({"confirmation_amount": 120.0})
    elif model_name == "sc.settlement.adjustment":
        vals.pop("document_no", None)
        vals.update({"amount": 120.0, "item_name": "运行时闭环调整"})
    else:
        raise UserError("Unsupported model %s" % model_name)
    record = env[model_name].sudo().create(vals)
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
    assert len(reviews) == 1, len(reviews)
    assert record.state == "draft", record.state
    _assert_final_blocked(record, submitter, spec.get("final_method"))

    record.with_user(reviewer).with_company(company).validate_tier()
    record.invalidate_recordset()
    reviews = _reviews(record)
    print("FIN_DOC_TIER_APPROVED=%s/%s/%s/%s" % (spec["model"], record.state, record.validation_status, reviews.mapped("status")))
    assert record.validation_status == "validated", record.validation_status
    assert reviews and all(status == "approved" for status in reviews.mapped("status"))
    if spec.get("final_method"):
        getattr(record.with_user(submitter).with_company(company), spec["final_method"])()
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
        },
        {
            "model": "sc.payment.execution",
            "code": "PAYEXEC",
            "review_group": "smart_construction_core.group_sc_cap_finance_manager",
            "reviewer_login": "chenshuai",
            "final_method": "action_paid",
            "final_state": "paid",
        },
        {
            "model": "sc.invoice.registration",
            "code": "INVOICE",
            "review_group": "smart_construction_core.group_sc_cap_finance_manager",
            "reviewer_login": "chenshuai",
            "final_method": "action_register",
            "final_state": "registered",
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
    ]
    try:
        for spec in specs:
            _check_model(spec, submitter)
        print("BUSINESS_FINANCE_DOCUMENT_TIER_RUNTIME_SMOKE=PASS")
    finally:
        _env().cr.rollback()
        print("BUSINESS_FINANCE_DOCUMENT_TIER_RUNTIME_ROLLBACK=OK")


main()
