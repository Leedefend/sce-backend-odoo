# -*- coding: utf-8 -*-
"""Audit required-field marker projection for construction business forms.

Run inside Odoo shell:
    ENV=dev DB_NAME=sc_demo bash scripts/ops/odoo_shell_exec.sh < scripts/verify/industry_form_required_marker_audit.py
"""

import json

from odoo.addons.smart_core.app_config_engine.services.assemblers.page_assembler import PageAssembler  # noqa: F401


PROFILES = ("create", "edit")


def _json_value(record, field_name, fallback):
    raw = getattr(record, field_name, None)
    if raw in (None, False, ""):
        return fallback
    try:
        parsed = json.loads(raw)
        return parsed if isinstance(parsed, type(fallback)) else fallback
    except Exception:
        return fallback


def _normalize_profile(profile):
    normalized = str(profile or "").strip().lower()
    if normalized in {"read", "view"}:
        return "readonly"
    return normalized if normalized in {"create", "edit", "readonly"} else ""


def _profiles_match(profiles, profile):
    if not isinstance(profiles, list) or not profiles:
        return False
    wanted = _normalize_profile(profile)
    normalized = {
        _normalize_profile(item)
        for item in profiles
        if str(item or "").strip()
    }
    normalized.discard("")
    return wanted in normalized if wanted else bool(normalized & {"create", "edit"})


def _required_names(category, form_policy, fields_map, profile):
    required = []
    for name in _json_value(category, "required_fields_json", []):
        field_name = str(name or "").strip()
        if field_name and field_name in fields_map and field_name not in required:
            required.append(field_name)
    for name in form_policy.get("required_fields") if isinstance(form_policy.get("required_fields"), list) else []:
        field_name = str(name or "").strip()
        if field_name and field_name in fields_map and field_name not in required:
            required.append(field_name)
    for row in form_policy.get("fields") if isinstance(form_policy.get("fields"), list) else []:
        if not isinstance(row, dict):
            continue
        field_name = str(row.get("name") or row.get("field") or row.get("field_name") or "").strip()
        if field_name and field_name in fields_map and field_name not in required and _profiles_match(row.get("required_profiles"), profile):
            required.append(field_name)
    return required


def _walk_layout_required(layout):
    required = set()
    visible = set()

    def walk(node):
        if isinstance(node, list):
            for child in node:
                walk(child)
            return
        if not isinstance(node, dict):
            return
        if str(node.get("type") or "").strip().lower() == "field":
            name = str(node.get("name") or "").strip()
            if name:
                visible.add(name)
                field_info = node.get("fieldInfo") if isinstance(node.get("fieldInfo"), dict) else {}
                if node.get("required") is True or field_info.get("required") is True:
                    required.add(name)
        for key in ("children", "groups", "pages", "fields", "items", "nodes"):
            children = node.get(key)
            if isinstance(children, list):
                walk(children)

    walk(layout)
    return visible, required


def _validation_required(data, profile):
    out = set()
    for row in data.get("validation_rules") if isinstance(data.get("validation_rules"), list) else []:
        if not isinstance(row, dict):
            continue
        if str(row.get("code") or "").strip().upper() != "REQUIRED":
            continue
        field_name = str(row.get("field") or "").strip()
        if not field_name:
            continue
        profiles = row.get("when_profiles")
        if isinstance(profiles, list) and profiles and not _profiles_match(profiles, profile):
            continue
        out.add(field_name)
    return out


def _audit_category(category, profile):
    model_name = str(category.target_model or "").strip()
    form_policy = _json_value(category, "form_policy_json", {})
    if not model_name or model_name not in env or not isinstance(form_policy, dict):  # noqa: F821
        return []
    fields_map = env[model_name].sudo().fields_get()  # noqa: F821
    expected = _required_names(category, form_policy, fields_map, profile)
    if not expected:
        return []
    payload = {
        "model": model_name,
        "view_types": ["form"],
        "view_type": "form",
        "render_profile": profile,
        "context": {
            "default_business_category_code": str(category.code or "").strip(),
            "current_business_category_code": str(category.code or "").strip(),
        },
    }
    data, _versions = PageAssembler(env).assemble_page_contract(payload)  # noqa: F821
    contract_fields = data.get("fields") if isinstance(data.get("fields"), dict) else {}
    field_policies = data.get("field_policies") if isinstance(data.get("field_policies"), dict) else {}
    business_policy = data.get("business_form_policy") if isinstance(data.get("business_form_policy"), dict) else {}
    business_required = set(str(name or "").strip() for name in (business_policy.get("required_fields") or []) if str(name or "").strip())
    validation_required = _validation_required(data, profile)
    form = (data.get("views") or {}).get("form") if isinstance(data.get("views"), dict) else {}
    layout_visible, layout_required = _walk_layout_required(form.get("layout") if isinstance(form, dict) else [])

    errors = []
    for name in expected:
        descriptor = contract_fields.get(name) if isinstance(contract_fields.get(name), dict) else {}
        policy = field_policies.get(name) if isinstance(field_policies.get(name), dict) else {}
        policy_marks_required = policy.get("source_required") is True or _profiles_match(policy.get("required_profiles"), profile)
        if descriptor.get("required") is not True:
            errors.append("%s/%s/%s: field descriptor missing required marker" % (category.code, profile, name))
        if not policy_marks_required:
            errors.append("%s/%s/%s: field policy missing required marker" % (category.code, profile, name))
        if name not in business_required:
            errors.append("%s/%s/%s: business_form_policy.required_fields missing" % (category.code, profile, name))
        if name not in validation_required:
            errors.append("%s/%s/%s: validation REQUIRED rule missing" % (category.code, profile, name))
        if name in layout_visible and name not in layout_required:
            errors.append("%s/%s/%s: layout fieldInfo missing required marker" % (category.code, profile, name))
    return errors


categories = env["sc.business.category"].sudo().search([("target_model", "!=", False)], order="code")  # noqa: F821
all_errors = []
checked = 0
for category in categories:
    form_policy = _json_value(category, "form_policy_json", {})
    if not isinstance(form_policy, dict) or not (form_policy.get("fields") or form_policy.get("required_fields")):
        continue
    for profile in PROFILES:
        errors = _audit_category(category, profile)
        if errors:
            all_errors.extend(errors)
        checked += 1

if all_errors:
    print("[industry_form_required_marker_audit] FAIL checked=%s errors=%s" % (checked, len(all_errors)))
    for error in all_errors[:120]:
        print("ERROR", error)
    if len(all_errors) > 120:
        print("ERROR ... truncated %s more" % (len(all_errors) - 120))
    raise SystemExit(1)

print("[industry_form_required_marker_audit] PASS checked=%s categories=%s" % (checked, len(categories)))
