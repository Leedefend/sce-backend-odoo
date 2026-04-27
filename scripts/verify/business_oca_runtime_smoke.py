# -*- coding: utf-8 -*-
"""Rollback-only Odoo shell smoke for business OCA tier runtime flows.

Run with:
  make verify.business.oca_runtime_smoke

This script expects to be executed by ``odoo shell`` and uses the global
``env`` object. It creates temporary records, validates approve/reject flows,
prints machine-readable markers, and rolls back at the end.
"""

import base64
import os

from odoo.exceptions import UserError


EXCLUDE_PREFIXES = ("demo", "sc_fx")
EXCLUDE_LOGINS = {"admin"}


def _env():
    return globals()["env"]


def _active_internal_users(group_xmlid):
    group = _env().ref(group_xmlid)
    return group.users.filtered(
        lambda user: (
            user.active
            and not user.share
            and user.login not in EXCLUDE_LOGINS
            and not str(user.login or "").startswith(EXCLUDE_PREFIXES)
        )
    ).sorted("login")


def _user_from_env(env_name, group_xmlid, *, prefer_login=None, exclude_user=False):
    login = str(os.getenv(env_name) or prefer_login or "").strip()
    users = _active_internal_users(group_xmlid)
    if login:
        user = users.filtered(lambda item: item.login == login)[:1]
        if user:
            return user[0]
    if exclude_user:
        users = users.filtered(lambda item: item.id != exclude_user.id)
    if not users:
        raise UserError("No active real user in %s" % group_xmlid)
    return users[0]


def _create_payment_request(submitter):
    env = _env()
    company = submitter.company_id or env.company
    partner = env["res.partner"].sudo().create({"name": "OCA Runtime Payment Vendor"})
    project = env["project.project"].sudo().create(
        {
            "name": "OCA Runtime Payment Project",
            "code": "OCA-RUNTIME-PAY",
            "funding_enabled": True,
            "company_id": company.id,
            "user_id": submitter.id,
        }
    )
    env["project.funding.baseline"].sudo().create(
        {"project_id": project.id, "total_amount": 10000.0, "state": "active"}
    )
    contract = env["construction.contract"].sudo().create(
        {
            "subject": "OCA Runtime Payment Contract",
            "type": "in",
            "project_id": project.id,
            "partner_id": partner.id,
        }
    )
    request = env["payment.request"].sudo().create(
        {
            "name": "OCA-RUNTIME-PAY",
            "type": "pay",
            "project_id": project.id,
            "partner_id": partner.id,
            "contract_id": contract.id,
            "amount": 100.0,
            "state": "draft",
        }
    )
    env["ir.attachment"].sudo().create(
        {
            "name": "oca-runtime-payment.txt",
            "type": "binary",
            "datas": base64.b64encode(b"oca runtime payment").decode("ascii"),
            "res_model": request._name,
            "res_id": request.id,
            "mimetype": "text/plain",
        }
    )
    return request, project, company


def _submit_payment(submitter):
    env = _env()
    request, project, company = _create_payment_request(submitter)
    project.sudo().message_subscribe(partner_ids=[submitter.partner_id.id])
    request.with_user(submitter).with_company(company).action_submit()
    request.invalidate_recordset()
    reviews = env["tier.review"].sudo().search(
        [("model", "=", "payment.request"), ("res_id", "=", request.id)]
    )
    assert request.state == "submit", request.state
    assert request.validation_status in ("pending", "waiting"), request.validation_status
    assert len(reviews) == 1, len(reviews)
    return request, reviews, company


def _check_payment_flows():
    env = _env()
    submitter = _user_from_env(
        "SC_OCA_PAYMENT_SUBMITTER",
        "smart_construction_core.group_sc_cap_business_initiator",
        prefer_login="caisiqi",
    )
    reviewer = _user_from_env(
        "SC_OCA_PAYMENT_REVIEWER",
        "smart_construction_core.group_sc_cap_finance_manager",
        prefer_login="chenshuai",
        exclude_user=submitter,
    )
    print("PAYMENT_OCA_ACTORS=%s->%s" % (submitter.login, reviewer.login))

    request, reviews, company = _submit_payment(submitter)
    request.project_id.sudo().message_subscribe(partner_ids=[reviewer.partner_id.id])
    print("PAYMENT_APPROVE_BEFORE=%s/%s/%s" % (request.state, request.validation_status, reviews.mapped("status")))
    request.with_user(reviewer).with_company(company).validate_tier()
    request.invalidate_recordset()
    reviews = env["tier.review"].sudo().search(
        [("model", "=", "payment.request"), ("res_id", "=", request.id)]
    )
    print("PAYMENT_APPROVE_AFTER=%s/%s/%s" % (request.state, request.validation_status, reviews.mapped("status")))
    assert request.state == "approved", request.state
    assert request.validation_status == "validated", request.validation_status
    assert reviews and all(status == "approved" for status in reviews.mapped("status"))

    request, reviews, company = _submit_payment(submitter)
    request.project_id.sudo().message_subscribe(partner_ids=[reviewer.partner_id.id])
    print("PAYMENT_REJECT_BEFORE=%s/%s/%s" % (request.state, request.validation_status, reviews.mapped("status")))
    request.with_user(reviewer).with_company(company).reject_tier()
    request.invalidate_recordset()
    reviews = env["tier.review"].sudo().search(
        [("model", "=", "payment.request"), ("res_id", "=", request.id)]
    )
    print("PAYMENT_REJECT_AFTER=%s/%s/%s" % (request.state, request.validation_status, reviews.mapped("status")))
    assert request.state == "rejected", request.state
    assert request.validation_status == "rejected", request.validation_status
    assert reviews and all(status == "rejected" for status in reviews.mapped("status"))


