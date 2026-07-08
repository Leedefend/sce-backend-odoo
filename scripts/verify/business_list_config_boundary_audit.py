# -*- coding: utf-8 -*-
"""Audit published business list configs against the user-facing list surface.

Run inside Odoo shell:
  ENV=dev DB_NAME=sc_demo make verify.business_config.list_config_boundary
"""

import json
import os

from odoo import api
from odoo.exceptions import UserError

from odoo.addons.smart_core.handlers.form_field_configuration import (
    BusinessConfigListSearchAuditHandler,
    _view_orchestration_field_names,
)
from odoo.addons.smart_core.handlers.ui_contract_v2 import UiContractV2Handler


def _env():
    return globals()["env"]


def _unwrap(result):
    if hasattr(result, "to_legacy_dict"):
        return result.to_legacy_dict()
    return result if isinstance(result, dict) else {}


def _ref_id(value):
    try:
        return int(getattr(value, "id", 0) or 0)
    except Exception:
        try:
            return int(value or 0)
        except Exception:
            return 0


def _text(value):
    return str(value or "").strip()


def _contract_columns(record):
    return _view_orchestration_field_names(record.contract_json or {}, "tree")


def _configured_action_keys(env_obj):
    Contract = env_obj["ui.business.config.contract"].sudo()
    contracts = Contract.search([("status", "=", "published"), ("view_type", "in", ["tree", "list"])], order="id")
    keys = {}
    for record in contracts:
        columns = _contract_columns(record)
        model = _text(record.model)
        action_id = _ref_id(record.action_id)
        view_id = _ref_id(record.view_id)
        role_key = _text(record.role_key)
        if not columns or not model or not action_id:
            continue
        key = (model, action_id, view_id, role_key)
        keys[key] = {
            "model": model,
            "action_id": action_id,
            "view_id": view_id,
            "role_key": role_key,
        }
    return contracts, keys


def _config_surface_profile(env_obj, *, model, action_id, view_id, role_key):
    result = _unwrap(BusinessConfigListSearchAuditHandler(
        env=env_obj,
        payload={
            "model": model,
            "action_id": action_id,
            "view_id": view_id,
            "role_key": role_key,
        },
    ).handle())
    if not result.get("ok"):
        raise UserError("列表配置审计失败：%s action_id=%s" % (model, action_id))
    data = result.get("data") or {}
    columns = list(data.get("business_config_list_columns") or [])
    labels = data.get("business_config_list_column_labels") if isinstance(data.get("business_config_list_column_labels"), dict) else {}
    return columns, {name: _text(labels.get(name) or name) for name in columns}


def _handling_surface_profile(env_obj, *, model, action_id):
    env_obj = api.Environment(env_obj.cr, env_obj.uid, dict(env_obj.context or {}))
    payload = {
        "action_id": action_id,
        "model": model,
        "view_type": "list",
        "op": "model",
    }
    result = _unwrap(UiContractV2Handler(env=env_obj, payload=payload).handle(payload, None))
    if not result.get("ok"):
        raise UserError("办理面契约生成失败：%s action_id=%s" % (model, action_id))
    data = result.get("data") or {}
    layout = data.get("layoutContract") if isinstance(data.get("layoutContract"), dict) else {}
    profile = layout.get("listProfile") if isinstance(layout.get("listProfile"), dict) else {}
    columns = list(profile.get("columns") or [])
    labels = profile.get("column_labels") if isinstance(profile.get("column_labels"), dict) else {}
    return columns, {name: _text(labels.get(name) or name) for name in columns}


TECHNICAL_FIELD_PREFIXES = ("p1_visible_", "legacy_visible_", "accepted_visible_", "user_acceptance_")
EXPLICIT_HISTORY_CARRIER_FIELDS = {
    "legacy_attachment_ref",
    "legacy_line_attachment_ref",
    "legacy_attachment_name",
    "legacy_attachment_path",
    "creator_legacy_user_id",
    "legacy_residual_reason",
}


def _name_leaks_history_carrier(field_name):
    name = _text(field_name)
    return name in EXPLICIT_HISTORY_CARRIER_FIELDS


def _label_leaks_technical_identity(field_name, label):
    name = _text(field_name)
    text = _text(label)
    if _name_leaks_history_carrier(name):
        return True
    if not text:
        return True
    if text == name:
        return name.startswith(TECHNICAL_FIELD_PREFIXES) or _name_leaks_history_carrier(name)
    return text.startswith(TECHNICAL_FIELD_PREFIXES + ("P1可见",)) or text in EXPLICIT_HISTORY_CARRIER_FIELDS


def _view_modes(action):
    return [item.strip() for item in str(action.view_mode or "").split(",") if item.strip()]


