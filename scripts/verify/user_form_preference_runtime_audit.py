# -*- coding: utf-8 -*-
"""Audit user form preferences on discovered business forms.

Run inside Odoo shell:
    bash scripts/ops/odoo_shell_exec.sh < scripts/verify/user_form_preference_runtime_audit.py
"""

from odoo.addons.smart_core.app_config_engine.services.assemblers.page_assembler import PageAssembler
from odoo.addons.smart_construction_custom.models import user_preferences

def _walk_layout(layout):
    names = []
    three_column_nodes = []
    tab_like_nodes = []
    required_nodes = []

    def visit(node):
        if isinstance(node, list):
            for item in node:
                visit(item)
            return
        if not isinstance(node, dict):
            return
        name = str(node.get("name") or "").strip()
        node_type = str(node.get("type") or "").strip().lower()
        if name:
            names.append(name)
        if node.get("columns") in (3, "3"):
            three_column_nodes.append(name or node_type or "node")
        if node_type in {"page", "notebook", "tab"} or node.get("pages") or node.get("tabs"):
            tab_like_nodes.append(name or node_type or "node")
        field_info = node.get("fieldInfo") if isinstance(node.get("fieldInfo"), dict) else {}
        if node_type == "field" and name and (node.get("required") is True or field_info.get("required") is True):
            required_nodes.append(name)
        for value in node.values():
            visit(value)

    visit(layout)
    return names, three_column_nodes, tab_like_nodes, required_nodes


def _required_rule_fields(data):
    out = set()
    for row in data.get("validation_rules") if isinstance(data.get("validation_rules"), list) else []:
        if not isinstance(row, dict):
            continue
        if str(row.get("code") or "").strip().upper() != "REQUIRED":
            continue
        name = str(row.get("field") or "").strip()
        if name:
            out.add(name)
    return out


failures = []
checked = 0
assembler = PageAssembler(env)
initializer = env["sc.user.preference.initialization"]

for item in initializer._formal_handling_form_targets():
    xmlid = item.get("menu_xmlid") or "menu:%s" % item.get("menu_id")
    action_rec = item["action"]

    data, _versions = assembler.assemble_page_contract(
        {
            "model": action_rec.res_model,
            "view_types": ["form"],
            "view_type": "form",
            "action_id": int(action_rec.id),
            "render_profile": "create",
        },
        action=action_rec.read()[0],
    )
    layout = (((data.get("views") or {}).get("form") or {}).get("layout")) or []
    names, three_column_nodes, tab_like_nodes, _required_nodes = _walk_layout(layout)
    checked += 1

    if "sc_custom_user_flat_fields" not in names:
        failures.append((xmlid, "missing_user_flat_layout", action_rec.res_model, int(action_rec.id), names[:8]))
    if not three_column_nodes:
        failures.append((xmlid, "missing_three_columns", action_rec.res_model, int(action_rec.id)))
    if tab_like_nodes:
        failures.append((xmlid, "tab_like_layout_present", action_rec.res_model, int(action_rec.id), tab_like_nodes[:5]))

for key, config in user_preferences.PARTNER_ACTIONS.items():
    action_rec = env.ref(config["xmlid"], raise_if_not_found=False)
    if not action_rec:
        failures.append((config["xmlid"], "missing_partner_action"))
        continue
    data, _versions = assembler.assemble_page_contract(
        {
            "model": action_rec.res_model,
            "view_types": ["form"],
            "view_type": "form",
            "action_id": int(action_rec.id),
            "render_profile": "create",
        },
        action=action_rec.read()[0],
    )
    layout = (((data.get("views") or {}).get("form") or {}).get("layout")) or []
    names, three_column_nodes, tab_like_nodes, required_nodes = _walk_layout(layout)
    checked += 1
    fields_map = data.get("fields") if isinstance(data.get("fields"), dict) else {}
    field_policies = data.get("field_policies") if isinstance(data.get("field_policies"), dict) else {}
    validation_required = _required_rule_fields(data)
    configured_required = {
        str(name or "").strip()
        for name in config.get("required_fields", [])
        if str(name or "").strip()
    }
    expected_required = [
        name
        for name, _label in config["fields"]
        if name in fields_map
        and (
            name in configured_required
            or (isinstance(fields_map.get(name), dict) and fields_map[name].get("required") is True)
        )
    ]
    if "sc_custom_partner_flat_fields" not in names:
        failures.append((key, "missing_partner_flat_layout", int(action_rec.id), names[:8]))
    if not three_column_nodes:
        failures.append((key, "missing_partner_three_columns", int(action_rec.id)))
    if tab_like_nodes:
        failures.append((key, "partner_tab_like_layout_present", int(action_rec.id), tab_like_nodes[:5]))
    if not expected_required:
        failures.append((key, "partner_expected_required_empty", int(action_rec.id)))
    for name in expected_required:
        policy = field_policies.get(name) if isinstance(field_policies.get(name), dict) else {}
        if name not in required_nodes:
            failures.append((key, "partner_layout_required_missing", name, int(action_rec.id)))
        if policy.get("source_required") is not True:
            failures.append((key, "partner_field_policy_required_missing", name, int(action_rec.id)))
        if name not in validation_required:
            failures.append((key, "partner_validation_required_missing", name, int(action_rec.id)))

if failures:
    print("[user_form_preference_runtime_audit] FAIL checked=%s failures=%s" % (checked, len(failures)))
    for failure in failures:
        print(failure)
    raise SystemExit(1)

print("[user_form_preference_runtime_audit] PASS checked=%s" % checked)
