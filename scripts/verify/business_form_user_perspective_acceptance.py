# -*- coding: utf-8 -*-
"""User-perspective acceptance for category-driven business handling forms.

This verifies the create-form contract users actually see:
- every business category opens a category-owned form structure;
- create forms do not show migration/source/audit fields;
- create forms keep the business flow shape: identity, object, document/detail;
- readonly forms keep source-trace sections where the policy defines them.

Run inside Odoo shell:
    docker compose exec -T odoo odoo shell -c /var/lib/odoo/odoo.conf -d sc_demo < scripts/verify/business_form_user_perspective_acceptance.py
"""

from odoo.addons.smart_core.handlers.ui_contract_v2 import UiContractV2Handler


CREATE_FORBIDDEN_FIELDS = {
    "active",
    "creator_legacy_user_id",
    "creator_name",
    "created_time",
    "entry_user_id",
    "entry_data",
    "source_created_by",
    "source_created_at",
    "validation_status",
    "can_review",
    "reject_reason",
}
CREATE_FORBIDDEN_PREFIXES = ("legacy_",)
READONLY_ONLY_PREFIXES = ("legacy_",)


def _legacy_dict(result):
    return result.to_legacy_dict() if hasattr(result, "to_legacy_dict") else result


def _field_refs(structure):
    refs = []
    for slot in structure.get("slots") or []:
        for group in slot.get("groups") or []:
            for field_name in group.get("fieldRefs") or []:
                if field_name and field_name not in refs:
                    refs.append(field_name)
    return refs


def _slot_titles(structure):
    return [str(slot.get("title") or "").strip() for slot in structure.get("slots") or []]


def _contract(handler, category, profile):
    action_id = None
    if category.action_xmlid:
        action = env.ref(category.action_xmlid, raise_if_not_found=False)
        action_id = action.id if action else None
    envelope = _legacy_dict(
        handler.handle(
            {
                "params": {
                    "op": "action_open" if action_id else "model",
                    "action_id": action_id,
                    "model": category.target_model,
                    "view_type": "form",
                    "render_profile": profile,
                    "client_type": "web_pc",
                    "delivery_profile": "full",
                    "context": {
                        "default_business_category_code": category.code,
                        "current_business_category_code": category.code,
                    },
                }
            }
        )
    )
    return (envelope.get("data") or {}).get("formStructureContract") or {}


handler = UiContractV2Handler(env, su_env=env["ir.model"].sudo().env)
Category = env["sc.business.category"].sudo()
categories = Category.search([], order="domain, code")
errors = []
checked = 0

for category in categories:
    if category.target_model not in env.registry:
        errors.append("%s: missing target model %s" % (category.code, category.target_model))
        continue

    create_structure = _contract(handler, category, "create")
    checked += 1
    if create_structure.get("source") != "ui.contract.v2.business_category_form_policy":
        errors.append("%s: create form is not category-owned" % category.code)
        continue

    create_refs = _field_refs(create_structure)
    create_titles = _slot_titles(create_structure)
    leaked = [
        field_name
        for field_name in create_refs
        if field_name.startswith(CREATE_FORBIDDEN_PREFIXES) or field_name in CREATE_FORBIDDEN_FIELDS
    ]
    if leaked:
        errors.append("%s: create form leaks history/audit fields %s" % (category.code, ",".join(leaked)))

    if "business_category_id" in env[category.target_model]._fields and "business_category_id" not in create_refs:
        errors.append("%s: create form missing business_category_id" % category.code)
    if "project_id" in env[category.target_model]._fields and "project_id" not in create_refs:
        errors.append("%s: create form missing project_id" % category.code)
    business_title_text = "".join(create_titles)
    business_title_tokens = (
        "明细",
        "金额",
        "事项",
        "问题",
        "整改",
        "复验",
        "合同",
        "日志",
        "责任",
        "确认",
        "登记",
        "支付",
        "退回",
        "往来",
        "日报",
        "余额",
        "抵扣",
        "现场情况",
        "质量安全",
        "项目款",
        "借公司款",
        "收入",
        "收款",
    )
    summary_or_readonly_category = category.code in {
        "finance.responsibility.company_contractor.balance",
    }
    if not summary_or_readonly_category and not any(token in business_title_text for token in business_title_tokens):
        errors.append("%s: create form missing business document/detail section" % category.code)

    readonly_structure = _contract(handler, category, "readonly")
    readonly_refs = _field_refs(readonly_structure)
    policy_fields = (category.form_policy_json or "")
    expects_history = any(prefix in policy_fields for prefix in READONLY_ONLY_PREFIXES)
    if expects_history and not any(field_name.startswith(READONLY_ONLY_PREFIXES) for field_name in readonly_refs):
        errors.append("%s: readonly form lost legacy/source continuity fields" % category.code)

print("business_form_user_perspective_acceptance checked=%s errors=%s" % (checked, len(errors)))
for error in errors:
    print("ERROR", error)
if errors:
    raise SystemExit(1)
print("business form user perspective acceptance passed")
