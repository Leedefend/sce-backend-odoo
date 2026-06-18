# -*- coding: utf-8 -*-
"""Rollback-only smoke for low-code approval policy runtime consumption.

This intentionally uses one current-contract-valid business document. Broad
multi-document approval regressions stay in the dedicated finance/document
approval smoke targets.
"""

from base64 import b64encode


def _env():
    return globals()["env"]


def _policy(model_name):
    policy = _env()["sc.approval.policy"].sudo().search([("target_model", "=", model_name)], limit=1)
    if not policy:
        raise AssertionError("missing approval policy for %s" % model_name)
    return policy


def _set_policy(model_name, enabled):
    policy = _policy(model_name)
    policy.write(
        {
            "active": True,
            "approval_required": bool(enabled),
            "mode": "single" if enabled else "none",
            "runtime_state": "tier_validation",
        }
    )
    policy.sync_tier_definitions()
    return policy


def _project(name):
    return _env()["project.project"].sudo().create({"name": name, "code": name.upper().replace(" ", "-")[:32]})


def _partner(name):
    return _env()["res.partner"].sudo().create({"name": name})


def _attach(record, label):
    attachment = _env()["ir.attachment"].sudo().create(
        {
            "name": "%s.txt" % label,
            "datas": b64encode(("business-config-approval-runtime:%s" % label).encode("utf-8")).decode("ascii"),
            "res_model": record._name,
            "res_id": record.id,
            "mimetype": "text/plain",
        }
    )
    if "attachment_ids" in record._fields:
        record.write({"attachment_ids": [(4, attachment.id)]})
    return attachment


def _expense(project, partner, suffix):
    claim = _env()["sc.expense.claim"].sudo().create(
        {
            "claim_type": "project_company_repay",
            "expense_type": "还款登记",
            "project_id": project.id,
            "partner_id": partner.id,
            "amount": 100.0,
            "approved_amount": 100.0,
            "paid_amount": 0.0,
            "summary": "Business config approval runtime smoke %s" % suffix,
            "payment_account_name": "Business config smoke payer",
            "payer_account": "BUSINESS-CONFIG-SMOKE-PAYER-%s" % suffix,
            "receipt_account_name": "Business config smoke receiver",
            "payee_account": "BUSINESS-CONFIG-SMOKE-RECEIVER-%s" % suffix,
        }
    )
    _attach(claim, "business-config-approval-runtime-%s" % suffix)
    return claim


def main():
    try:
        model_name = "sc.expense.claim"
        project = _project("Business Config Approval Runtime")
        partner = _partner("Business Config Approval Runtime Partner")

        _set_policy(model_name, True)
        required = _expense(project, partner, "required")
        required.action_submit()
        required.invalidate_recordset()
        print("%s_ENABLED_SUBMIT_STATE=%s/%s" % (model_name, required.state, required.validation_status))
        assert required.state == "submit", required.state
        assert required.validation_status in ("pending", "waiting", "no"), required.validation_status

        _set_policy(model_name, False)
        optional = _expense(project, partner, "optional")
        optional.action_submit()
        optional.invalidate_recordset()
        print("%s_DISABLED_SUBMIT_STATE=%s/%s" % (model_name, optional.state, optional.validation_status))
        assert optional.state == "approved", optional.state

        print("BUSINESS_CONFIG_APPROVAL_RUNTIME_SMOKE=PASS")
    finally:
        _env().cr.rollback()
        print("BUSINESS_CONFIG_APPROVAL_RUNTIME_ROLLBACK=OK")


main()
