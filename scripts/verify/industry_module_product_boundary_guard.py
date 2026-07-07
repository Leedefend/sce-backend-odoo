#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

import ast
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
ADDONS = ROOT / "addons"

INDUSTRY_MODULES = (
    "smart_construction_bootstrap",
    "smart_construction_bundle",
    "smart_construction_core",
    "smart_construction_custom",
    "smart_construction_portal",
    "smart_construction_scene",
    "smart_construction_seed",
)

# Source assets intentionally carried but not loaded by manifests.
ALLOWED_UNDECLARED_XML = {
    "smart_construction_core": {
        "data/tax.xml": "empty compatibility stub; taxes are created idempotently by hooks.ensure_core_taxes",
        "views/res_users_views.xml": "legacy user-form experiment; enterprise/user module owns user profile surface",
        "views/support/partner_acceptance_product_menu_policy.xml": "historical acceptance policy; not part of formal runtime menu policy",
    },
    "smart_construction_custom": {
        "data/user_master_v1.xml": "real legacy user payload; loaded only by idempotent baseline loader",
    },
    "smart_construction_seed": {
        "data/sc_seed_login_env.xml": "demo login flag; seed hook gates demo mode explicitly",
        "data/sc_seed_partner.xml": "demo partner seed; demo steps must run through the guarded seed registry",
    },
}

FORBIDDEN_MANIFEST_XML = {
    "smart_construction_core": {
        "views/res_users_views.xml",
        "views/support/partner_acceptance_product_menu_policy.xml",
    },
    "smart_construction_custom": {
        "data/user_master_v1.xml",
    },
    "smart_construction_seed": {
        "data/sc_seed_login_env.xml",
        "data/sc_seed_partner.xml",
    },
}

FORBIDDEN_PRODUCTION_TOKENS = {
    "smart_construction_core": ("smart_construction_demo.", "sc_demo", "Demo-", "演示项目"),
    "smart_construction_bundle": ("smart_construction_demo.", "sc_demo", "Demo-", "演示项目"),
    "smart_construction_portal": ("smart_construction_demo.", "sc_demo", "Demo-", "演示项目"),
    "smart_construction_scene": ("smart_construction_demo.", "sc_demo", "Demo-", "演示项目", "（演示）"),
}

ASSET_DIRS = ("data", "security", "views", "actions", "wizard")
ASSET_SUFFIXES = (".xml", ".csv")
REQUIRED_PACKAGE_DIRS = (
    "smart_construction_core/handlers",
    "smart_construction_scene/policies",
    "smart_construction_scene/profiles",
    "smart_construction_scene/providers",
)
PORTAL_EXECUTE_LEGACY_ALLOWLIST = {
    "addons/smart_construction_core/models/support/portal_execute.py",
    "addons/smart_construction_core/services/portal_execute_button_service.py",
}


def _manifest(module: str) -> dict:
    path = ADDONS / module / "__manifest__.py"
    if not path.is_file():
        raise FileNotFoundError(path)
    return ast.literal_eval(path.read_text(encoding="utf-8"))


def _module_assets(module: str) -> set[str]:
    base = ADDONS / module
    files: set[str] = set()
    for dirname in ASSET_DIRS:
        directory = base / dirname
        if not directory.exists():
            continue
        for path in directory.rglob("*"):
            if path.is_file() and path.suffix in ASSET_SUFFIXES:
                files.add(path.relative_to(base).as_posix())
    return files


def _manifest_data(module: str) -> list[str]:
    manifest = _manifest(module)
    return [str(item) for item in manifest.get("data", [])]


