#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

import importlib.util
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
BOUNDARY_MODULE_PATH = ROOT / "addons" / "smart_core" / "utils" / "backend_contract_boundaries.py"

REQUIRED_SOURCE_STATUSES = {
    "developer_draft",
    "tenant_runtime",
    "product_release",
}
REQUIRED_SYSTEM_CONFIG_MENU_XMLIDS: set[str] = set()
REQUIRED_GLOBAL_CONFIG_MENU_GROUPS = {
    "smart_construction_core.group_sc_cap_business_config_admin",
    "smart_core.group_smart_core_business_config_admin",
    "smart_core.group_smart_core_admin",
}
REQUIRED_PLATFORM_CONFIG_ACTION_GROUPS = {
    "smart_core.group_smart_core_business_config_admin",
    "smart_core.group_smart_core_admin",
}
GLOBAL_CONFIG_ENTRY_FILES = {
    "business_config_workbench": (
        ROOT / "addons" / "smart_construction_core" / "views" / "support" / "business_config_workbench_views.xml",
        REQUIRED_GLOBAL_CONFIG_MENU_GROUPS,
    ),
    "menu_config_policy_menu": (
        ROOT / "addons" / "smart_construction_core" / "views" / "support" / "menu_config_policy_views.xml",
        REQUIRED_GLOBAL_CONFIG_MENU_GROUPS,
    ),
    "menu_config_policy_action": (
        ROOT / "addons" / "smart_core" / "views" / "ui_menu_config_policy_views.xml",
        REQUIRED_PLATFORM_CONFIG_ACTION_GROUPS,
    ),
}
REQUIRED_DOC_FILES = [
    ROOT / "docs" / "product" / "formal_product_boundary_v1.md",
    ROOT / "docs" / "low_code_config_capability_matrix.md",
]


