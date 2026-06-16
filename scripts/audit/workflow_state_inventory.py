#!/usr/bin/env python3
"""Inventory workflow state and approval surfaces from a live Odoo database.

Run inside ``odoo shell``:

    odoo shell -c /etc/odoo/odoo.conf -d sc_demo --no-http < scripts/audit/workflow_state_inventory.py

The script prints Markdown so the output can be redirected to docs or artifacts.
"""

from __future__ import annotations

import json
from collections import defaultdict
from datetime import datetime

from lxml import etree


CORE_MODULE_PREFIXES = (
    "smart_construction_core.",
    "payment.",
    "purchase.",
    "project.",
)

WORKFLOW_METHOD_NAMES = (
    "action_confirm",
    "action_submit",
    "action_submit_progress",
    "action_approve",
    "action_approval_decision",
    "action_done",
    "action_close",
    "action_accept",
    "action_reject",
    "action_receive",
    "action_issue",
    "action_activate",
    "action_deactivate",
    "action_return",
    "action_settle",
    "action_select",
    "action_release",
    "action_supersede",
    "action_mark_conflict",
    "action_mark_create_required",
    "action_ignore",
    "action_resolve_customer",
    "action_resolve_supplier",
    "action_resolve_customer_supplier",
    "action_paid",
    "action_received",
    "action_register",
    "action_deduct",
    "action_reconcile",
    "action_start",
    "action_reset_to_draft",
    "action_set_running",
    "action_reset_draft",
    "action_cancel",
    "button_confirm",
    "button_draft",
    "validate_tier",
    "reject_tier",
    "action_on_tier_approved",
    "action_on_tier_rejected",
)

STATE_FIELD_CANDIDATES = (
    "state",
    "sc_state",
    "lifecycle_state",
    "attainment_state",
    "candidate_state",
    "responsibility_state",
    "mapping_state",
    "suggested_state",
    "review_state",
    "promotion_state",
    "projection_state",
)


def _selection_pairs(field):
    selection = getattr(field, "selection", None) or []
    if callable(selection):
        return ["<callable>"]
    out = []
    for item in selection:
        if isinstance(item, (list, tuple)) and len(item) >= 2:
            out.append("%s=%s" % (item[0], item[1]))
        else:
            out.append(str(item))
    return out


def _model_modules(model_name):
    rows = env["ir.model.data"].sudo().search([
        ("model", "=", "ir.model"),
        ("module", "!=", "__export__"),
    ])
    model_records = env["ir.model"].sudo().search([("model", "=", model_name)])
    model_ids = set(model_records.ids)
    return sorted({row.module for row in rows if row.res_id in model_ids})


def _is_business_model(model_name, model_obj):
    if getattr(model_obj, "_abstract", False) or getattr(model_obj, "_transient", False):
        return False
    if model_name.startswith(("ir.", "res.", "mail.", "bus.", "base.", "web.")):
        return False
    if model_name.startswith(("smart_core.", "sc.", "payment.", "purchase.", "project.")):
        return True
    modules = _model_modules(model_name)
    return any(module.startswith("smart_construction") for module in modules)


def _button_rows(model_name):
    View = env["ir.ui.view"].sudo()
    views = View.search([
        ("model", "=", model_name),
        ("type", "=", "form"),
        ("arch_db", "!=", False),
    ])
    buttons = []
    for view in views:
        try:
            root = etree.fromstring((view.arch_db or "").encode("utf-8"))
        except Exception:
            continue
        for button in root.xpath(".//header//button | .//sheet//button | .//button"):
            name = (button.get("name") or "").strip()
            if not name:
                continue
            buttons.append({
                "view": view.xml_id or view.name or str(view.id),
                "name": name,
                "string": (button.get("string") or "").strip(),
                "type": (button.get("type") or "").strip(),
                "states": (button.get("states") or "").strip(),
                "invisible": (button.get("invisible") or "").strip(),
                "groups": (button.get("groups") or "").strip(),
            })
    dedup = []
    seen = set()
    for row in buttons:
        key = tuple(row.get(k, "") for k in ("view", "name", "string", "type", "states", "invisible", "groups"))
        if key in seen:
            continue
        seen.add(key)
        dedup.append(row)
    return dedup


def _tier_definition_count(model_name):
    Tier = env.get("tier.definition")
    if not Tier:
        return 0
    domain_candidates = [
        [("model", "=", model_name)],
        [("model_id.model", "=", model_name)],
    ]
    for domain in domain_candidates:
        try:
            return Tier.sudo().search_count(domain)
        except Exception:
            continue
    return 0


def _business_category_profile(model_name):
    Category = env.get("sc.business.category")
    if not Category:
        return []
    rows = Category.sudo().search([])
    out = []
    for row in rows:
        policy = row.ledger_policy_json or ""
        if model_name in policy:
            try:
                parsed = json.loads(policy)
            except Exception:
                parsed = {}
            out.append({
                "code": row.code,
                "name": row.name,
                "terminal_action": parsed.get("terminal_action") or "",
                "payment_request_policy": parsed.get("payment_request_policy") or "",
                "cashflow_policy": parsed.get("cashflow_policy") or "",
            })
    return out


def _workflow_contract_supported_models():
    if "sc.workflow.contract.service" not in env.registry.models:
        return set()
    Service = env["sc.workflow.contract.service"]
    profiles = getattr(Service, "PROFILE_BY_MODEL", None)
    if isinstance(profiles, dict):
        return set(profiles)
    try:
        return set(Service.sudo().supported_model_names())
    except Exception:
        return set()


def _workflow_methods(model_obj):
    return [name for name in WORKFLOW_METHOD_NAMES if callable(getattr(model_obj, name, None))]


