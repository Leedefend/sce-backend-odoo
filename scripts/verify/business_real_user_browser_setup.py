# -*- coding: utf-8 -*-
"""Prepare committed, temporary business records for real-user browser closure."""

import json
import base64
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
    vals = {
        "name": "%s Project %s" % (PREFIX, code),
        "code": "%s-%s" % (PREFIX, code),
        "company_id": company.id,
        "user_id": submitter.id,
    }
    if "funding_enabled" in env["project.project"]._fields:
        vals["funding_enabled"] = True
    project = env["project.project"].sudo().create(vals)
    project.sudo().message_subscribe(partner_ids=[submitter.partner_id.id])
    return project, company


def _partner(name):
    return _env()["res.partner"].sudo().create({"name": "%s %s" % (PREFIX, name)})


def _product(name):
    env = _env()
    uom = env.ref("uom.product_uom_unit")
    return env["product.product"].sudo().create(
        {
            "name": "%s %s" % (PREFIX, name),
            "type": "product",
            "uom_id": uom.id,
            "uom_po_id": uom.id,
        }
    )


def _contract(project, partner, code, contract_type="in"):
    return _env()["construction.contract"].sudo().create(
        {
            "subject": "%s Contract %s" % (PREFIX, code),
            "type": contract_type,
            "project_id": project.id,
            "partner_id": partner.id,
        }
    )


def _create_record(spec, submitter):
    env = _env()
    model_name = spec["model"]
    code = spec["code"]
    project, company = _base_project(submitter, code)
    cleanup = []
    vals = {
        "project_id": project.id,
        "document_no": "%s-%s" % (PREFIX, code),
    }
    if model_name == "payment.request":
        partner = _partner("Payment Vendor")
        contract = _contract(project, partner, code)
        baseline = env["project.funding.baseline"].sudo().create(
            {"project_id": project.id, "total_amount": 10000.0, "state": "active"}
        )
        record = env[model_name].sudo().create(
            {
                "name": "%s-%s" % (PREFIX, code),
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
                "name": "%s-payment.txt" % PREFIX,
                "type": "binary",
                "datas": base64.b64encode(b"browser payment").decode("ascii"),
                "res_model": record._name,
                "res_id": record.id,
                "mimetype": "text/plain",
            }
        )
        cleanup = [
            ("project.funding.baseline", baseline.id),
            ("construction.contract", contract.id),
            ("res.partner", partner.id),
        ]
    elif model_name == "project.material.plan":
        product = _product("Material Product")
        uom = env.ref("uom.product_uom_unit")
        record = env[model_name].sudo().create(
            {
                "name": "%s-%s" % (PREFIX, code),
                "project_id": project.id,
                "line_ids": [(0, 0, {"product_id": product.id, "quantity": 2.0, "uom_id": uom.id})],
            }
        )
        cleanup = [("product.product", product.id)]
    elif model_name == "sc.expense.claim":
        record = env[model_name].sudo().create(
            {
                "project_id": project.id,
                "amount": 100.0,
                "summary": "%s expense claim" % PREFIX,
            }
        )
    elif model_name == "sc.settlement.order":
        partner = _partner("Settlement Partner")
        contract = _contract(project, partner, code)
        product = _product("Settlement Product")
        uom = env.ref("uom.product_uom_unit")
        purchase = env["purchase.order"].sudo().create(
            {
                "partner_id": partner.id,
                "project_id": project.id,
                "state": "purchase",
                "order_line": [
                    (
                        0,
                        0,
                        {
                            "name": "%s settlement item" % PREFIX,
                            "product_id": product.id,
                            "product_qty": 1.0,
                            "product_uom": uom.id,
                            "price_unit": 100.0,
                        },
                    )
                ],
            }
        )
        record = env[model_name].sudo().create(
            {
                "project_id": project.id,
                "partner_id": partner.id,
                "contract_id": contract.id,
                "purchase_order_ids": [(6, 0, [purchase.id])],
                "line_ids": [
                    (
                        0,
                        0,
                        {
                            "name": "%s settlement line" % PREFIX,
                            "contract_id": contract.id,
                            "qty": 1.0,
                            "price_unit": 100.0,
                        },
                    )
                ],
            }
        )
        cleanup = [
            ("purchase.order", purchase.id),
            ("construction.contract", contract.id),
            ("product.product", product.id),
            ("res.partner", partner.id),
        ]
    elif model_name == "purchase.order":
        partner = _partner("Purchase Vendor")
        product = _product("Purchase Product")
        uom = env.ref("uom.product_uom_unit")
        record = env[model_name].sudo().create(
            {
                "partner_id": partner.id,
                "project_id": project.id,
                "order_line": [
                    (
                        0,
                        0,
                        {
                            "name": "%s purchase item" % PREFIX,
                            "product_id": product.id,
                            "product_qty": 1.0,
                            "product_uom": uom.id,
                            "price_unit": 100.0,
                        },
                    )
                ],
            }
        )
        cleanup = [("product.product", product.id), ("res.partner", partner.id)]
    elif model_name == "sc.receipt.income":
        vals.update({"amount": 120.0})
        record = env[model_name].sudo().create(vals)
    elif model_name == "sc.payment.execution":
        vals.update({"paid_amount": 120.0, "planned_amount": 120.0})
        record = env[model_name].sudo().create(vals)
    elif model_name == "sc.invoice.registration":
        vals.update({"amount_no_tax": 100.0, "tax_amount": 20.0, "amount_total": 120.0})
        record = env[model_name].sudo().create(vals)
    elif model_name == "sc.financing.loan":
        vals.update({"amount": 120.0})
        record = env[model_name].sudo().create(vals)
    elif model_name == "sc.treasury.reconciliation":
        vals.update({"confirmation_amount": 120.0})
        record = env[model_name].sudo().create(vals)
    elif model_name == "sc.settlement.adjustment":
        vals.pop("document_no", None)
        vals.update({"amount": 120.0, "item_name": "%s 合同明细调整" % PREFIX})
        record = env[model_name].sudo().create(vals)
    else:
        raise UserError("Unsupported browser closure model %s" % model_name)
    record.project_id.sudo().message_subscribe(partner_ids=[spec["reviewer"].partner_id.id])
    submit_method = spec.get("submit_method") or "action_confirm"
    getattr(record.with_user(submitter).with_company(company), submit_method)()
    record.invalidate_recordset()
    if record.validation_status not in ("pending", "waiting"):
        raise UserError("%s did not enter approval pending state" % model_name)
    return record, project, cleanup


