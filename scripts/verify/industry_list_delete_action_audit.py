# -*- coding: utf-8 -*-
"""Audit industry business-category list delete action projection.

Run inside Odoo shell:
    ENV=dev DB_NAME=sc_demo bash scripts/ops/odoo_shell_exec.sh < scripts/verify/industry_list_delete_action_audit.py
"""

import json

from odoo.addons.smart_core.app_config_engine.services.assemblers.page_assembler import PageAssembler  # noqa: F401
from odoo.addons.smart_core.utils.contract_governance import apply_contract_governance  # noqa: F401
from odoo.addons.smart_core.utils.delete_policy import resolve_unlink_policy  # noqa: F401


def _json_value(record, field_name, fallback):
    raw = getattr(record, field_name, None)
    if raw in (None, False, ""):
        return fallback
    try:
        parsed = json.loads(raw)
        return parsed if isinstance(parsed, type(fallback)) else fallback
    except Exception:
        return fallback


def _as_dict(value):
    return value if isinstance(value, dict) else {}


def _runtime_batch_policies(data):
    list_profile = _as_dict(data.get("list_profile"))
    surface_policies = _as_dict(data.get("surface_policies"))
    profile_policy = _as_dict(list_profile.get("batch_policy"))
    surface_policy = _as_dict(surface_policies.get("batch_policy"))
    policies = []
    if profile_policy:
        policies.append(("list_profile.batch_policy", profile_policy))
    if surface_policy:
        policies.append(("surface_policies.batch_policy", surface_policy))
    return policies


def _rights(data):
    permissions = _as_dict(data.get("permissions"))
    effective = _as_dict(permissions.get("effective"))
    return _as_dict(effective.get("rights"))


def _is_readonly_projection_model(model_name):
    tokens = tuple(part.strip().lower() for part in str(model_name or "").split(".") if part.strip())
    return any(token in tokens for token in ("fact", "summary", "residual", "ledger", "candidate"))


def _category_payload(category):
    code = str(category.code or "").strip()
    defaults = _json_value(category, "default_values_json", {})
    context = {"allowed_business_category_codes": [code]} if code else {}
    if code:
        context["current_business_category_code"] = code
        context["default_business_category_code"] = code
    for key, value in defaults.items():
        context.setdefault("default_%s" % key, value)
    return {
        "model": str(category.target_model or "").strip(),
        "view_types": ["tree"],
        "view_type": "tree",
        "context": context,
    }


def _audit_category(category):
    model_name = str(category.target_model or "").strip()
    if not model_name or model_name not in env:  # noqa: F821
        return [], False
    delete_policy = resolve_unlink_policy(env, model_name)  # noqa: F821
    if (
        env[model_name].check_access_rights("unlink", raise_exception=False)  # noqa: F821
        and not _is_readonly_projection_model(model_name)
        and (
            not bool(delete_policy.get("allowed"))
            or str(delete_policy.get("delete_mode") or "").strip().lower() != "unlink"
        )
    ):
        return [
            "%s/%s: model has unlink ACL but no delete_policy; add a governed unlink policy or explicitly classify it read-only"
            % (category.code, model_name)
        ], True
    if not bool(delete_policy.get("allowed")) or str(delete_policy.get("delete_mode") or "").strip().lower() != "unlink":
        return [], False

    data, _versions = PageAssembler(env).assemble_page_contract(_category_payload(category))  # noqa: F821
    data = apply_contract_governance(data, "user", inject_contract_mode=False)
    rights = _rights(data)
    errors = []
    if not bool(rights.get("unlink")):
        errors.append(
            "%s/%s: delete_policy allows unlink but effective permissions omit unlink"
            % (category.code, model_name)
        )
        return errors, True

    policies = _runtime_batch_policies(data)
    if not policies:
        errors.append("%s/%s: list contract missing batch_policy" % (category.code, model_name))
        return errors, True

    for source, policy in policies:
        actions = [str(item or "").strip().lower() for item in (policy.get("available_actions") or [])]
        delete_mode = str(policy.get("delete_mode") or "").strip().lower()
        if "delete" not in actions:
            errors.append("%s/%s/%s: available_actions missing delete" % (category.code, model_name, source))
        if delete_mode != "unlink":
            errors.append("%s/%s/%s: delete_mode must be unlink" % (category.code, model_name, source))
        if policy.get("enabled") is not True:
            errors.append("%s/%s/%s: batch_policy must be enabled" % (category.code, model_name, source))
    return errors, True


categories = env["sc.business.category"].sudo().search([("target_model", "!=", False)], order="code")  # noqa: F821
all_errors = []
checked = 0
for category in categories:
    errors, expected = _audit_category(category)
    if not expected:
        continue
    checked += 1
    all_errors.extend(errors)

if all_errors:
    print("[industry_list_delete_action_audit] FAIL checked=%s errors=%s" % (checked, len(all_errors)))
    for error in all_errors[:160]:
        print("ERROR", error)
    if len(all_errors) > 160:
        print("ERROR ... truncated %s more" % (len(all_errors) - 160))
    raise SystemExit(1)

print("[industry_list_delete_action_audit] PASS checked=%s categories=%s" % (checked, len(categories)))
