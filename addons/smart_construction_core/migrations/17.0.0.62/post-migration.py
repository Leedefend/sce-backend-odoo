# -*- coding: utf-8 -*-
from __future__ import annotations

import json

from odoo import SUPERUSER_ID, api


TECHNICAL_FIELD = "payment_family"
DISPLAY_FIELD = "payment_family_label"
TARGET_CATEGORY_CODE = "tax.certificate.registration"
TARGET_MODEL = "sc.legacy.payment.residual.fact"
TARGET_PAYMENT_FAMILY = "tax_certificate_registration"
TARGET_LABEL = "外经证登记"


def _payload(value):
    if isinstance(value, dict):
        return dict(value)
    if not value:
        return {}
    try:
        parsed = json.loads(value)
    except Exception:
        return {}
    return parsed if isinstance(parsed, dict) else {}


def _replace_field_names(items):
    if not isinstance(items, list):
        return items, False
    changed = False
    next_items = []
    for item in items:
        if isinstance(item, str):
            if item == TECHNICAL_FIELD:
                next_items.append(DISPLAY_FIELD)
                changed = True
            else:
                next_items.append(item)
            continue
        if isinstance(item, dict):
            next_item = dict(item)
            if next_item.get("name") == TECHNICAL_FIELD:
                next_item["name"] = DISPLAY_FIELD
                changed = True
            if next_item.get("name") == DISPLAY_FIELD:
                if next_item.get("visible_profiles") != ["edit", "readonly"]:
                    next_item["visible_profiles"] = ["edit", "readonly"]
                    changed = True
                if next_item.get("readonly_profiles") != ["create", "edit", "readonly"]:
                    next_item["readonly_profiles"] = ["create", "edit", "readonly"]
                    changed = True
                if next_item.get("group") != "advanced":
                    next_item["group"] = "advanced"
                    changed = True
            next_items.append(next_item)
            continue
        next_items.append(item)
    return next_items, changed


def _normalize_policy(payload):
    if not isinstance(payload, dict):
        return payload, False
    next_payload = dict(payload)
    changed = False

    fields, fields_changed = _replace_field_names(next_payload.get("fields"))
    if fields_changed:
        next_payload["fields"] = fields
        changed = True

    sections = next_payload.get("sections")
    if isinstance(sections, list):
        next_sections = []
        for section in sections:
            if not isinstance(section, dict):
                next_sections.append(section)
                continue
            next_section = dict(section)
            section_fields, section_changed = _replace_field_names(next_section.get("fields"))
            if section_changed:
                next_section["fields"] = section_fields
                changed = True
            next_sections.append(next_section)
        if changed:
            next_payload["sections"] = next_sections

    return next_payload, changed


def _normalize_contract(payload):
    next_payload, changed = _normalize_policy(payload)
    orchestration = next_payload.get("view_orchestration") if isinstance(next_payload, dict) else None
    form = (((orchestration or {}).get("views") or {}).get("form") or {}) if isinstance(orchestration, dict) else {}
    if isinstance(form, dict):
        next_form, form_changed = _normalize_policy(form)
        if form_changed:
            next_payload = dict(next_payload)
            next_orchestration = dict(orchestration)
            next_views = dict(next_orchestration.get("views") or {})
            next_views["form"] = next_form
            next_orchestration["views"] = next_views
            next_payload["view_orchestration"] = next_orchestration
            changed = True
    return next_payload, changed


def migrate(cr, version):
    env = api.Environment(cr, SUPERUSER_ID, {})
    updates = {"categories": 0, "contracts": 0}

    Category = env["sc.business.category"].sudo()
    category = Category.search([("code", "=", TARGET_CATEGORY_CODE)], limit=1)
    if category:
        default_values = _payload(category.default_values_json)
        if default_values.get(TECHNICAL_FIELD) == TARGET_PAYMENT_FAMILY and default_values.get(DISPLAY_FIELD) != TARGET_LABEL:
            default_values[DISPLAY_FIELD] = TARGET_LABEL
            category.write({"default_values_json": json.dumps(default_values, ensure_ascii=False)})
            updates["categories"] += 1

        payload, changed = _normalize_policy(_payload(category.form_policy_json))
        if changed:
            category.write({"form_policy_json": json.dumps(payload, ensure_ascii=False)})
            updates["categories"] += 1

    Contract = env["ui.business.config.contract"].sudo().with_context(active_test=False)
    contracts = Contract.search([
        ("model", "=", TARGET_MODEL),
        ("view_type", "=", "form"),
        ("active", "=", True),
        ("status", "=", "published"),
    ])
    for rec in contracts:
        payload, changed = _normalize_contract(_payload(rec.contract_json))
        if not changed:
            continue
        cr.execute(
            """
            UPDATE ui_business_config_contract
               SET contract_json = %s::jsonb,
                   write_date = NOW()
             WHERE id = %s
            """,
            (json.dumps(payload, ensure_ascii=False), rec.id),
        )
        updates["contracts"] += 1

    print(
        "[17.0.0.62] tax certificate visible family label normalized: categories=%s contracts=%s"
        % (updates["categories"], updates["contracts"])
    )