def _state_fields(model_obj):
    rows = []
    for name in STATE_FIELD_CANDIDATES:
        field = model_obj._fields.get(name)
        if not field:
            continue
        rows.append({
            "name": name,
            "type": field.type,
            "required": bool(getattr(field, "required", False)),
            "readonly": bool(getattr(field, "readonly", False)),
            "selection": _selection_pairs(field) if field.type == "selection" else [],
        })
    return rows


def _approval_fields(model_obj):
    names = []
    for name in ("validation_status", "can_review", "review_ids", "rejected", "reject_reason"):
        if name in model_obj._fields:
            names.append(name)
    return names


def _statusbar_fields(buttons):
    out = set()
    for row in buttons:
        invisible = row.get("invisible") or ""
        states = row.get("states") or ""
        if "state" in invisible or states:
            out.add("state")
        if "validation_status" in invisible:
            out.add("validation_status")
        if "can_review" in invisible:
            out.add("can_review")
    return sorted(out)


def _print_model(row):
    print("### `%s`" % row["model"])
    print("")
    print("- Label: %s" % row["label"])
    print("- State fields: %s" % (", ".join("`%s`" % item["name"] for item in row["state_fields"]) or "-"))
    for field in row["state_fields"]:
        if field["selection"]:
            print("  - `%s`: %s" % (field["name"], "; ".join(field["selection"])))
    print("- Approval fields: %s" % (", ".join("`%s`" % item for item in row["approval_fields"]) or "-"))
    print("- Tier definitions: %s" % row["tier_definition_count"])
    print("- Workflow contract: %s" % ("covered" if row["workflow_contract_covered"] else "uncovered"))
    print("- Workflow methods: %s" % (", ".join("`%s`" % item for item in row["workflow_methods"]) or "-"))
    if row["buttons"]:
        print("- Header/form buttons:")
        for button in row["buttons"][:20]:
            print(
                "  - `%s` %s type=%s invisible=%s states=%s groups=%s"
                % (
                    button["name"],
                    button["string"] or "",
                    button["type"] or "-",
                    button["invisible"] or "-",
                    button["states"] or "-",
                    button["groups"] or "-",
                )
            )
        if len(row["buttons"]) > 20:
            print("  - ... %s more" % (len(row["buttons"]) - 20))
    if row["business_categories"]:
        print("- Business categories:")
        for category in row["business_categories"][:12]:
            print(
                "  - `%s` %s terminal=%s payment_policy=%s cashflow=%s"
                % (
                    category["code"],
                    category["name"],
                    category["terminal_action"] or "-",
                    category["payment_request_policy"] or "-",
                    category["cashflow_policy"] or "-",
                )
            )
    print("")


def main():
    rows = []
    covered_models = _workflow_contract_supported_models()
    for model_name in sorted(env.registry.models):
        model_obj = env[model_name]
        if not _is_business_model(model_name, model_obj):
            continue
        state_fields = _state_fields(model_obj)
        approval_fields = _approval_fields(model_obj)
        workflow_methods = _workflow_methods(model_obj)
        buttons = _button_rows(model_name)
        tier_count = _tier_definition_count(model_name)
        business_categories = _business_category_profile(model_name)
        if not any([state_fields, approval_fields, workflow_methods, buttons, tier_count, business_categories]):
            continue
        rows.append({
            "model": model_name,
            "label": model_obj._description or "",
            "state_fields": state_fields,
            "approval_fields": approval_fields,
            "workflow_methods": workflow_methods,
            "buttons": buttons,
            "tier_definition_count": tier_count,
            "business_categories": business_categories,
            "button_state_refs": _statusbar_fields(buttons),
            "workflow_contract_covered": model_name in covered_models,
        })

    print("# Workflow State Inventory")
    print("")
    print("- Generated: %s" % datetime.utcnow().isoformat(timespec="seconds") + "Z")
    print("- Database: %s" % env.cr.dbname)
    print("- Models with workflow signals: %s" % len(rows))
    print("")
    print("## Summary")
    print("")
    by_state_field = defaultdict(int)
    with_tier = 0
    with_approval_fields = 0
    with_workflow_methods = 0
    covered_count = 0
    for row in rows:
        for field in row["state_fields"]:
            by_state_field[field["name"]] += 1
        if row["tier_definition_count"]:
            with_tier += 1
        if row["approval_fields"]:
            with_approval_fields += 1
        if row["workflow_methods"]:
            with_workflow_methods += 1
        if row["workflow_contract_covered"]:
            covered_count += 1
    for name, count in sorted(by_state_field.items()):
        print("- `%s`: %s models" % (name, count))
    print("- tier definitions present: %s models" % with_tier)
    print("- approval fields present: %s models" % with_approval_fields)
    print("- workflow methods present: %s models" % with_workflow_methods)
    print("- workflowContract covered: %s models" % covered_count)
    print("- workflowContract uncovered: %s models" % (len(rows) - covered_count))
    print("")
    print("## Workflow Contract Coverage")
    print("")
    print("- Covered profiles: %s" % (", ".join("`%s`" % item for item in sorted(covered_models)) or "-"))
    print("- Uncovered models with workflow methods:")
    uncovered = [
        row for row in rows
        if row["workflow_methods"] and not row["workflow_contract_covered"]
    ]
    if uncovered:
        for row in uncovered:
            print("  - `%s`: %s" % (row["model"], ", ".join("`%s`" % item for item in row["workflow_methods"])))
    else:
        print("  - -")
    print("")
    print("## Models")
    print("")
    for row in rows:
        _print_model(row)


main()