def _audit(env_obj):
    contracts, keys = _configured_action_keys(env_obj)
    Action = env_obj["ir.actions.act_window"].sudo()
    checked = []
    mismatches = []
    skipped = []
    errors = []
    for key, item in sorted(keys.items(), key=lambda row: (row[0][1], row[0][0], row[0][2], row[0][3])):
        action = Action.browse(item["action_id"])
        if not action.exists():
            skipped.append({**item, "reason": "action_missing"})
            continue
        action_model = _text(getattr(action, "res_model", ""))
        if action_model and action_model != item["model"]:
            skipped.append({
                **item,
                "name": _text(action.name),
                "action_model": action_model,
                "reason": "action_model_mismatch",
            })
            continue
        modes = _view_modes(action)
        if modes and modes[0] not in {"tree", "list"}:
            skipped.append({
                **item,
                "name": _text(action.name),
                "view_mode": _text(action.view_mode),
                "reason": "default_not_list",
            })
            continue
        try:
            surface_columns, surface_labels = _handling_surface_profile(
                env_obj,
                model=item["model"],
                action_id=item["action_id"],
            )
            config_columns, config_labels = _config_surface_profile(env_obj, **item)
            label_mismatches = [
                {
                    "field": name,
                    "config_label": config_labels.get(name),
                    "surface_label": surface_labels.get(name),
                }
                for name in config_columns
                if config_labels.get(name) != surface_labels.get(name)
            ]
            label_leaks = [
                {
                    "field": name,
                    "config_label": config_labels.get(name),
                    "surface_label": surface_labels.get(name),
                }
                for name in config_columns
                if _label_leaks_technical_identity(name, config_labels.get(name))
            ]
            row = {
                **item,
                "name": _text(action.name),
                "view_mode": _text(action.view_mode),
                "config_count": len(config_columns),
                "surface_count": len(surface_columns),
                "label_mismatch_count": len(label_mismatches),
                "label_leak_count": len(label_leaks),
            }
            checked.append(row)
            if config_columns != surface_columns or label_mismatches or label_leaks:
                row.update({
                    "missing_in_surface": [name for name in config_columns if name not in surface_columns],
                    "extra_in_surface": [name for name in surface_columns if name not in config_columns],
                    "config_head": config_columns[:8],
                    "surface_head": surface_columns[:8],
                    "config_label_head": {name: config_labels.get(name) for name in config_columns[:8]},
                    "surface_label_head": {name: surface_labels.get(name) for name in surface_columns[:8]},
                    "label_mismatches": label_mismatches[:20],
                    "label_leaks": label_leaks[:20],
                })
                mismatches.append(row)
        except Exception as exc:
            errors.append({
                **item,
                "name": _text(action.name),
                "error": repr(exc),
            })
    return {
        "database": env_obj.cr.dbname,
        "published_tree_contracts": len(contracts),
        "unique_configured_action_keys": len(keys),
        "checked_list_actions": len(checked),
        "exact_matches": len(checked) - len(mismatches),
        "mismatches": len(mismatches),
        "skipped_non_list_or_missing": len(skipped),
        "errors": len(errors),
        "mismatch_items": mismatches,
        "skipped_sample": skipped[:50],
        "error_items": errors[:50],
        "boundary": {
            "config_authority": "ui.business.config.contract.view_orchestration.views.tree.columns",
            "config_surface": "BusinessConfigListSearchAuditHandler.business_config_list_columns + business_config_list_column_labels",
            "handling_surface": "ui.contract.v2.layoutContract.listProfile.columns + column_labels",
            "user_visible_label_boundary": "configured list labels must match handling surface labels; explicit history carriers are forbidden, and transition aliases must not expose technical labels",
            "user_preference_boundary": "sc.user.view.preference is ui_only",
        },
    }


def main():
    env_obj = _env()
    report = _audit(env_obj)
    report_path = os.getenv("BUSINESS_LIST_CONFIG_BOUNDARY_REPORT_PATH", "/tmp/business_list_config_boundary_audit.json")
    if report_path:
        report_dir = os.path.dirname(report_path)
        if report_dir:
            os.makedirs(report_dir, exist_ok=True)
        with open(report_path, "w", encoding="utf-8") as handle:
            json.dump(report, handle, ensure_ascii=False, indent=2)
            handle.write("\n")
    failed = report["mismatches"] or report["errors"]
    print("[business_list_config_boundary_audit] %s checked=%s mismatches=%s errors=%s skipped=%s" % (
        "FAIL" if failed else "PASS",
        report["checked_list_actions"],
        report["mismatches"],
        report["errors"],
        report["skipped_non_list_or_missing"],
    ))
    print(json.dumps(report, ensure_ascii=False, indent=2))
    if failed:
        raise UserError("业务列表配置与办理面字段不一致")


main()
