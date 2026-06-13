# -*- coding: utf-8 -*-
"""Audit interactive form capabilities for category-driven handling forms.

This goes beyond field visibility:
- category defaults are valid and can be passed through Odoo default_get;
- select fields have option sources;
- attachment policies have usable attachment fields;
- relationship fields have available data and critical cascade/domain support.

Run inside Odoo shell:
    docker exec -i sc-backend-odoo-dev-odoo-1 odoo shell -c /var/lib/odoo/odoo.conf -d sc_demo < scripts/verify/business_form_interaction_capability_audit.py
"""

from __future__ import annotations

import json

from odoo.addons.smart_core.handlers.ui_contract_v2 import UiContractV2Handler


CRITICAL_CASCADE_FIELDS = {
    "contract_id",
    "settlement_id",
    "material_settlement_id",
    "payment_request_id",
}
RELATION_CONTEXT_FIELDS = {"project_id", "partner_id", "contract_id"}
ATTACHMENT_FIELD_NAMES = {"attachment_ids", "biz_attachment_ids", "tech_attachment_ids"}
ATTACHMENT_AUDIT_EXEMPT_TARGET_MODELS = {
    "sc.company.contractor.responsibility.fact",
    "sc.company.contractor.responsibility.summary",
}


def _legacy_dict(result):
    return result.to_legacy_dict() if hasattr(result, "to_legacy_dict") else result


def _json_dict(raw):
    try:
        parsed = json.loads(raw or "{}")
    except Exception:
        return {}
    return parsed if isinstance(parsed, dict) else {}


def _field_refs(structure):
    refs = []
    for slot in structure.get("slots") or []:
        for group in slot.get("groups") or []:
            for field_name in group.get("fieldRefs") or []:
                if field_name and field_name not in refs:
                    refs.append(field_name)
    return refs


def _selection_has_options(field):
    selection = getattr(field, "selection", None)
    if callable(selection):
        return True
    if isinstance(selection, str):
        return True
    return bool(selection)


def _has_onchange(model, field_name):
    onchange_methods = getattr(model, "_onchange_methods", {}) or {}
    return bool(onchange_methods.get(field_name))


def _field_domain_text(field):
    domain = getattr(field, "domain", None)
    return str(domain or "")


def _is_usable_attachment_field(field):
    return (
        field.type == "many2many"
        and getattr(field, "comodel_name", "") == "ir.attachment"
        and not getattr(field, "readonly", False)
    )


def _contract(handler, category):
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
    )
    return (envelope.get("data") or {}).get("formStructureContract") or {}


handler = UiContractV2Handler(env, su_env=env["ir.model"].sudo().env)
Category = env["sc.business.category"].sudo()
categories = Category.search([], order="domain, code")

errors = []
warnings = []
summary = {
    "checked": 0,
    "selection_fields": 0,
    "many2one_fields": 0,
    "attachment_categories": 0,
    "critical_cascade_fields": 0,
}

for category in categories:
    if category.target_model not in env:
        errors.append("%s: missing target model %s" % (category.code, category.target_model))
        continue
    model = env[category.target_model].sudo()
    structure = _contract(handler, category)
    refs = _field_refs(structure)
    ref_set = set(refs)
    fields = model._fields
    summary["checked"] += 1

    defaults = _json_dict(category.default_values_json)
    default_context = {
        "default_business_category_code": category.code,
        "current_business_category_code": category.code,
    }
    for key, value in defaults.items():
        if key == "business_category_code":
            continue
        if key not in fields:
            errors.append("%s: default value references missing field %s" % (category.code, key))
            continue
        default_context["default_%s" % key] = value
    if "business_category_id" in fields:
        default_context["default_business_category_id"] = category.id
    default_fields = [name for name in defaults if name in fields]
    if "business_category_id" in fields:
        default_fields.append("business_category_id")
    if default_fields:
        got = model.with_context(**default_context).default_get(default_fields)
        for key, value in defaults.items():
            if key == "business_category_code" or key not in fields:
                continue
            if key not in got:
                errors.append("%s: default_get did not expose default for %s" % (category.code, key))
        if "business_category_id" in fields and got.get("business_category_id") != category.id:
            errors.append("%s: business_category_id default not applied" % category.code)

    if (
        category.attachment_policy in {"required", "recommended"}
        and category.target_model not in ATTACHMENT_AUDIT_EXEMPT_TARGET_MODELS
    ):
        summary["attachment_categories"] += 1
        attachment_refs = [name for name in refs if name in fields and _is_usable_attachment_field(fields[name])]
        if not attachment_refs:
            errors.append("%s: %s attachment policy but no usable ir.attachment field on create form" % (category.code, category.attachment_policy))

    for field_name in refs:
        field = fields.get(field_name)
        if not field:
            continue
        if field.type == "selection" and not getattr(field, "readonly", False):
            summary["selection_fields"] += 1
            if not _selection_has_options(field):
                errors.append("%s: selection field %s has no option source" % (category.code, field_name))
        if field.type == "many2one":
            summary["many2one_fields"] += 1
            comodel = getattr(field, "comodel_name", "")
            if not comodel or comodel not in env:
                errors.append("%s: relation field %s points to missing model %s" % (category.code, field_name, comodel))
                continue
            if field_name in RELATION_CONTEXT_FIELDS or field_name in CRITICAL_CASCADE_FIELDS or field_name == "business_category_id":
                count = env[comodel].sudo().search_count([])
                if count <= 0:
                    warnings.append("%s: relation field %s target model %s currently has no records" % (category.code, field_name, comodel))
            if field_name in CRITICAL_CASCADE_FIELDS:
                summary["critical_cascade_fields"] += 1
                domain_text = _field_domain_text(field)
                has_context_domain = any(token in domain_text for token in ("project_id", "partner_id", "contract_id", "type", "state"))
                has_related_onchange = _has_onchange(model, field_name) or any(_has_onchange(model, ctx) for ctx in ("project_id", "partner_id", "type"))
                if "project_id" in ref_set and not (has_context_domain or has_related_onchange):
                    errors.append(
                        "%s: relation field %s lacks project/partner/type domain or onchange cascade"
                        % (category.code, field_name)
                    )

print("business_form_interaction_capability checked=%s errors=%s warnings=%s summary=%s" % (summary["checked"], len(errors), len(warnings), summary))
for error in errors:
    print("ERROR", error)
for warning in warnings:
    print("WARN", warning)
if errors:
    raise SystemExit(1)
print("business form interaction capability audit passed")