def _load_boundaries():
    spec = importlib.util.spec_from_file_location("backend_contract_boundaries", BOUNDARY_MODULE_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def build_report() -> dict:
    errors: list[dict] = []
    boundaries = _load_boundaries()
    source_statuses = set(getattr(boundaries, "LOWCODE_SOURCE_STATUSES", set()))
    system_config_menu_xmlids = set(getattr(boundaries, "LOWCODE_SYSTEM_CONFIG_MENU_XMLIDS", set()))

    missing_statuses = sorted(REQUIRED_SOURCE_STATUSES - source_statuses)
    if missing_statuses:
        errors.append({
            "category": "source_status",
            "message": "missing low-code source status constants",
            "missing": missing_statuses,
        })

    missing_system_config_menus = sorted(REQUIRED_SYSTEM_CONFIG_MENU_XMLIDS - system_config_menu_xmlids)
    if missing_system_config_menus:
        errors.append({
            "category": "system_config_menu",
            "message": "missing protected system config menu xmlids",
            "missing": missing_system_config_menus,
        })

    runtime_text = _read(ROOT / "addons" / "smart_core" / "model" / "ui_menu_config_policy.py")
    if "LOWCODE_SYSTEM_CONFIG_MENU_XMLIDS" not in runtime_text:
        errors.append({
            "category": "runtime_protection",
            "message": "menu runtime overlay must use LOWCODE_SYSTEM_CONFIG_MENU_XMLIDS",
        })

    boundary_text = _read(BOUNDARY_MODULE_PATH)
    if "ensure_lowcode_contract_source_status" not in boundary_text:
        errors.append({
            "category": "source_status_backfill_helper",
            "message": "low-code boundary helper must support explicit source_status backfill",
        })

    hook_text = _read(ROOT / "addons" / "smart_construction_core" / "hooks.py")
    if "_backfill_lowcode_contract_source_status" not in hook_text:
        errors.append({
            "category": "fresh_install_source_status_backfill",
            "message": "fresh installs must backfill explicit low-code source_status",
        })

    custom_hook_text = _read(ROOT / "addons" / "smart_construction_custom" / "hooks.py")
    if "backfill_lowcode_contract_source_status" not in custom_hook_text:
        errors.append({
            "category": "custom_fresh_install_source_status_backfill",
            "message": "custom fresh installs must backfill explicit low-code source_status after user preferences",
        })

    custom_user_pref_text = _read(ROOT / "addons" / "smart_construction_custom" / "models" / "user_preferences.py")
    if "ensure_lowcode_contract_source_status" not in custom_user_pref_text:
        errors.append({
            "category": "custom_user_preference_source_status",
            "message": "custom user preference contracts must stamp explicit source_status when generated",
        })

    migration_text = _read(ROOT / "addons" / "smart_construction_core" / "migrations" / "17.0.0.59" / "post-migration.py")
    if "ensure_lowcode_contract_source_status" not in migration_text:
        errors.append({
            "category": "upgrade_source_status_backfill",
            "message": "module upgrades must backfill explicit low-code source_status",
        })

    custom_migration_text = _read(ROOT / "addons" / "smart_construction_custom" / "migrations" / "17.0.1.1" / "post-migration.py")
    if "ensure_lowcode_contract_source_status" not in custom_migration_text:
        errors.append({
            "category": "custom_upgrade_source_status_backfill",
            "message": "custom module upgrades must backfill explicit low-code source_status",
        })

    makefile_text = _read(ROOT / "Makefile")
    if "LOWCODE_CONFIG_RUNTIME_SOURCE_STATUS_STRICT=1" not in makefile_text:
        errors.append({
            "category": "runtime_source_status_strict_gate",
            "message": "product surface gate must enforce explicit low-code source_status",
        })

    shell_exec_text = _read(ROOT / "scripts" / "ops" / "odoo_shell_exec.sh")
    if "LOWCODE_*" not in shell_exec_text:
        errors.append({
            "category": "runtime_source_status_strict_env_forward",
            "message": "Odoo shell runner must forward LOWCODE_* strict gate environment variables",
        })

    for key, (path, required_groups) in GLOBAL_CONFIG_ENTRY_FILES.items():
        text = _read(path)
        missing_groups = sorted(group for group in required_groups if group not in text)
        if missing_groups:
            errors.append({
                "category": "global_config_entry_groups",
                "path": path.relative_to(ROOT).as_posix(),
                "entry": key,
                "message": "global low-code config entries must be limited to configuration administrator groups",
                "missing_groups": missing_groups,
            })

    menu_handler_text = _read(ROOT / "addons" / "smart_core" / "handlers" / "menu_configuration.py")
    if "source_status" not in menu_handler_text or "LOWCODE_SOURCE_STATUS_TENANT_RUNTIME" not in menu_handler_text:
        errors.append({
            "category": "menu_contract_source_status",
            "message": "menu orchestration contracts must stamp tenant_runtime source_status",
        })

    form_handler_text = _read(ROOT / "addons" / "smart_core" / "handlers" / "form_field_configuration.py")
    if "LOWCODE_SOURCE_STATUS_TENANT_RUNTIME" not in form_handler_text:
        errors.append({
            "category": "view_contract_source_status",
            "message": "view orchestration low-code writers must stamp tenant_runtime source_status",
        })

    for path in REQUIRED_DOC_FILES:
        text = _read(path)
        for token in sorted(REQUIRED_SOURCE_STATUSES):
            if token not in text:
                errors.append({
                    "category": "doc_source_status",
                    "path": str(path.relative_to(ROOT)),
                    "message": "document must define low-code source status",
                    "token": token,
                })
        for token in ("系统配置入口", "产品发布菜单", "用户/租户配置菜单"):
            if token not in text:
                errors.append({
                    "category": "doc_menu_boundary",
                    "path": str(path.relative_to(ROOT)),
                    "message": "document must define menu object boundary",
                    "token": token,
                })

    return {
        "guard": "lowcode_config_boundary_guard",
        "schema_version": "1.0",
        "source_statuses": sorted(source_statuses),
        "system_config_menu_xmlids": sorted(system_config_menu_xmlids),
        "error_count": len(errors),
        "errors": errors,
    }


def main() -> int:
    report = build_report()
    print(json.dumps(report, ensure_ascii=False, sort_keys=True))
    if report["error_count"]:
        print("[lowcode_config_boundary_guard] FAIL")
        return 1
    print("[lowcode_config_boundary_guard] PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
