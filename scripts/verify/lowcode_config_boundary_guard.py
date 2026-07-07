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

LOWCODE_CAPABILITY_REQUIREMENTS = {
    "menu_orchestration": {
        "source_markers": {
            "addons/smart_core/handlers/menu_configuration.py": (
                '"lowcode_boundary": "menu_config"',
                '"contract_source": MENU_ORCHESTRATION_SOURCE_TENANT_LOWCODING',
                "requested_set = {int(menu_id) for menu_id in requested_menu_ids",
            ),
            "frontend/apps/web/scripts/low_code_menu_navigation_alignment_acceptance.mjs": (
                "configuredParentId",
                "navigation_config_only",
            ),
        },
        "acceptance_targets": (
            "verify.business_config.low_code_menu_navigation_alignment",
            "verify.user_menu.reachability.guard",
        ),
        "doc_tokens": ("菜单配置", "产品导航 menu_ids", "ui.menu.config.policy"),
    },
    "form_field_structure": {
        "source_markers": {
            "addons/smart_core/handlers/form_field_configuration.py": (
                '"lowcode_boundary": "form_config"',
                "VIEW_ORCHESTRATION_SOURCE_FIELD_POLICY",
                "legacy_lowcode_draft 已停止作为保存来源",
                "_append_business_config_scope_domain",
            ),
            "addons/smart_core/model/ui_form_field_policy.py": (
                "SOURCE_KIND = \"ui_form_field_policy_overlay\"",
                "SOURCE_AUTHORITIES = (\"ui.form.field.policy\", \"ir.model.fields\", \"app.view.config\")",
                "_effective_policies",
            ),
        },
        "acceptance_targets": (
            "verify.business_config.low_code_runtime_consistency",
            "verify.business_config.low_code_group_matrix",
            "verify.business_config.low_code_layout_runtime",
        ),
        "doc_tokens": ("表单配置", "view_orchestration.views.form", "ui.form.field.policy"),
    },
    "list_search_configuration": {
        "source_markers": {
            "addons/smart_core/handlers/form_field_configuration.py": (
                "class BusinessConfigListSearchAuditHandler",
                '"user_preference_boundary": "ui_only"',
                "class BusinessConfigListSearchSetHandler",
                "class BusinessConfigListSearchBootstrapHandler",
            ),
            "scripts/verify/business_list_config_boundary_audit.py": (
                "config_authority",
                "handling_surface",
                "user_preference_boundary",
            ),
            "frontend/apps/web/scripts/low_code_business_config_acceptance.mjs": (
                "listSearchAuditBoundary",
                "userPreferenceBoundary",
                "sc.user.view.preference",
            ),
        },
        "acceptance_targets": (
            "verify.business_config.list_config_boundary",
            "verify.business_config.low_code_acceptance",
        ),
        "doc_tokens": ("列表与搜索配置", "view_orchestration.views.tree", "sc.user.view.preference"),
    },
    "approval_policy_configuration": {
        "source_markers": {
            "addons/smart_construction_core/handlers/approval_policy_configuration.py": (
                '"lowcode_boundary": "approval_policy"',
                '"policy_source": APPROVAL_POLICY_RUNTIME_SOURCE',
                "NO_BUSINESS_FACT_AUTHORITY",
            ),
            "frontend/apps/web/scripts/low_code_business_config_acceptance.mjs": (
                "approvalBoundary",
                "approvalSourceAuthority.lowcode_boundary",
                "approvalSourceAuthority.policy_source",
            ),
        },
        "acceptance_targets": (
            "verify.business_config.approval_runtime",
            "verify.business_config.low_code_acceptance",
        ),
        "doc_tokens": ("审批配置", "sc.approval.policy", "sc.approval.step"),
    },
    "version_snapshot_rollback": {
        "source_markers": {
            "addons/smart_core/handlers/business_config_surface.py": (
                "class BusinessConfigSnapshotSummaryHandler",
                "class BusinessConfigSnapshotExportHandler",
                "class BusinessConfigSnapshotCompareHandler",
            ),
            "addons/smart_core/handlers/form_field_configuration.py": (
                "class BusinessConfigContractPublishHandler",
                "class BusinessConfigContractRollbackHandler",
                "ui.business.config.contract.version",
            ),
            "scripts/verify/business_config_contract_snapshot.py": (
                "BUSINESS_CONFIG_SNAPSHOT_PATH",
                "snapshot",
            ),
        },
        "acceptance_targets": (
            "verify.business_config.snapshot",
            "verify.business_config.low_code_acceptance",
        ),
        "doc_tokens": ("配置版本管理", "ui.business.config.contract.version", "回滚"),
    },
    "capability_boundary_and_coverage": {
        "source_markers": {
            "docs/architecture/low_code_business_config_capability_matrix_v1.json": (
                "menu_orchestration",
                "form_field_structure",
                "list_search_configuration",
                "approval_policy_configuration",
                "version_snapshot_rollback",
                "capability_boundary_and_coverage",
            ),
            "scripts/verify/business_config_guard_inventory.py": (
                "EXPECTED_CAPABILITY_AUTHORING_INTENTS",
                "FULL_ACCEPTANCE_TARGETS",
                "TARGET_SOURCE_MARKER_REQUIREMENTS",
            ),
            "frontend/apps/web/scripts/low_code_business_config_acceptance.mjs": (
                "auditLowCodeBoundaryParity",
                "boundaryParity",
            ),
        },
        "acceptance_targets": (
            "verify.business_config.guard_inventory",
            "verify.business_config.coverage",
            "verify.business_config.unit",
        ),
        "doc_tokens": ("配置能力边界", "coverage", "低代码全域边界"),
    },
}

