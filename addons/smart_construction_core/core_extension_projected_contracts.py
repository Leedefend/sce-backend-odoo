# -*- coding: utf-8 -*-
import logging

from odoo.addons.smart_construction_core.core_extension_policy_catalog import (
    USER_CONFIRMED_FORMAL_LIST_ACTION_XMLIDS,
)

_logger = logging.getLogger(__name__)


def _user_confirmed_formal_list_action_ids(env):
    ids = set()
    for xmlid in USER_CONFIRMED_FORMAL_LIST_ACTION_XMLIDS:
        rec = env.ref(xmlid, raise_if_not_found=False)
        if rec and rec.exists():
            ids.add(int(rec.id))
    return ids


def smart_core_finalize_projected_contract_data(env, data, context):
    if not isinstance(data, dict):
        return None
    head = data.get("head") if isinstance(data.get("head"), dict) else {}
    model = str(data.get("model") or head.get("model") or "").strip()
    view_type = str(data.get("view_type") or head.get("view_type") or (context or {}).get("view_type") or "").strip().lower()
    if model == "project.project" and (view_type == "form" or isinstance((data.get("views") or {}).get("form") if isinstance(data.get("views"), dict) else None, dict)):
        projected = dict(data)
        try:
            from odoo.addons.smart_construction_core.services.contract_governance_overrides import (
                _apply_project_ledger_form_surface_governance,
            )

            _apply_project_ledger_form_surface_governance(projected, "user")
            return projected
        except Exception:
            _logger.exception("Failed to finalize project form contract surface")
            return None
    try:
        action_id = int(data.get("action_id") or head.get("action_id") or 0)
    except Exception:
        action_id = 0
    list_profile = data.get("list_profile") if isinstance(data.get("list_profile"), dict) else {}
    column_policy = list_profile.get("column_policy") if isinstance(list_profile.get("column_policy"), dict) else {}
    if str(column_policy.get("reason") or "").strip() == "business_list_config_contract_authoritative":
        return None
    if not action_id or action_id not in _user_confirmed_formal_list_action_ids(env):
        return None
    action = env["ir.actions.act_window"].sudo().browse(action_id)
    if not action.exists() or not action.res_model:
        return None
    try:
        view_contract = (
            env["app.view.config"]
            .with_context(contract_action_id=action_id, contract_projection_readonly=True)
            ._generate_from_fields_view_get(action.res_model, "tree")
            .with_user(env.user)
            .sudo()
            .with_context(contract_action_id=action_id, contract_projection_readonly=True)
            .get_contract_api(filter_runtime=True, check_model_acl=True)
        )
    except Exception:
        _logger.exception("Failed to lock user-confirmed formal list contract for action_id=%s", action_id)
        return None
    if not isinstance(view_contract, dict):
        return None
    try:
        import xml.etree.ElementTree as ET

        view = action.view_id
        arch = view.arch_db if view and view.exists() else ""
        root = ET.fromstring(arch) if arch else None
        fields_get = env[action.res_model].sudo().fields_get()
        locked_columns = []
        locked_schema = []
        locked_order = ""
        if root is not None and root.tag in ("tree", "list"):
            locked_order = str(root.get("default_order") or "").strip()
            for node in root.findall(".//field[@name]"):
                name = str(node.get("name") or "").strip()
                if not name:
                    continue
                if str(node.get("column_invisible") or "").strip() in {"1", "True", "true"}:
                    continue
                meta = fields_get.get(name) or {}
                label = str(node.get("string") or meta.get("string") or name)
                locked_columns.append(name)
                locked_schema.append({
                    "name": name,
                    "label": label,
                    "string": label,
                    "type": meta.get("type") or "char",
                    "widget": node.get("widget") or "",
                    "optional": node.get("optional") or "",
                })
    except Exception:
        _logger.exception("Failed to parse locked tree view for action_id=%s", action_id)
        locked_columns = []
        locked_schema = []
        locked_order = ""

    locked = dict(data)
    views = dict(locked.get("views") if isinstance(locked.get("views"), dict) else {})
    tree = dict(view_contract)
    if locked_columns:
        tree["columns"] = locked_columns
        tree["columns_schema"] = locked_schema
    if locked_order:
        tree["order"] = locked_order
        tree["default_order"] = locked_order
    governance = dict(tree.get("governance") if isinstance(tree.get("governance"), dict) else {})
    governance["user_confirmed_formal_list_lock"] = {
        "applied": True,
        "action_id": action_id,
        "source": "action_bound_tree_view",
    }
    tree["governance"] = governance
    views["tree"] = tree
    locked["views"] = views

    fields_map = dict(locked.get("fields") if isinstance(locked.get("fields"), dict) else {})
    for row in tree.get("columns_schema") or []:
        if not isinstance(row, dict):
            continue
        name = str(row.get("name") or "").strip()
        if not name:
            continue
        descriptor = dict(fields_map.get(name) if isinstance(fields_map.get(name), dict) else {})
        label = str(row.get("label") or row.get("string") or descriptor.get("string") or name)
        descriptor.update({
            "name": name,
            "string": label,
            "label": label,
            "type": row.get("type") or descriptor.get("type") or "char",
        })
        fields_map[name] = descriptor
    locked["fields"] = fields_map

    columns = [str(col or "").strip() for col in tree.get("columns") or [] if str(col or "").strip()]
    if columns:
        locked["list_profile"] = {
            **(locked.get("list_profile") if isinstance(locked.get("list_profile"), dict) else {}),
            "columns": columns,
            "column_labels": {
                str(row.get("name") or ""): str(row.get("label") or row.get("string") or row.get("name") or "")
                for row in tree.get("columns_schema") or []
                if isinstance(row, dict) and str(row.get("name") or "").strip()
            },
            "preference_policy": {
                "allow_visibility": False,
                "allow_order": False,
                "locked_columns": columns,
                "must_request_columns": columns,
            },
        }
    return locked

