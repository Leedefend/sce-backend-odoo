# -*- coding: utf-8 -*-
from __future__ import annotations

import json
import xml.etree.ElementTree as ET

from odoo import SUPERUSER_ID, api, fields


ENTRY_FIELDS = {"source_created_by", "source_created_at"}
ENTRY_LABEL_BY_FIELD = {
    "source_created_by": "录入人",
    "source_created_at": "录入时间",
}


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


def _field_name(value):
    if isinstance(value, dict):
        return str(value.get("name") or value.get("field") or value.get("id") or "").strip()
    return str(value or "").strip()


def _tree_has_entry_surface(arch):
    if not arch:
        return False
    if "source_created_by" in arch and "source_created_at" in arch:
        return True
    try:
        root = ET.fromstring(arch)
    except Exception:
        return False
    labels = {
        str(node.get("string") or "").strip()
        for node in root.findall(".//field")
        if str(node.get("string") or "").strip()
    }
    return "录入人" in labels and "录入时间" in labels


def _model_has_tree_entry_surface(env, model_name):
    View = env["ir.ui.view"].sudo()
    for view in View.search([("model", "=", model_name), ("type", "=", "tree")]):
        if str(view.name or "").startswith("formal.entry.metadata."):
            continue
        if _tree_has_entry_surface(view.arch_db or ""):
            return True
    return False


def _field_label(env, model_name, field_name, item):
    if isinstance(item, dict):
        label = str(item.get("label") or item.get("string") or "").strip()
        if label:
            return label
    if not model_name or model_name not in env:
        return ""
    try:
        meta = env[model_name].sudo().fields_get([field_name]).get(field_name) or {}
    except Exception:
        return ""
    return str(meta.get("string") or "").strip()


def _dedupe_entry_columns(env, model_name, columns):
    if not isinstance(columns, list):
        return columns, False
    labels_by_name = {
        _field_name(item): _field_label(env, model_name, _field_name(item), item)
        for item in columns
        if _field_name(item)
    }
    next_columns = []
    changed = False
    for item in columns:
        name = _field_name(item)
        if name in ENTRY_FIELDS:
            expected_label = ENTRY_LABEL_BY_FIELD[name]
            has_business_peer = any(
                other_name != name and expected_label in (other_label or "")
                for other_name, other_label in labels_by_name.items()
            )
            if has_business_peer:
                changed = True
                continue
        next_columns.append(item)
    return next_columns, changed


def _sanitize_tree_payload(env, model_name, payload):
    if isinstance(payload, list):
        next_items = []
        changed = False
        for item in payload:
            next_item, item_changed = _sanitize_tree_payload(env, model_name, item)
            next_items.append(next_item)
            changed = changed or item_changed
        return next_items, changed
    if not isinstance(payload, dict):
        return payload, False

    next_payload = dict(payload)
    changed = False
    for key in ("columns", "columns_schema", "read_fields"):
        if key not in next_payload:
            continue
        next_values, key_changed = _dedupe_entry_columns(env, model_name, next_payload.get(key))
        if key_changed:
            next_payload[key] = next_values
            changed = True

    for key, value in list(next_payload.items()):
        if key in ("columns", "columns_schema", "read_fields"):
            continue
        next_value, value_changed = _sanitize_tree_payload(env, model_name, value)
        if value_changed:
            next_payload[key] = next_value
            changed = True
    return next_payload, changed


def _pin_material_plan_action(env):
    action = env.ref("smart_construction_core.action_project_material_plan", raise_if_not_found=False)
    tree_view = env.ref("smart_construction_core.view_project_material_plan_user_confirmed_tree", raise_if_not_found=False)
    form_view = env.ref("smart_construction_core.view_project_material_plan_form", raise_if_not_found=False)
    if not action or not tree_view:
        return False
    action.write(
        {
            "view_id": tree_view.id,
            "view_ids": [
                (5, 0, 0),
                (0, 0, {"view_mode": "tree", "view_id": tree_view.id}),
                (0, 0, {"view_mode": "form", "view_id": form_view.id if form_view else False}),
            ],
        }
    )
    return True


def migrate(cr, version):
    env = api.Environment(cr, SUPERUSER_ID, {})
    updates = {"material_plan_action": 0, "metadata_tree_views": 0, "contracts": 0}

    if _pin_material_plan_action(env):
        updates["material_plan_action"] += 1

    View = env["ir.ui.view"].sudo()
    generated_views = View.search([
        ("name", "=like", "formal.entry.metadata.%.tree.%"),
        ("type", "=", "tree"),
        ("inherit_id", "!=", False),
    ])
    for view in generated_views:
        if _model_has_tree_entry_surface(env, view.model):
            view.unlink()
            updates["metadata_tree_views"] += 1

    Contract = env["ui.business.config.contract"].sudo().with_context(active_test=False)
    contracts = Contract.search([
        ("view_type", "in", ["tree", "list"]),
        ("contract_json", "!=", False),
    ])
    for rec in contracts:
        payload, changed = _sanitize_tree_payload(env, rec.model, _payload(rec.contract_json))
        if not changed:
            continue
        rec.write(
            {
                "contract_json": payload,
                "version_no": int(rec.version_no or 1) + 1,
                "published_at": fields.Datetime.now() if rec.status == "published" else rec.published_at,
            }
        )
        updates["contracts"] += 1

    print(
        "[17.0.0.63] formal list entry metadata deduped: material_plan_action=%s metadata_tree_views=%s contracts=%s"
        % (updates["material_plan_action"], updates["metadata_tree_views"], updates["contracts"])
    )