LOWCODE_BOUNDARY_DOC = ROOT / "docs" / "architecture" / "backend_contract_boundaries.md"
LOWCODE_CAPABILITY_MATRIX = ROOT / "docs" / "architecture" / "low_code_business_config_capability_matrix_v1.json"


def _load_boundaries():
    spec = importlib.util.spec_from_file_location("backend_contract_boundaries", BOUNDARY_MODULE_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _target_deps(makefile_text: str, target: str) -> set[str]:
    prefix = f"{target}:"
    for line in makefile_text.splitlines():
        if line.startswith(prefix):
            return {item.strip() for item in line[len(prefix):].split() if item.strip()}
    return set()


def _validate_lowcode_capability_matrix(errors: list[dict]) -> list[str]:
    if not LOWCODE_CAPABILITY_MATRIX.is_file():
        errors.append({
            "category": "lowcode_capability_matrix",
            "message": "low-code capability matrix is missing",
            "path": LOWCODE_CAPABILITY_MATRIX.relative_to(ROOT).as_posix(),
        })
        return []
    try:
        payload = json.loads(_read(LOWCODE_CAPABILITY_MATRIX))
    except json.JSONDecodeError as exc:
        errors.append({
            "category": "lowcode_capability_matrix",
            "message": "low-code capability matrix is invalid JSON",
            "error": str(exc),
        })
        return []
    capabilities = payload.get("capabilities") if isinstance(payload, dict) else []
    capability_ids = [
        str(item.get("id") or "").strip()
        for item in capabilities
        if isinstance(item, dict)
    ]
    missing = sorted(set(LOWCODE_CAPABILITY_REQUIREMENTS) - set(capability_ids))
    if missing:
        errors.append({
            "category": "lowcode_capability_matrix",
            "message": "low-code capability matrix must declare every guarded capability",
            "missing": missing,
        })
    return capability_ids


def _validate_lowcode_capability_boundaries(errors: list[dict]) -> list[str]:
    capability_ids = _validate_lowcode_capability_matrix(errors)
    makefile_text = _read(ROOT / "Makefile")
    full_acceptance_deps = _target_deps(makefile_text, "verify.business_config.full_acceptance")
    unit_body = makefile_text
    doc_text = _read(LOWCODE_BOUNDARY_DOC) if LOWCODE_BOUNDARY_DOC.is_file() else ""
    if not doc_text:
        errors.append({
            "category": "lowcode_boundary_document",
            "message": "backend low-code boundary document is missing or empty",
            "path": LOWCODE_BOUNDARY_DOC.relative_to(ROOT).as_posix(),
        })

    for capability_id, requirement in LOWCODE_CAPABILITY_REQUIREMENTS.items():
        for target in requirement["acceptance_targets"]:
            if target not in full_acceptance_deps and target != "verify.business_config.unit":
                errors.append({
                    "category": "lowcode_capability_acceptance",
                    "capability": capability_id,
                    "message": "capability acceptance target must be included in verify.business_config.full_acceptance",
                    "target": target,
                })
            if target == "verify.business_config.unit" and "scripts/verify/lowcode_config_boundary_guard.py" not in unit_body:
                errors.append({
                    "category": "lowcode_capability_acceptance",
                    "capability": capability_id,
                    "message": "unit chain must execute lowcode_config_boundary_guard.py",
                    "target": target,
                })
        for rel_path, markers in requirement["source_markers"].items():
            path = ROOT / rel_path
            if not path.is_file():
                errors.append({
                    "category": "lowcode_capability_marker",
                    "capability": capability_id,
                    "path": rel_path,
                    "message": "required low-code boundary artifact is missing",
                })
                continue
            text = _read(path)
            for marker in markers:
                if marker not in text:
                    errors.append({
                        "category": "lowcode_capability_marker",
                        "capability": capability_id,
                        "path": rel_path,
                        "message": "required low-code boundary marker is missing",
                        "marker": marker,
                    })
        for token in requirement["doc_tokens"]:
            if token not in doc_text:
                errors.append({
                    "category": "lowcode_boundary_document",
                    "capability": capability_id,
                    "path": LOWCODE_BOUNDARY_DOC.relative_to(ROOT).as_posix(),
                    "message": "backend boundary document must define low-code capability boundary",
                    "token": token,
                })
    return capability_ids


def build_report() -> dict:
    errors: list[dict] = []
    boundaries = _load_boundaries()
    source_statuses = set(getattr(boundaries, "LOWCODE_SOURCE_STATUSES", set()))
    system_config_menu_xmlids = set(getattr(boundaries, "LOWCODE_SYSTEM_CONFIG_MENU_XMLIDS", set()))
    capability_ids = _validate_lowcode_capability_boundaries(errors)

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
    for token in (
        "LOWCODE_SYSTEM_CONFIG_MENU_XMLIDS_PARAM",
        "smart_core_lowcode_system_config_menu_xmlids",
        "call_extension_hook_first",
        "_lowcode_system_config_menu_xmlids",
    ):
        if token not in runtime_text:
            errors.append({
                "category": "runtime_protection",
                "message": "menu runtime overlay must load protected config menus through platform-neutral extension/config sources",
                "token": token,
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

    construction_extension_text = _read(ROOT / "addons" / "smart_construction_core" / "core_extension.py")
    construction_init_text = _read(ROOT / "addons" / "smart_construction_core" / "__init__.py")
    for token in (
        "def smart_core_lowcode_system_config_menu_xmlids",
        "smart_construction_core.menu_sc_business_config_center",
        "smart_construction_core.menu_sc_business_config_workbench",
        "smart_construction_core.menu_ui_menu_config_policy_business_config",
    ):
        if token not in construction_extension_text:
            errors.append({
                "category": "industry_lowcode_config_recovery_hook",
                "message": "industry module must declare its own low-code protected config recovery menus",
                "token": token,
            })
    if "smart_core_lowcode_system_config_menu_xmlids" not in construction_init_text:
        errors.append({
            "category": "industry_lowcode_config_recovery_hook",
            "message": "industry module must export the low-code protected config recovery menu hook",
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
    for token in (
        "requested_set = {int(menu_id) for menu_id in requested_menu_ids",
        "if requested_set:",
        '("menu_id", "in", sorted(candidate_ids))',
    ):
        if token not in menu_handler_text:
            errors.append({
                "category": "menu_config_navigation_boundary",
                "message": "menu config panel must be constrained by current product navigation menu_ids before falling back to root subtree",
                "token": token,
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
        "capabilities": sorted(capability_ids),
        "guarded_capability_count": len(LOWCODE_CAPABILITY_REQUIREMENTS),
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