def verify_manifest_shape() -> list[str]:
    errors: list[str] = []
    for module in INDUSTRY_MODULES:
        base = ADDONS / module
        data_files = _manifest_data(module)
        data_set = set(data_files)
        actual = _module_assets(module)
        allowed_undeclared = set(ALLOWED_UNDECLARED_XML.get(module, {}))

        for item in data_files:
            if not (base / item).is_file():
                errors.append(f"{module}: manifest data entry missing on disk: {item}")

        for item in sorted(actual - data_set - allowed_undeclared):
            errors.append(f"{module}: asset is neither loaded nor documented as intentionally excluded: {item}")

        for item in sorted(allowed_undeclared - actual):
            errors.append(f"{module}: allowed undeclared asset no longer exists: {item}")

        for item in sorted(FORBIDDEN_MANIFEST_XML.get(module, set()) & data_set):
            errors.append(f"{module}: forbidden production manifest asset is loaded: {item}")

    return errors


def verify_production_token_boundary() -> list[str]:
    errors: list[str] = []
    for module, tokens in FORBIDDEN_PRODUCTION_TOKENS.items():
        base = ADDONS / module
        for item in _manifest_data(module):
            path = base / item
            if not path.is_file() or path.suffix not in ASSET_SUFFIXES:
                continue
            text = path.read_text(encoding="utf-8", errors="ignore")
            for token in tokens:
                if token in text:
                    errors.append(f"{module}: loaded production asset contains demo token {token!r}: {item}")
    return errors


def verify_custom_user_payload_boundary() -> list[str]:
    errors: list[str] = []
    user_master = ADDONS / "smart_construction_custom" / "data/user_master_v1.xml"
    loader = ADDONS / "smart_construction_custom" / "models/user_data_baseline.py"
    if not user_master.is_file():
        errors.append("smart_construction_custom: missing carried legacy user master payload")
        return errors
    loader_text = loader.read_text(encoding="utf-8") if loader.is_file() else ""
    if "LEGACY_USER_MASTER_XML" not in loader_text or "user_master_v1.xml" not in loader_text:
        errors.append("smart_construction_custom: user_master_v1.xml must be referenced by the idempotent user data baseline loader")
    return errors


def verify_python_package_boundaries() -> list[str]:
    errors: list[str] = []
    for relative in REQUIRED_PACKAGE_DIRS:
        directory = ADDONS / relative
        init_file = directory / "__init__.py"
        if not directory.is_dir():
            errors.append(f"missing package directory: addons/{relative}")
        elif not init_file.is_file():
            errors.append(f"missing explicit package initializer: addons/{relative}/__init__.py")
    return errors


def verify_portal_execute_demo_boundary() -> list[str]:
    errors: list[str] = []
    service = ADDONS / "smart_construction_core" / "services/portal_execute_button_service.py"
    snapshot = ROOT / "docs/contract/snapshots/portal_execute_button_pm.json"
    service_text = service.read_text(encoding="utf-8") if service.is_file() else ""
    snapshot_text = snapshot.read_text(encoding="utf-8") if snapshot.is_file() else ""

    if 'method = method or "action_portal_demo_ping"' in service_text:
        errors.append("smart_construction_core: portal execute default method must not use action_portal_demo_ping")
    if '"portal_demo_ping"' in snapshot_text or '"action_portal_demo_ping"' in snapshot_text:
        errors.append("docs/contract: portal execute PM snapshot must use product portal ping semantics")

    for path in (ADDONS / "smart_construction_core").rglob("*.py"):
        relative = path.relative_to(ROOT).as_posix()
        text = path.read_text(encoding="utf-8", errors="ignore")
        if "action_portal_demo_ping" not in text:
            continue
        if relative not in PORTAL_EXECUTE_LEGACY_ALLOWLIST:
            errors.append(f"smart_construction_core: legacy portal demo method leaks outside compatibility layer: {relative}")
    return errors


def verify_static_navigation_product_labels() -> list[str]:
    errors: list[str] = []
    nav_map = ADDONS / "smart_construction_core" / "static/src/config/domain_nav_map.js"
    text = nav_map.read_text(encoding="utf-8") if nav_map.is_file() else ""
    if 'tag: "试点"' in text or "tag: '试点'" in text:
        errors.append("smart_construction_core: pinned navigation entries must not be labeled as pilot")
    return errors


