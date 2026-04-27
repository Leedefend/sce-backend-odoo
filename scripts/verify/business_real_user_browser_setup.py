# -*- coding: utf-8 -*-
"""Prepare committed, temporary business records for real-user browser closure."""

import json
from pathlib import Path

from odoo.exceptions import UserError


ARTIFACT_DIR = Path("/mnt/artifacts/browser-real-user-business-closure/current")
PREFIX = "BROWSER-CLOSURE"


def _env():
    return globals()["env"]


def _active_user(group_xmlid, login=None, exclude=False):
    group = _env().ref(group_xmlid)
    users = group.users.filtered(
        lambda user: user.active
        and not user.share
        and user.login != "admin"
        and not str(user.login or "").startswith(("demo", "sc_fx"))
    ).sorted("login")
    if exclude:
        users = users.filtered(lambda user: user.id != exclude.id)
    if login:
        user = users.filtered(lambda item: item.login == login)[:1]
        if user:
            return user[0]
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
                "name": "真实用户浏览器闭环验证",
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
            "name": "%s Project %s" % (PREFIX, code),
            "code": "%s-%s" % (PREFIX, code),
            "company_id": company.id,
            "user_id": submitter.id,
        }
    )
    project.sudo().message_subscribe(partner_ids=[submitter.partner_id.id])
    return project, company


def _create_record(spec, submitter):
    env = _env()
    model_name = spec["model"]
    code = spec["code"]
    project, company = _base_project(submitter, code)
    vals = {
        "project_id": project.id,
        "document_no": "%s-%s" % (PREFIX, code),
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
        vals.update({"amount": 120.0, "item_name": "%s 合同明细调整" % PREFIX})
    else:
        raise UserError("Unsupported browser closure model %s" % model_name)
    record = env[model_name].sudo().create(vals)
    record.project_id.sudo().message_subscribe(partner_ids=[spec["reviewer"].partner_id.id])
    record.with_user(submitter).with_company(company).action_confirm()
    record.invalidate_recordset()
    if record.validation_status not in ("pending", "waiting"):
        raise UserError("%s did not enter approval pending state" % model_name)
    return record, project


def main():
    env = _env()
    submitter = _active_user(
        "smart_construction_core.group_sc_cap_business_initiator",
        login="caisiqi",
    )
    specs = [
        {
            "model": "sc.receipt.income",
            "label": "收款登记",
            "code": "RECEIPT",
            "review_group": "smart_construction_core.group_sc_cap_finance_manager",
            "reviewer_login": "chenshuai",
            "final_state": "confirmed",
        },
        {
            "model": "sc.payment.execution",
            "label": "付款执行",
            "code": "PAYEXEC",
            "review_group": "smart_construction_core.group_sc_cap_finance_manager",
            "reviewer_login": "chenshuai",
            "final_state": "confirmed",
        },
        {
            "model": "sc.invoice.registration",
            "label": "发票登记",
            "code": "INVOICE",
            "review_group": "smart_construction_core.group_sc_cap_finance_manager",
            "reviewer_login": "chenshuai",
            "final_state": "confirmed",
        },
        {
            "model": "sc.financing.loan",
            "label": "融资借款",
            "code": "LOAN",
            "review_group": "smart_construction_core.group_sc_cap_finance_manager",
            "reviewer_login": "chenshuai",
            "final_state": "confirmed",
        },
        {
            "model": "sc.treasury.reconciliation",
            "label": "资金对账",
            "code": "TREASURY",
            "review_group": "smart_construction_core.group_sc_cap_finance_manager",
            "reviewer_login": "chenshuai",
            "final_state": "confirmed",
        },
        {
            "model": "sc.settlement.adjustment",
            "label": "结算调整",
            "code": "ADJUST",
            "review_group": "smart_construction_core.group_sc_cap_settlement_manager",
            "reviewer_login": "wutao",
            "final_state": "confirmed",
        },
    ]
    cases = []
    for spec in specs:
        _ensure_policy(spec["model"], spec["review_group"])
        reviewer = _active_user(spec["review_group"], login=spec["reviewer_login"], exclude=submitter)
        spec["reviewer"] = reviewer
        record, project = _create_record(spec, submitter)
        cases.append(
            {
                "model": spec["model"],
                "label": spec["label"],
                "record_id": record.id,
                "project_id": project.id,
                "title": record.display_name,
                "reviewer_login": reviewer.login,
                "reviewer_name": reviewer.name,
                "reviewer_password": "123456",
                "submitter_login": submitter.login,
                "submitter_name": submitter.name,
                "expected_state": spec["final_state"],
            }
        )

    ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)
    setup = {"prefix": PREFIX, "cases": cases}
    (ARTIFACT_DIR / "setup.json").write_text(json.dumps(setup, ensure_ascii=False, indent=2), encoding="utf-8")
    env.cr.commit()
    print("BUSINESS_REAL_USER_BROWSER_SETUP=PASS")
    print(json.dumps(setup, ensure_ascii=False, indent=2))


main()
