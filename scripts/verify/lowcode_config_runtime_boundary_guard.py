# -*- coding: utf-8 -*-
"""Verify low-code configuration boundaries against a live Odoo database."""

from __future__ import annotations

import json
import os

from odoo.addons.smart_core.utils.backend_contract_boundaries import (
    LOWCODE_SOURCE_STATUS_DEVELOPER_DRAFT,
    LOWCODE_SOURCE_STATUS_PRODUCT_RELEASE,
    LOWCODE_SOURCE_STATUS_TENANT_RUNTIME,
    LOWCODE_SYSTEM_CONFIG_MENU_XMLIDS,
    menu_orchestration_source_status,
    normalize_lowcode_source_status,
    view_orchestration_source_status,
)
from odoo.addons.smart_core.model.ui_menu_config_policy import (
    LOWCODE_SYSTEM_CONFIG_MENU_XMLIDS_PARAM,
)
from odoo.addons.smart_core.utils.extension_hooks import call_extension_hook_first


def _split_xmlid_list(raw) -> set[str]:
    if isinstance(raw, str):
        values = raw.split(",")
    elif isinstance(raw, (list, tuple, set, frozenset)):
        values = raw
    else:
        values = ()
    return {str(value or "").strip() for value in values if str(value or "").strip()}


def _env():
    return globals()["env"]


def _ref(env_obj, xmlid: str):
    return env_obj.ref(xmlid, raise_if_not_found=False)


def _visible_menu_ids(env_obj, user) -> set[int]:
    user_env = env_obj(user=user.id)
    menu_model = user_env["ir.ui.menu"]
    try:
        return {int(menu_id) for menu_id in menu_model._visible_menu_ids(debug=False)}
    except TypeError:
        return {int(menu_id) for menu_id in menu_model._visible_menu_ids()}


def _lowcode_system_config_menu_xmlids(env_obj) -> set[str]:
    xmlids = set(LOWCODE_SYSTEM_CONFIG_MENU_XMLIDS)
    hook_xmlids = call_extension_hook_first(env_obj, "smart_core_lowcode_system_config_menu_xmlids", env_obj)
    xmlids.update(_split_xmlid_list(hook_xmlids))
    try:
        raw = env_obj["ir.config_parameter"].sudo().get_param(LOWCODE_SYSTEM_CONFIG_MENU_XMLIDS_PARAM, "") or ""
    except Exception:
        raw = ""
    xmlids.update(_split_xmlid_list(raw))
    return xmlids


def _lowcode_global_config_entry_xmlids(env_obj, system_xmlids: set[str]) -> set[str]:
    recovery_parent = call_extension_hook_first(env_obj, "smart_core_lowcode_config_recovery_parent_menu_xmlids", env_obj)
    recovery_parent_xmlids = _split_xmlid_list(recovery_parent)
    if not recovery_parent_xmlids:
        recovery_parent_xmlids = {xmlid for xmlid in system_xmlids if xmlid.endswith(".menu_sc_business_config_center")}
    return set(system_xmlids) - recovery_parent_xmlids


def _menu_orchestration_source_status(payload: dict) -> tuple[str, bool]:
    orchestration = payload.get("menu_orchestration") if isinstance(payload.get("menu_orchestration"), dict) else {}
    explicit = str(orchestration.get("source_status") or "").strip()
    if explicit:
        return normalize_lowcode_source_status(explicit), True
    return menu_orchestration_source_status(payload), False


def _view_orchestration_has_explicit_source_status(payload: dict) -> bool:
    orchestration = payload.get("view_orchestration") if isinstance(payload.get("view_orchestration"), dict) else {}
    context = orchestration.get("context") if isinstance(orchestration.get("context"), dict) else {}
    return bool(str(context.get("source_status") or "").strip())


def _contract_status(payload: dict) -> tuple[str, bool, str]:
    if isinstance(payload.get("menu_orchestration"), dict):
        status, explicit = _menu_orchestration_source_status(payload)
        return status, explicit, "menu_orchestration"
    if isinstance(payload.get("view_orchestration"), dict):
        return view_orchestration_source_status(payload), _view_orchestration_has_explicit_source_status(payload), "view_orchestration"
    return LOWCODE_SOURCE_STATUS_PRODUCT_RELEASE, False, "unknown"