def verify_capability_registry_role_boundary() -> list[str]:
    errors: list[str] = []
    registry = ADDONS / "smart_construction_core" / "services/capability_registry.py"
    text = registry.read_text(encoding="utf-8") if registry.is_file() else ""
    for token in ("demo_pm", "demo_finance", "demo_role_executive"):
        if token in text:
            errors.append(f"smart_construction_core: capability roles must come from groups, not demo login token {token!r}")
    return errors


def verify_handler_product_language_boundary() -> list[str]:
    errors: list[str] = []
    handlers_dir = ADDONS / "smart_construction_core" / "handlers"
    forbidden_tokens = ("这里演示", "demo ping", "演示", "试点")
    for path in handlers_dir.rglob("*.py"):
        text = path.read_text(encoding="utf-8", errors="ignore")
        for token in forbidden_tokens:
            if token in text:
                errors.append(
                    "smart_construction_core: handler product code contains demo-oriented wording "
                    f"{token!r}: {path.relative_to(ROOT).as_posix()}"
                )
    return errors


def verify_runtime_comment_product_language_boundary() -> list[str]:
    errors: list[str] = []
    forbidden_tokens = (
        "seed/demo",
        "demo 可提供",
        "demo xmlid",
        "demo XMLID",
        "最小可跑",
        "后续替换",
        "临时实现",
        "占位实现",
    )
    scan_roots = (
        ADDONS / "smart_construction_core" / "models",
        ADDONS / "smart_construction_core" / "services",
        ADDONS / "smart_construction_core" / "handlers",
        ADDONS / "smart_construction_scene",
        ADDONS / "smart_construction_portal",
        ADDONS / "smart_construction_custom" / "models",
    )
    excluded_parts = {"tests", "docs", "migrations", "tools", "__pycache__"}
    for root in scan_roots:
        if not root.is_dir():
            continue
        for path in root.rglob("*.py"):
            if any(part in excluded_parts for part in path.relative_to(root).parts):
                continue
            text = path.read_text(encoding="utf-8", errors="ignore")
            for token in forbidden_tokens:
                if token in text:
                    errors.append(
                        "industry modules: runtime code comments must use product seed/fixture language, "
                        f"not demo wording {token!r}: {path.relative_to(ROOT).as_posix()}"
                    )
    return errors


def verify_portal_controller_exception_observability() -> list[str]:
    path = ADDONS / "smart_construction_portal" / "controllers" / "portal_controller.py"
    if not path.is_file():
        return []
    text = path.read_text(encoding="utf-8", errors="ignore")
    if "except Exception:\n        pass" not in text:
        return []
    return [
        "smart_construction_portal: public portal controller must not silently swallow "
        "exceptions; log degraded auth/session/payload paths at debug level"
    ]


def verify_app_entry_exception_observability() -> list[str]:
    errors: list[str] = []
    guarded_paths = (
        ADDONS / "smart_construction_core" / "handlers" / "app_nav.py",
        ADDONS / "smart_construction_core" / "handlers" / "app_catalog.py",
    )
    for path in guarded_paths:
        if not path.is_file():
            continue
        text = path.read_text(encoding="utf-8", errors="ignore")
        if "except Exception:\n        pass" in text:
            errors.append(
                "smart_construction_core: app catalog/navigation entry fallbacks must log "
                f"exception degradation at debug level: {path.relative_to(ROOT).as_posix()}"
            )
    return errors


def verify_scene_governance_exception_observability() -> list[str]:
    errors: list[str] = []
    guarded_paths = (
        ADDONS / "smart_construction_scene" / "services" / "scene_governance_service.py",
        ADDONS / "smart_construction_scene" / "services" / "scene_package_service.py",
    )
    for path in guarded_paths:
        if not path.is_file():
            continue
        text = path.read_text(encoding="utf-8", errors="ignore")
        if "except Exception:\n            pass" in text:
            errors.append(
                "smart_construction_scene: scene governance/package services must log "
                f"exception degradation before fallback: {path.relative_to(ROOT).as_posix()}"
            )
    return errors