def _create_material_plan(submitter):
    env = _env()
    company = submitter.company_id or env.company
    uom = env.ref("uom.product_uom_unit")
    product = env["product.product"].sudo().create(
        {
            "name": "OCA Runtime Material Product",
            "type": "product",
            "uom_id": uom.id,
            "uom_po_id": uom.id,
        }
    )
    project = env["project.project"].sudo().create(
        {
            "name": "OCA Runtime Material Project",
            "code": "OCA-RUNTIME-MAT",
            "company_id": company.id,
            "user_id": submitter.id,
        }
    )
    plan = env["project.material.plan"].sudo().create(
        {
            "name": "OCA-RUNTIME-MAT",
            "project_id": project.id,
            "line_ids": [
                (
                    0,
                    0,
                    {"product_id": product.id, "quantity": 2.0, "uom_id": uom.id},
                )
            ],
        }
    )
    return plan, project, company


def _submit_material(submitter):
    env = _env()
    plan, project, company = _create_material_plan(submitter)
    project.sudo().message_subscribe(partner_ids=[submitter.partner_id.id])
    plan.with_user(submitter).with_company(company).action_submit()
    plan.invalidate_recordset()
    reviews = env["tier.review"].sudo().search(
        [("model", "=", "project.material.plan"), ("res_id", "=", plan.id)]
    )
    assert plan.state == "submit", plan.state
    assert plan.validation_status in ("pending", "waiting"), plan.validation_status
    assert len(reviews) == 1, len(reviews)
    return plan, reviews, company


def _check_material_flows():
    env = _env()
    submitter = _user_from_env(
        "SC_OCA_MATERIAL_SUBMITTER",
        "smart_construction_core.group_sc_cap_material_user",
        prefer_login="zhaowei",
    )
    reviewer = _user_from_env(
        "SC_OCA_MATERIAL_REVIEWER",
        "smart_construction_core.group_sc_cap_material_manager",
        prefer_login="chenshuai",
        exclude_user=submitter,
    )
    print("MATERIAL_OCA_ACTORS=%s->%s" % (submitter.login, reviewer.login))

    plan, reviews, company = _submit_material(submitter)
    plan.project_id.sudo().message_subscribe(partner_ids=[reviewer.partner_id.id])
    print("MATERIAL_APPROVE_BEFORE=%s/%s/%s" % (plan.state, plan.validation_status, reviews.mapped("status")))
    plan.with_user(reviewer).with_company(company).validate_tier()
    plan.invalidate_recordset()
    reviews = env["tier.review"].sudo().search(
        [("model", "=", "project.material.plan"), ("res_id", "=", plan.id)]
    )
    print("MATERIAL_APPROVE_AFTER=%s/%s/%s" % (plan.state, plan.validation_status, reviews.mapped("status")))
    assert plan.state == "approved", plan.state
    assert plan.validation_status == "validated", plan.validation_status
    assert reviews and all(status == "approved" for status in reviews.mapped("status"))

    plan, reviews, company = _submit_material(submitter)
    plan.project_id.sudo().message_subscribe(partner_ids=[reviewer.partner_id.id])
    print("MATERIAL_REJECT_BEFORE=%s/%s/%s" % (plan.state, plan.validation_status, reviews.mapped("status")))
    plan.with_user(reviewer).with_company(company).reject_tier()
    plan.invalidate_recordset()
    reviews = env["tier.review"].sudo().search(
        [("model", "=", "project.material.plan"), ("res_id", "=", plan.id)]
    )
    print(
        "MATERIAL_REJECT_AFTER=%s/%s/reviews=%s/reason=%s"
        % (plan.state, plan.validation_status, len(reviews), plan.reject_reason)
    )
    assert plan.state == "draft", plan.state
    assert plan.reject_reason, "material reject reason missing"
    assert not reviews, reviews.ids


def main():
    try:
        _check_payment_flows()
        _check_material_flows()
        print("BUSINESS_OCA_RUNTIME_SMOKE=PASS")
    finally:
        _env().cr.rollback()
        print("BUSINESS_OCA_RUNTIME_ROLLBACK=OK")


main()
