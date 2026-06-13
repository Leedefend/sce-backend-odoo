# -*- coding: utf-8 -*-
"""Audit contract-domain business form policies.

Run inside Odoo shell:
    docker compose exec -T odoo odoo shell -c /var/lib/odoo/odoo.conf -d sc_demo < scripts/verify/contract_form_handling_policy_audit.py
"""

from odoo.addons.smart_core.handlers.ui_contract_v2 import UiContractV2Handler


CASES = [
    {
        "code": "contract.income",
        "action_xmlid": "smart_construction_core.action_construction_contract_income",
        "model": "construction.contract.income",
        "context": {
            "default_type": "out",
            "default_business_category_code": "contract.income",
        },
        "expected_slots": ["办理类型", "项目与发包人", "合同范围", "合同明细与金额", "办理说明"],
        "required_fields": ["business_category_id", "subject", "project_id", "partner_id", "tax_id", "line_ids"],
        "forbidden_create_fields": ["legacy_contract_no", "legacy_document_no", "entry_user_text", "settlement_amount"],
    },
    {
        "code": "contract.expense",
        "action_xmlid": "smart_construction_core.action_construction_contract_expense",
        "model": "construction.contract.expense",
        "context": {
            "default_type": "in",
            "default_business_category_code": "contract.expense",
        },
        "expected_slots": ["办理类型", "项目与供应商/分包方", "合同范围", "合同明细与金额", "办理说明"],
        "required_fields": [
            "business_category_id",
            "subject",
            "project_id",
            "partner_id",
            "expense_contract_category_id",
            "tax_id",
            "line_ids",
        ],
        "forbidden_create_fields": ["legacy_contract_no", "legacy_document_no", "entry_user_text", "paid_amount"],
    },
    {
        "code": "contract.expense.supplement",
        "action_xmlid": "smart_construction_core.action_construction_contract_expense",
        "model": "construction.contract.expense",
        "context": {
            "default_type": "in",
            "default_subject": "补充合同",
            "default_business_category_code": "contract.expense.supplement",
        },
        "expected_slots": ["办理类型", "项目与供应商/分包方", "补充事项", "补充明细与金额"],
        "required_fields": [
            "business_category_id",
            "subject",
            "project_id",
            "partner_id",
            "expense_contract_category_id",
            "tax_id",
            "line_ids",
        ],
        "forbidden_create_fields": ["legacy_contract_no", "legacy_document_no", "entry_user_text", "paid_amount"],
    },
]


def _legacy_dict(result):
    return result.to_legacy_dict() if hasattr(result, "to_legacy_dict") else result


def _structure_fields(structure):
    fields = []
    for slot in structure.get("slots") or []:
        for group in slot.get("groups") or []:
            fields.extend(group.get("fieldRefs") or [])
    return fields


handler = UiContractV2Handler(env, su_env=env["ir.model"].sudo().env)
errors = []

for case in CASES:
    action = env.ref(case["action_xmlid"])
    result = handler.handle(
        {
            "params": {
                "op": "action_open",
                "action_id": action.id,
                "model": case["model"],
                "view_type": "form",
                "render_profile": "create",
                "client_type": "web_pc",
                "delivery_profile": "full",
                "context": case["context"],
            }
        }
    )
    envelope = _legacy_dict(result)
    data = envelope.get("data") or {}
    structure = data.get("formStructureContract") or data.get("form_structure_contract") or {}
    slots = [slot.get("title") for slot in structure.get("slots") or []]
    fields = _structure_fields(structure)
    print("CASE", case["code"], "source", structure.get("source"), "slots", slots, "fields", len(fields))
    if envelope.get("ok") is not True:
        errors.append("%s: contract failed" % case["code"])
    if structure.get("source") != "ui.contract.v2.business_category_form_policy":
        errors.append("%s: missing business category form structure" % case["code"])
    for title in case["expected_slots"]:
        if title not in slots:
            errors.append("%s: missing slot %s" % (case["code"], title))
    for field_name in case["required_fields"]:
        if field_name not in fields:
            errors.append("%s: missing field %s" % (case["code"], field_name))
    for field_name in case["forbidden_create_fields"]:
        if field_name in fields:
            errors.append("%s: create form leaked %s" % (case["code"], field_name))

income_defaults = env["construction.contract.income"].with_context(
    default_type="out",
    default_business_category_code="contract.income",
).default_get(["business_category_id", "type", "tax_id"])
income_category = env["sc.business.category"].browse(income_defaults.get("business_category_id"))
if income_category.code != "contract.income":
    errors.append("contract.income default_get did not resolve business category")

supplement_defaults = env["construction.contract.expense"].with_context(
    default_type="in",
    default_subject="补充合同",
    default_business_category_code="contract.expense.supplement",
).default_get(["business_category_id", "type", "subject", "tax_id"])
supplement_category = env["sc.business.category"].browse(supplement_defaults.get("business_category_id"))
if supplement_category.code != "contract.expense.supplement":
    errors.append("contract.expense.supplement default_get did not resolve business category")

if errors:
    for error in errors:
        print("ERROR", error)
    raise SystemExit(1)

print("contract form handling policy audit passed")