def verify_core_api_controller_exception_observability() -> list[str]:
    errors: list[str] = []
    guarded_paths = (
        ADDONS / "smart_construction_core" / "controllers" / "frontend_api.py",
        ADDONS / "smart_construction_core" / "controllers" / "execute_controller.py",
        ADDONS / "smart_construction_core" / "controllers" / "portal_execute_button_controller.py",
        ADDONS / "smart_construction_core" / "controllers" / "meta_controller.py",
    )
    for path in guarded_paths:
        if not path.is_file():
            continue
        text = path.read_text(encoding="utf-8", errors="ignore")
        if "except Exception:\n        pass" in text:
            errors.append(
                "smart_construction_core: core API controllers must log JSON/session "
                f"fallback exceptions at debug level: {path.relative_to(ROOT).as_posix()}"
            )
    return errors


def verify_business_slice_project_resolution_observability() -> list[str]:
    errors: list[str] = []
    guarded_paths = (
        ADDONS / "smart_construction_core" / "services" / "cost_tracking_service.py",
        ADDONS / "smart_construction_core" / "services" / "payment_slice_service.py",
        ADDONS / "smart_construction_core" / "services" / "project_execution_service.py",
        ADDONS / "smart_construction_core" / "services" / "project_plan_bootstrap_service.py",
        ADDONS / "smart_construction_core" / "services" / "settlement_slice_service.py",
    )
    for path in guarded_paths:
        if not path.is_file():
            continue
        text = path.read_text(encoding="utf-8", errors="ignore")
        if "def resolve_project_with_diagnostics" not in text:
            continue
        method_text = text.split("def resolve_project_with_diagnostics", 1)[1].split("\n    def ", 1)[0]
        if "except Exception:\n                pass" in method_text or "except Exception:\n            pass" in method_text:
            errors.append(
                "smart_construction_core: business slice project resolution fallbacks must log "
                f"exception degradation at debug level: {path.relative_to(ROOT).as_posix()}"
            )
    return errors


def verify_policy_capability_dashboard_exception_observability() -> list[str]:
    errors: list[str] = []
    guarded_paths = (
        ADDONS / "smart_construction_core" / "handlers" / "approval_policy_configuration.py",
        ADDONS / "smart_construction_core" / "services" / "capability_registry.py",
        ADDONS / "smart_construction_core" / "services" / "project_dashboard_service.py",
    )
    for path in guarded_paths:
        if not path.is_file():
            continue
        text = path.read_text(encoding="utf-8", errors="ignore")
        if "except Exception:\n                pass" in text or "except Exception:\n        pass" in text:
            errors.append(
                "smart_construction_core: policy/capability/dashboard degradation paths must log "
                f"exceptions at debug level: {path.relative_to(ROOT).as_posix()}"
            )
    return errors


def verify_core_model_runtime_exception_observability() -> list[str]:
    errors: list[str] = []
    guarded_paths = (
        ADDONS / "smart_construction_core" / "models" / "core" / "project_core.py",
        ADDONS / "smart_construction_core" / "models" / "support" / "scene_orchestration.py",
    )
    for path in guarded_paths:
        if not path.is_file():
            continue
        text = path.read_text(encoding="utf-8", errors="ignore")
        if "except Exception:\n                pass" in text or "except Exception:\n                    pass" in text:
            errors.append(
                "smart_construction_core: core runtime model degradation paths must log "
                f"exceptions at debug level: {path.relative_to(ROOT).as_posix()}"
            )
    return errors


def verify_core_extension_wizard_exception_observability() -> list[str]:
    errors: list[str] = []
    guarded_paths = (
        ADDONS / "smart_construction_core" / "core_extension.py",
        ADDONS / "smart_construction_core" / "wizard" / "project_boq_import_wizard.py",
    )
    for path in guarded_paths:
        if not path.is_file():
            continue
        text = path.read_text(encoding="utf-8", errors="ignore")
        if "except Exception:\n            pass" in text or "except Exception:\n                pass" in text:
            errors.append(
                "smart_construction_core: runtime extension/wizard degradation paths must log "
                f"exceptions at debug level: {path.relative_to(ROOT).as_posix()}"
            )
    return errors