def main() -> int:
    env_obj = _env()
    strict_source_status = os.getenv("LOWCODE_CONFIG_RUNTIME_SOURCE_STATUS_STRICT", "").strip() in {"1", "true", "True"}
    errors: list[dict] = []
    warnings: list[dict] = []
    system_config_xmlids = _lowcode_system_config_menu_xmlids(env_obj)
    global_config_entry_xmlids = _lowcode_global_config_entry_xmlids(env_obj, system_config_xmlids)
    admin_xmlids = (
        "smart_core.group_smart_core_admin",
        "smart_core.group_smart_core_business_config_admin",
        "smart_construction_core.group_sc_cap_business_config_admin",
    )
    admin_groups = [group for group in (_ref(env_obj, xmlid) for xmlid in admin_xmlids) if group]
    admin_group_ids = {int(group.id) for group in admin_groups}
    system_menus = [
        (xmlid, menu)
        for xmlid in sorted(system_config_xmlids)
        for menu in [_ref(env_obj, xmlid)]
        if menu
    ]
    system_menu_ids = {int(menu.id): xmlid for xmlid, menu in system_menus}
    global_config_menu_ids = {
        menu_id: xmlid
        for menu_id, xmlid in system_menu_ids.items()
        if xmlid in global_config_entry_xmlids
    }

    User = env_obj["res.users"].sudo()
    domain = [("active", "=", True)]
    if "share" in User._fields:
        domain.append(("share", "=", False))
    users = User.search(domain, order="login")
    non_admin_visible_rows = []
    admin_visible_rows = []
    for user in users:
        user_group_ids = {int(group.id) for group in user.groups_id}
        is_config_admin = bool(user_group_ids & admin_group_ids)
        visible_ids = _visible_menu_ids(env_obj, user)
        visible_global_config_entries = sorted(
            {
                xmlid
                for menu_id, xmlid in global_config_menu_ids.items()
                if menu_id in visible_ids
            }
        )
        visible_system = sorted(
            {
                xmlid
                for menu_id, xmlid in system_menu_ids.items()
                if menu_id in visible_ids
            }
        )
        if visible_global_config_entries and not is_config_admin:
            non_admin_visible_rows.append({
                "login": str(user.login or ""),
                "visible_global_config_entries": visible_global_config_entries,
            })
        if visible_system and is_config_admin:
            admin_visible_rows.append({
                "login": str(user.login or ""),
                "visible_system_config_menus": visible_system,
            })
    if non_admin_visible_rows:
        errors.append({
            "category": "ordinary_user_system_config_visibility",
            "message": "ordinary business users must not see global low-code configuration entries",
            "users": non_admin_visible_rows[:20],
            "count": len(non_admin_visible_rows),
        })
    if system_menus and not admin_visible_rows:
        errors.append({
            "category": "admin_recovery_entry_visibility",
            "message": "at least one active configuration administrator must see a system config recovery entry",
            "system_config_menu_xmlids": sorted(system_menu_ids.values()),
        })

    status_counts: dict[str, int] = {}
    carrier_counts: dict[str, int] = {}
    missing_source_status_rows = []
    developer_draft_rows = []
    Contract = env_obj["ui.business.config.contract"].sudo()
    for rec in Contract.search([("active", "=", True), ("status", "=", "published")], order="model, name, id"):
        payload = rec.contract_json if isinstance(rec.contract_json, dict) else {}
        status, explicit, carrier = _contract_status(payload)
        status_counts[status] = status_counts.get(status, 0) + 1
        carrier_counts[carrier] = carrier_counts.get(carrier, 0) + 1
        if carrier in {"menu_orchestration", "view_orchestration"} and not explicit:
            missing_source_status_rows.append({
                "id": int(rec.id),
                "name": str(rec.name or ""),
                "model": str(rec.model or ""),
                "carrier": carrier,
                "inferred_source_status": status,
            })
        if status == LOWCODE_SOURCE_STATUS_DEVELOPER_DRAFT:
            developer_draft_rows.append({
                "id": int(rec.id),
                "name": str(rec.name or ""),
                "model": str(rec.model or ""),
                "carrier": carrier,
            })
    if missing_source_status_rows:
        legacy_payload = {
            "category": "legacy_missing_source_status",
            "message": "published config contracts without explicit source_status are tolerated as legacy but must not grow",
            "count": len(missing_source_status_rows),
            "samples": missing_source_status_rows[:20],
        }
        if strict_source_status:
            legacy_payload["message"] = "published config contracts must have explicit source_status"
            errors.append(legacy_payload)
        else:
            warnings.append(legacy_payload)
    if developer_draft_rows:
        errors.append({
            "category": "developer_draft_published_runtime",
            "message": "developer_draft contracts must not be published into runtime",
            "count": len(developer_draft_rows),
            "contracts": developer_draft_rows[:20],
        })

    report = {
        "guard": "lowcode_config_runtime_boundary_guard",
        "schema_version": "1.0",
        "database": env_obj.cr.dbname,
        "declared_system_config_menu_xmlids": sorted(system_config_xmlids),
        "declared_global_config_entry_xmlids": sorted(global_config_entry_xmlids),
        "system_config_menu_xmlids": sorted(system_menu_ids.values()),
        "global_config_entry_xmlids": sorted(global_config_menu_ids.values()),
        "active_internal_user_count": len(users),
        "config_admin_with_recovery_entry_count": len(admin_visible_rows),
        "contract_source_status_counts": dict(sorted(status_counts.items())),
        "contract_carrier_counts": dict(sorted(carrier_counts.items())),
        "strict_source_status": strict_source_status,
        "warning_count": len(warnings),
        "warnings": warnings,
        "error_count": len(errors),
        "errors": errors,
    }
    report_path = (
        os.getenv("BUSINESS_CONFIG_LOWCODE_RUNTIME_BOUNDARY_GUARD_PATH", "").strip()
        or os.getenv("LOWCODE_CONFIG_RUNTIME_BOUNDARY_GUARD_PATH", "").strip()
    )
    if report_path:
        with open(report_path, "w", encoding="utf-8") as handle:
            json.dump(report, handle, ensure_ascii=False, indent=2, sort_keys=True)
    print("[lowcode_config_runtime_boundary_guard] " + ("FAIL " if errors else "PASS ") + json.dumps(report, ensure_ascii=False, sort_keys=True))
    return 1 if errors else 0


raise SystemExit(main())
