# -*- coding: utf-8 -*-
"""Audit business-category form policy coverage and create-form projection.

Run inside Odoo shell:
    docker compose exec -T odoo odoo shell -c /var/lib/odoo/odoo.conf -d sc_demo < scripts/verify/business_form_policy_coverage_audit.py
"""

from odoo.addons.smart_core.handlers.ui_contract_v2 import UiContractV2Handler


TRACE_FIELDS_FORBIDDEN_ON_CREATE = {
    "legacy_source_table",
    "legacy_record_id",
    "legacy_contract_no",
    "creator_name",
    "created_time",
    "source_created_by",
    "source_created_at",
}


def _legacy_dict(result):
    return result.to_legacy_dict() if hasattr(result, "to_legacy_dict") else result


def _field_refs(structure):
    out = []
    for slot in structure.get("slots") or []:
        for group in slot.get("groups") or []:
            out.extend(group.get("fieldRefs") or [])
    return out


handler = UiContractV2Handler(env, su_env=env["ir.model"].sudo().env)
Category = env["sc.business.category"].sudo()
categories = Category.search([], order="domain, code")
errors = []
checked = 0

for category in categories:
    if (category.form_policy_json or "").strip() in ("", "{}"):
        errors.append("%s: missing form_policy_json" % category.code)
        continue
    if category.target_model not in env:
        errors.append("%s: missing target model %s" % (category.code, category.target_model))
        continue

    action_id = None
    if category.action_xmlid:
        action = env.ref(category.action_xmlid, raise_if_not_found=False)
        action_id = action.id if action else None
    result = handler.handle(
        {
            "params": {
                "op": "action_open" if action_id else "model",
                "action_id": action_id,
                "model": category.target_model,
                "view_type": "form",
                "render_profile": "create",
                "client_type": "web_pc",
                "delivery_profile": "full",
                "context": {
                    "default_business_category_code": category.code,
                    "current_business_category_code": category.code,
                },
            }
        }
    )
    envelope = _legacy_dict(result)
    data = envelope.get("data") or {}
    structure = data.get("formStructureContract") or data.get("form_structure_contract") or {}
    refs = _field_refs(structure)
    checked += 1
    if envelope.get("ok") is not True:
        errors.append("%s: ui.contract.v2 returned not ok" % category.code)
    if structure.get("source") != "ui.contract.v2.business_category_form_policy":
        errors.append("%s: missing business form structure source" % category.code)
    if not structure.get("slots"):
        errors.append("%s: empty business form slots" % category.code)
    leaked = sorted(TRACE_FIELDS_FORBIDDEN_ON_CREATE.intersection(refs))
    if leaked:
        errors.append("%s: create form leaks trace fields %s" % (category.code, ",".join(leaked)))

print("business_form_policy_coverage checked=%s total=%s errors=%s" % (checked, len(categories), len(errors)))
for error in errors:
    print("ERROR", error)
if errors:
    raise SystemExit(1)
print("business form policy coverage audit passed")