def main():
    env = _env()
    submitter = _active_user(
        "smart_construction_core.group_sc_cap_business_initiator",
        login="caisiqi",
    )
    specs = [
        {
            "model": "payment.request",
            "label": "付款申请",
            "code": "PAYREQ",
            "review_group": "smart_construction_core.group_sc_cap_finance_manager",
            "reviewer_login": "chenshuai",
            "submit_method": "action_submit",
            "final_state": "approved",
            "reject_state": "rejected",
            "reject_validation": "rejected",
            "reject_review": "rejected",
        },
        {
            "model": "sc.expense.claim",
            "label": "费用/保证金",
            "code": "EXPENSE",
            "review_group": "smart_construction_core.group_sc_cap_finance_manager",
            "reviewer_login": "chenshuai",
            "submit_method": "action_submit",
            "final_state": "approved",
            "reject_state": "draft",
            "reject_validation": "no",
            "reject_review": "none",
        },
        {
            "model": "project.material.plan",
            "label": "物资计划",
            "code": "MATERIAL",
            "review_group": "smart_construction_core.group_sc_cap_material_manager",
            "reviewer_login": "chenshuai",
            "submitter_group": "smart_construction_core.group_sc_cap_material_user",
            "submitter_login": "zhaowei",
            "submit_method": "action_submit",
            "final_state": "approved",
            "reject_state": "draft",
            "reject_validation": "no",
            "reject_review": "none",
        },
        {
            "model": "sc.settlement.order",
            "label": "结算单",
            "code": "SETTLE",
            "review_group": "smart_construction_core.group_sc_cap_settlement_manager",
            "reviewer_login": "chenshuai",
            "submit_method": "action_submit",
            "final_state": "approve",
            "reject_state": "draft",
            "reject_validation": "no",
            "reject_review": "none",
        },
        {
            "model": "purchase.order",
            "label": "采购单",
            "code": "PURCHASE",
            "review_group": "smart_construction_core.group_sc_cap_purchase_manager",
            "reviewer_login": "chenshuai",
            "submit_method": "button_confirm",
            "final_state": "purchase",
            "approve_state_in": ["purchase", "done"],
            "reject_state_in": ["draft", "sent"],
            "reject_validation": "rejected",
            "reject_review": "rejected",
        },
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
        submitter_for_spec = submitter
        if spec.get("submitter_group"):
            submitter_for_spec = _active_user(spec["submitter_group"], login=spec.get("submitter_login"))
        reviewer = _active_user(spec["review_group"], login=spec["reviewer_login"], exclude=submitter_for_spec)
        spec["reviewer"] = reviewer
        record, project, cleanup = _create_record(spec, submitter_for_spec)
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
                "submitter_login": submitter_for_spec.login,
                "submitter_name": submitter_for_spec.name,
                "expected_state": spec["final_state"],
                "expected_state_in": spec.get("approve_state_in") or [],
                "reject_state": spec.get("reject_state", "draft"),
                "reject_state_in": spec.get("reject_state_in") or [],
                "reject_validation": spec.get("reject_validation", "rejected"),
                "reject_review": spec.get("reject_review", "rejected"),
                "cleanup": [{"model": model, "id": rec_id} for model, rec_id in cleanup],
            }
        )

    ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)
    setup = {"prefix": PREFIX, "cases": cases}
    (ARTIFACT_DIR / "setup.json").write_text(json.dumps(setup, ensure_ascii=False, indent=2), encoding="utf-8")
    env.cr.commit()
    print("BUSINESS_REAL_USER_BROWSER_SETUP=PASS")
    print(json.dumps(setup, ensure_ascii=False, indent=2))


main()