def verify_runtime_pending_placeholder_language_boundary() -> list[str]:
    errors: list[str] = []
    forbidden_user_surface_tokens = (
        "样例单号",
        "来源样例",
        "技术材料占位",
        "技术产品占位",
        "技术占位",
        "缺少发票信息（占位）",
        "(placeholder)",
        "projects.dashboard_showcase",
        "/s/projects.dashboard_showcase",
        "项目驾驶舱样板",
        "showcase_overview",
        "showcase_metrics",
    )
    guarded_roots = (
        ADDONS / "smart_construction_core" / "models",
        ADDONS / "smart_construction_core" / "data",
        ADDONS / "smart_construction_core" / "views",
        ADDONS / "smart_construction_core" / "wizard",
        ADDONS / "smart_construction_scene" / "data",
        ADDONS / "smart_construction_scene" / "profiles",
    )
    for root in guarded_roots:
        if not root.is_dir():
            continue
        for path in root.rglob("*"):
            if path.suffix not in {".py", ".xml"}:
                continue
            text = path.read_text(encoding="utf-8", errors="ignore")
            scrubbed = "\n".join(
                line
                for line in text.splitlines()
                if not line.strip().startswith("LEGACY_SYSTEM_DEFAULT_")
            )
            if "待完善" in scrubbed:
                errors.append(
                    "smart_construction_core: runtime product surface must not expose pending placeholder wording: "
                    f"{path.relative_to(ROOT).as_posix()}"
                )
            for token in forbidden_user_surface_tokens:
                if token in scrubbed:
                    errors.append(
                        "smart_construction_core: runtime product surface must not expose sample/technical "
                        f"placeholder wording {token!r}: {path.relative_to(ROOT).as_posix()}"
                    )
    return errors


def verify_dashboard_focus_scene_runtime_contract() -> list[str]:
    errors: list[str] = []
    guarded_paths = (
        ADDONS / "smart_construction_scene" / "data" / "sc_scene_layout.xml",
        ADDONS / "smart_construction_scene" / "data" / "sc_scene_orchestration.xml",
        ADDONS / "smart_construction_scene" / "profiles" / "scene_registry_content.py",
        ADDONS / "smart_construction_scene" / "core_extension.py",
        ROOT / "scripts" / "verify" / "executive_readonly_seed.py",
        ROOT / "scripts" / "verify" / "executive_readonly_smoke.py",
    )
    legacy_xmlid_fragments = (
        "sc_scene_version_projects_dashboard_showcase_v2",
        "sc_scene_projects_dashboard_showcase",
    )
    for path in guarded_paths:
        if not path.is_file():
            continue
        text = path.read_text(encoding="utf-8", errors="ignore")
        scrubbed = text
        for fragment in legacy_xmlid_fragments:
            scrubbed = scrubbed.replace(fragment, "")
        if "dashboard_showcase" in scrubbed:
            errors.append(
                "smart_construction_scene: dashboard focus scene may retain legacy XMLIDs only, "
                f"not runtime showcase code/route/provider keys: {path.relative_to(ROOT).as_posix()}"
            )
    required_contracts = {
        ADDONS / "smart_construction_scene" / "data" / "sc_scene_layout.xml": (
            "'code': 'projects.dashboard_focus'",
            "'route': '/s/projects.dashboard_focus'",
            "'provider': 'projects.dashboard_focus.metrics'",
            "'provider': 'projects.dashboard_focus.overview'",
        ),
        ADDONS / "smart_construction_scene" / "data" / "sc_scene_orchestration.xml": (
            "<field name=\"code\">projects.dashboard_focus</field>",
            "<field name=\"name\">项目驾驶舱聚焦</field>",
        ),
        ADDONS / "smart_construction_scene" / "profiles" / "scene_registry_content.py": (
            '"code": "projects.dashboard_focus"',
            '"route": "/s/projects.dashboard_focus"',
        ),
    }
    for path, required_tokens in required_contracts.items():
        if not path.is_file():
            errors.append(
                "smart_construction_scene: dashboard focus scene contract file missing: "
                f"{path.relative_to(ROOT).as_posix()}"
            )
            continue
        text = path.read_text(encoding="utf-8", errors="ignore")
        for token in required_tokens:
            if token not in text:
                errors.append(
                    "smart_construction_scene: dashboard focus scene runtime contract missing "
                    f"{token!r}: {path.relative_to(ROOT).as_posix()}"
                )
    return errors


def verify_scene_registry_engine_fallback_observability() -> list[str]:
    path = ADDONS / "smart_construction_scene" / "scene_registry.py"
    if not path.is_file():
        return []
    text = path.read_text(encoding="utf-8", errors="ignore")
    if "except Exception:\n            pass" not in text:
        return []
    return [
        "smart_construction_scene: scene registry engine fallback must log "
        "exception degradation before using direct loader"
    ]


def verify_core_docs_product_examples() -> list[str]:
    errors: list[str] = []
    docs_dir = ADDONS / "smart_construction_core" / "docs"
    forbidden_tokens = ("project.project_demo", "account.analytic.account_contract_demo", "project.wbs_demo")
    if not docs_dir.is_dir():
        return errors
    for path in docs_dir.rglob("*.md"):
        text = path.read_text(encoding="utf-8", errors="ignore")
        for token in forbidden_tokens:
            if token in text:
                errors.append(
                    "smart_construction_core: docs must use product external-id examples, "
                    f"not demo token {token!r}: {path.relative_to(ROOT).as_posix()}"
                )
    return errors


def verify_core_runtime_demo_residual_allowlist() -> list[str]:
    errors: list[str] = []
    module_root = ADDONS / "smart_construction_core"
    compatibility_fragments_by_path = {
        "models/core/project_core.py": {
            "sc_demo_showcase",
            "sc_demo_showcase_ready",
        },
        "models/support/portal_execute.py": {
            "action_portal_demo_ping",
        },
        "models/support/runtime_user_management.py": {
            '"Demo"',
            '"demo_"',
        },
        "services/portal_execute_button_service.py": {
            "action_portal_demo_ping",
        },
    }
    forbidden_tokens = ("demo_", "_demo", "sc_demo", "Demo", "演示", "试点")
    excluded_parts = {"tests", "migrations", "docs", "tools", "__pycache__"}
    for path in module_root.rglob("*.py"):
        relative = path.relative_to(module_root).as_posix()
        if any(part in excluded_parts for part in path.relative_to(module_root).parts):
            continue
        if relative == "core_extension.py":
            continue
        text = path.read_text(encoding="utf-8", errors="ignore")
        for fragment in compatibility_fragments_by_path.get(relative, set()):
            text = text.replace(fragment, "")
        hits = {token for token in forbidden_tokens if token in text}
        if not hits:
            continue
        errors.append(
            "smart_construction_core: unexpected demo/pilot token in runtime python: "
            f"{relative} tokens={','.join(sorted(hits))}"
        )
    return errors


def verify_core_extension_legacy_label_boundary() -> list[str]:
    path = ADDONS / "smart_construction_core" / "core_extension.py"
    if not path.is_file():
        return []
    text = path.read_text(encoding="utf-8", errors="ignore")
    allowed_literals = {
        '"演示"': "action noise marker for legacy showcase action filtering",
        '"项目列表（演示）"': "hidden legacy showcase menu label",
        '"项目台账（试点）"': "legacy ledger label renamed to product label",
    }
    errors: list[str] = []
    for literal, reason in allowed_literals.items():
        if text.count(literal) != 1:
            errors.append(
                "smart_construction_core: core_extension legacy label compatibility literal "
                f"{literal} must appear exactly once ({reason})"
            )
    scrubbed = text
    for literal in allowed_literals:
        scrubbed = scrubbed.replace(literal, "")
    for token in ("演示", "试点"):
        if token in scrubbed:
            errors.append(
                "smart_construction_core: core_extension may only carry demo/pilot wording "
                f"inside explicit legacy label compatibility literals, found token {token!r}"
            )
    return errors


def verify_seed_showcase_product_fields() -> list[str]:
    errors: list[str] = []
    seed_files = (
        ADDONS / "smart_construction_seed" / "seed" / "steps" / "step_20_projects_demo.py",
        ADDONS / "smart_construction_seed" / "seed" / "steps" / "step_90_verify_demo.py",
    )
    forbidden_fields = ("sc_demo_showcase", "sc_demo_showcase_ready")
    for path in seed_files:
        if not path.is_file():
            continue
        text = path.read_text(encoding="utf-8", errors="ignore")
        for field in forbidden_fields:
            if field in text:
                errors.append(
                    "smart_construction_seed: project showcase seed must write product fields "
                    f"not legacy alias {field!r}: {path.relative_to(ROOT).as_posix()}"
                )
    return errors


def verify_custom_security_policy_role_login_boundary() -> list[str]:
    path = ADDONS / "smart_construction_custom" / "models" / "security_policy.py"
    if not path.is_file():
        return []
    text = path.read_text(encoding="utf-8", errors="ignore")
    required_formal_logins = (
        "sc_role_project_read",
        "sc_role_project_user",
        "sc_role_project_manager",
        "sc_role_owner",
        "sc_role_pm",
        "sc_role_finance",
        "sc_role_executive",
    )
    legacy_logins = tuple(login.replace("sc_", "demo_", 1) for login in required_formal_logins)
    errors: list[str] = []
    if "ROLE_LOGIN_GROUPS" not in text or "LEGACY_ROLE_LOGIN_ALIASES" not in text:
        errors.append(
            "smart_construction_custom: security policy must separate formal role logins "
            "from legacy demo login aliases"
        )
        return errors
    for login in required_formal_logins:
        if f'"{login}"' not in text:
            errors.append(
                "smart_construction_custom: security policy missing formal role login "
                f"{login!r}"
            )
    alias_start = text.find("LEGACY_ROLE_LOGIN_ALIASES")
    for login in legacy_logins:
        quoted = f'"{login}"'
        if text.count(quoted) != 1 or text.find(quoted) < alias_start:
            errors.append(
                "smart_construction_custom: legacy demo role login must appear only as "
                f"compatibility alias: {login!r}"
            )
    return errors


def main() -> int:
    errors: list[str] = []
    errors.extend(verify_manifest_shape())
    errors.extend(verify_production_token_boundary())
    errors.extend(verify_custom_user_payload_boundary())
    errors.extend(verify_python_package_boundaries())
    errors.extend(verify_portal_execute_demo_boundary())
    errors.extend(verify_static_navigation_product_labels())
    errors.extend(verify_capability_registry_role_boundary())
    errors.extend(verify_handler_product_language_boundary())
    errors.extend(verify_runtime_comment_product_language_boundary())
    errors.extend(verify_portal_controller_exception_observability())
    errors.extend(verify_app_entry_exception_observability())
    errors.extend(verify_scene_governance_exception_observability())
    errors.extend(verify_core_api_controller_exception_observability())
    errors.extend(verify_business_slice_project_resolution_observability())
    errors.extend(verify_policy_capability_dashboard_exception_observability())
    errors.extend(verify_core_model_runtime_exception_observability())
    errors.extend(verify_core_extension_wizard_exception_observability())
    errors.extend(verify_runtime_pending_placeholder_language_boundary())
    errors.extend(verify_dashboard_focus_scene_runtime_contract())
    errors.extend(verify_scene_registry_engine_fallback_observability())
    errors.extend(verify_core_docs_product_examples())
    errors.extend(verify_core_runtime_demo_residual_allowlist())
    errors.extend(verify_core_extension_legacy_label_boundary())
    errors.extend(verify_seed_showcase_product_fields())
    errors.extend(verify_custom_security_policy_role_login_boundary())

    if errors:
        print("[industry_module_product_boundary_guard] FAIL", file=sys.stderr)
        for error in errors:
            print(f"- {error}", file=sys.stderr)
        return 1

    print("[industry_module_product_boundary_guard] PASS modules=%s" % len(INDUSTRY_MODULES))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
