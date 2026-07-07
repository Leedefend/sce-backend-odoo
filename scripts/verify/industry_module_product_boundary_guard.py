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
        "data/tax.xml": "manifest-excluded tax anchor; taxes are created idempotently by hooks.ensure_core_taxes",
        "views/res_users_views.xml": "legacy user-form experiment; enterprise/user module owns user profile surface",
        "views/support/partner_acceptance_product_menu_policy.xml": "historical acceptance policy; not part of formal runtime menu policy",
    },
    "smart_construction_custom": {
        "data/user_master_v1.xml": "real legacy user payload; loaded only by idempotent baseline loader",
    },
    "smart_construction_seed": {
        "data/sc_seed_login_env.xml": "scenario login flag; seed hook gates scenario mode explicitly",
        "data/sc_seed_partner.xml": "scenario partner seed; scenario steps must run through the guarded seed registry",
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


def verify_guard_metadata_product_language() -> list[str]:
    text = Path(__file__).read_text(encoding="utf-8", errors="ignore")
    forbidden_tokens = ("compatibility " + "stub",)
    errors: list[str] = []
    for token in forbidden_tokens:
        if token in text:
            errors.append(
                "industry module guard metadata must describe excluded assets with product "
                f"ownership language, not {token!r}"
            )
    for reason in ALLOWED_UNDECLARED_XML.get("smart_construction_seed", {}).values():
        if "demo" in reason.lower():
            errors.append(
                "industry module guard metadata must describe seed excluded assets "
                "with scenario seed ownership language"
            )
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


def verify_legacy_temporary_account_boundary() -> list[str]:
    allowed_hits = {
        "addons/smart_construction_custom/data/user_master_v1.xml": 1,
        "addons/smart_construction_core/models/support/runtime_user_management.py": 1,
    }
    errors: list[str] = []
    scan_roots = (
        ADDONS / "smart_construction_core",
        ADDONS / "smart_construction_custom",
    )
    actual_hits: dict[str, int] = {}
    for root in scan_roots:
        if not root.is_dir():
            continue
        for path in root.rglob("*"):
            if path.suffix not in {".py", ".xml"}:
                continue
            relative = path.relative_to(ROOT).as_posix()
            text = path.read_text(encoding="utf-8", errors="ignore")
            count = text.count("临时账号")
            if count:
                actual_hits[relative] = count
    for relative, count in sorted(actual_hits.items()):
        if allowed_hits.get(relative) != count:
            errors.append(
                "smart_construction_core: temporary-account wording must stay limited "
                f"to the legacy user payload and runtime-user exclusion guard: {relative}"
            )
    for relative, count in sorted(allowed_hits.items()):
        if actual_hits.get(relative) != count:
            errors.append(
                "smart_construction_core: expected temporary-account historical payload anchor "
                f"{relative} count={count}"
            )
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
            errors.append(f"smart_construction_core: legacy portal demo method leaks outside historical method anchors: {relative}")
    return errors


def verify_portal_execute_legacy_method_anchor_boundary() -> list[str]:
    allowed_hits = {
        "addons/smart_construction_core/models/support/portal_execute.py": 1,
        "addons/smart_construction_core/services/portal_execute_button_service.py": 1,
    }
    errors: list[str] = []
    module_root = ADDONS / "smart_construction_core"
    actual_hits: dict[str, int] = {}
    for path in module_root.rglob("*.py"):
        relative = path.relative_to(ROOT).as_posix()
        if "migrations" in path.parts or "tests" in path.parts:
            continue
        count = path.read_text(encoding="utf-8", errors="ignore").count("action_portal_demo_ping")
        if count:
            actual_hits[relative] = count
    for relative, count in sorted(actual_hits.items()):
        if allowed_hits.get(relative) != count:
            errors.append(
                "smart_construction_core: action_portal_demo_ping must stay limited "
                f"to explicit portal execute historical method anchors: {relative}"
            )
    for relative, count in sorted(allowed_hits.items()):
        if actual_hits.get(relative) != count:
            errors.append(
                "smart_construction_core: expected portal execute historical method anchor "
                f"{relative} count={count}"
            )
    return errors


def verify_static_navigation_product_labels() -> list[str]:
    errors: list[str] = []
    nav_map = ADDONS / "smart_construction_core" / "static/src/config/domain_nav_map.js"
    text = nav_map.read_text(encoding="utf-8") if nav_map.is_file() else ""
    if 'tag: "试点"' in text or "tag: '试点'" in text:
        errors.append("smart_construction_core: pinned navigation entries must not be labeled as pilot")
    role_entry_map = ADDONS / "smart_construction_core" / "static/src/config/role_entry_map.js"
    role_entry_text = role_entry_map.read_text(encoding="utf-8") if role_entry_map.is_file() else ""
    if "Legacy fallback map" in role_entry_text:
        errors.append(
            "smart_construction_core: static role entry fallback must use historical "
            "fallback wording, not legacy fallback wording"
        )
    return errors


def verify_static_style_product_language_boundary() -> list[str]:
    errors: list[str] = []
    static_root = ADDONS / "smart_construction_core" / "static" / "src"
    forbidden_tokens = ("容器骨架",)
    if not static_root.is_dir():
        return errors
    for path in static_root.rglob("*"):
        if path.suffix not in {".css", ".scss"}:
            continue
        text = path.read_text(encoding="utf-8", errors="ignore")
        for token in forbidden_tokens:
            if token in text:
                errors.append(
                    "smart_construction_core: static style comments must use product layout language, "
                    f"not development wording {token!r}: {path.relative_to(ROOT).as_posix()}"
                )
    return errors


def verify_capability_registry_role_boundary() -> list[str]:
    errors: list[str] = []
    registry = ADDONS / "smart_construction_core" / "services/capability_registry.py"
    text = registry.read_text(encoding="utf-8") if registry.is_file() else ""
    for token in ("demo_pm", "demo_finance", "demo_role_executive"):
        if token in text:
            errors.append(f"smart_construction_core: capability roles must come from groups, not demo login token {token!r}")
    return errors


def verify_security_group_historical_boundary() -> list[str]:
    groups_xml = ADDONS / "smart_construction_core" / "security" / "sc_groups.xml"
    capability_groups_xml = ADDONS / "smart_construction_core" / "security" / "sc_capability_groups.xml"
    errors: list[str] = []
    groups_text = groups_xml.read_text(encoding="utf-8", errors="ignore") if groups_xml.is_file() else ""
    cap_text = capability_groups_xml.read_text(encoding="utf-8", errors="ignore") if capability_groups_xml.is_file() else ""
    required_fragments = {
        "已废弃历史组：仅保留 XMLID 与历史记录，避免升级报错；不再承载实际权限。": 2,
        "行业配置管理员（历史 XMLID 保留）": 1,
        "不再代表平台管理员，不继承 Smart Core 平台组或 Odoo 系统组": 1,
    }
    combined = "\n".join((groups_text, cap_text))
    for fragment, expected_count in required_fragments.items():
        if combined.count(fragment) != expected_count:
            errors.append(
                "smart_construction_core: security group historical boundary "
                f"anchor count mismatch for {fragment!r}: expected {expected_count}"
            )
    forbidden_fragments = (
        "已废弃历史兼容组",
        "历史 XMLID 兼容",
    )
    for fragment in forbidden_fragments:
        if fragment in combined:
            errors.append(
                "smart_construction_core: security groups must use historical-retention "
                f"wording, not generic compatibility wording {fragment!r}"
            )
    return errors


def verify_handler_product_language_boundary() -> list[str]:
    errors: list[str] = []
    handlers_dir = ADDONS / "smart_construction_core" / "handlers"
    forbidden_tokens = (
        "这里演示",
        "demo ping",
        "演示",
        "试点",
        "后续契约入口",
        "compatibility for lightweight boundary tests",
        "兼容早期 note",
    )
    for path in handlers_dir.rglob("*.py"):
        text = path.read_text(encoding="utf-8", errors="ignore")
        for token in forbidden_tokens:
            if token in text:
                errors.append(
                    "smart_construction_core: handler product code contains demo-oriented wording "
                    f"{token!r}: {path.relative_to(ROOT).as_posix()}"
                )
    return errors


def verify_my_work_historical_todo_boundary() -> list[str]:
    handler = ADDONS / "smart_construction_core" / "handlers" / "my_work_summary.py"
    text = handler.read_text(encoding="utf-8", errors="ignore")
    required_fragments = {
        'PRIMARY_TODO_AUTHORITY = "mail.activity"',
        'HISTORICAL_TODO_AUTHORITIES = ["sc.workflow.workitem"]',
        '"historical_todo_authorities": list(self.HISTORICAL_TODO_AUTHORITIES)',
    }
    forbidden_fragments = {
        "LEGACY_TODO_AUTHORITIES",
        '"legacy_todo_authorities"',
    }
    errors: list[str] = []
    for fragment in required_fragments:
        if text.count(fragment) != 1:
            errors.append(
                "smart_construction_core: my work todo source contract must declare "
                f"historical authority boundary exactly once: {fragment!r}"
            )
    for fragment in forbidden_fragments:
        if fragment in text:
            errors.append(
                "smart_construction_core: my work todo source contract must use "
                f"historical authority naming, not {fragment!r}"
            )
    return errors


def verify_core_model_legacy_product_message_boundary() -> list[str]:
    model_roots = (
        ADDONS / "smart_construction_core" / "models" / "core",
        ADDONS / "smart_construction_core" / "models" / "support",
    )
    errors: list[str] = []
    for model_root in model_roots:
        for path in model_root.rglob("*.py"):
            text = path.read_text(encoding="utf-8", errors="ignore")
            if "Legacy " in text:
                errors.append(
                    "smart_construction_core: business model product messages must use "
                    f"historical source wording, not English Legacy wording: {path.relative_to(ROOT).as_posix()}"
                )
    return errors


def verify_scene_provider_historical_entry_wording() -> list[str]:
    providers_root = ADDONS / "smart_construction_scene" / "providers"
    errors: list[str] = []
    if not providers_root.is_dir():
        return errors
    for path in providers_root.rglob("*.py"):
        text = path.read_text(encoding="utf-8", errors="ignore")
        if "兼容入口" in text:
            errors.append(
                "smart_construction_scene: provider guidance must use historical-entry "
                f"wording, not generic compatibility-entry wording: {path.relative_to(ROOT).as_posix()}"
            )
    return errors


def verify_project_dashboard_open_alias_boundary() -> list[str]:
    path = ADDONS / "smart_construction_core" / "handlers" / "project_dashboard_open.py"
    if not path.is_file():
        return ["smart_construction_core: project.dashboard.open compatibility handler missing"]
    text = path.read_text(encoding="utf-8", errors="ignore")
    required_fragments = {
        'INTENT_TYPE = "project.dashboard.open"',
        'DESCRIPTION = "历史入口转发到 project.dashboard.enter"',
        '"authorities": ["project.dashboard.enter"]',
        '"projection_only": True',
        '"compatibility_only": True',
        '"no_business_fact_authority": True',
        '"deprecated": True',
        '"deprecated_replacement_intent": "project.dashboard.enter"',
    }
    errors: list[str] = []
    for fragment in sorted(required_fragments):
        if text.count(fragment) != 1:
            errors.append(
                "smart_construction_core: project.dashboard.open must remain a single "
                f"deprecated proxy to project.dashboard.enter, missing anchor {fragment!r}"
            )
    if "兼容别名" in text:
        errors.append(
            "smart_construction_core: project.dashboard.open description must use "
            "historical-entry wording, not generic compatibility alias wording"
        )
    return errors


def verify_handler_historical_wrapper_boundary() -> list[str]:
    anchors_by_path = {
        ADDONS / "smart_construction_core" / "handlers" / "my_work_complete.py": {
            "# Historical import wrapper; new code calls my_work_failure_meta_for_exception directly.",
            "def _failure_meta_for_exception(exc):",
            "return my_work_failure_meta_for_exception(exc)",
        },
        ADDONS / "smart_construction_core" / "handlers" / "capability_visibility_report.py": {
            "# Historical import wrapper; new code calls suggested_action_for_capability_reason directly.",
            "def _suggested_action_for_reason(*, reason_code, state):",
            "return suggested_action_for_capability_reason(reason_code=reason_code, state=state)",
        },
        ADDONS / "smart_construction_core" / "handlers" / "project_execution_advance.py": {
            "# Historical semantic guard anchor after response-builder extraction:",
            '# "result": "blocked"',
            "# Historical semantic guard wrapper; new code calls ProjectExecutionHintService directly.",
            "def _build_lifecycle_hints(self, project_id: int, reason_code: str) -> dict:",
            "return self._hint_service().build_lifecycle_hints(project_id, reason_code)",
        },
    }
    forbidden_fragments = (
        "Keep this compatibility wrapper",
        "Keep this wrapper for backward compatibility",
        "Semantic guard compatibility anchor",
        "Compatibility shim for lifecycle semantic guard",
    )
    errors: list[str] = []
    for path, anchors in anchors_by_path.items():
        if not path.is_file():
            errors.append(
                "smart_construction_core: handler historical wrapper anchor file missing: "
                f"{path.relative_to(ROOT).as_posix()}"
            )
            continue
        text = path.read_text(encoding="utf-8", errors="ignore")
        for anchor in sorted(anchors):
            if text.count(anchor) != 1:
                errors.append(
                    "smart_construction_core: handler historical wrapper must remain a "
                    f"single direct delegation, missing anchor {anchor!r}: "
                    f"{path.relative_to(ROOT).as_posix()}"
                )
        for fragment in forbidden_fragments:
            if fragment in text:
                errors.append(
                    "smart_construction_core: handler historical wrapper must not use "
                    f"generic compatibility wording {fragment!r}: {path.relative_to(ROOT).as_posix()}"
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
        "后续在 _create_with_hierarchy",
        "后续 WBS",
        "后续调试",
        "后续可根据需要再调整",
        "供后续按类别定制",
        "供后续行",
        "后续子级",
        "后续无 code",
        "临时实现",
        "占位实现",
        "占位路由",
        "阶段2架构",
        "Phase-1",
        "Phase-3",
        "阶段2扩展点",
        "阶段2框架",
        "解析器骨架",
        "行解析器骨架",
        "导入解析骨架",
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
        "项目[样例]",
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
        "项目驾驶舱（兼容）",
        "兼容旧入口",
        "（兼容）",
        "(兼容)",
        "兼容旧字段",
        "兼容历史字段",
        "用户角色兼容字段",
        "兼容字段中",
        "兼容旧视图",
        "兼容旧版",
        "兼容旧数据",
        "兼容设置页",
        "用户验收样例",
        "兼容历史门户动作入口",
        "Early placeholders",
        "阶段1中",
        "现阶段",
        "后续可扩展",
        "后续补充",
        "后续阶段",
        "后续继续",
        "后续继续补",
        "后续绑定正式入口",
        "当前层级占位",
        "阶段2占位",
        "作为占位",
        "章节池占位",
        "占位组",
        "废弃占位",
    )
    guarded_roots = (
        ADDONS / "smart_construction_core" / "models",
        ADDONS / "smart_construction_core" / "services",
        ADDONS / "smart_construction_core" / "data",
        ADDONS / "smart_construction_core" / "views",
        ADDONS / "smart_construction_core" / "wizard",
        ADDONS / "smart_construction_scene" / "data",
        ADDONS / "smart_construction_scene" / "profiles",
    )
    allowed_pending_compatibility_lines = {
        'LEGACY_SYSTEM_DEFAULT_PROJECT_NAME = "系统默认项目（待完善）"',
        'LEGACY_SYSTEM_DEFAULT_SUPPLIER_NAME = "系统默认供应商（待完善）"',
    }
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
                if line.strip() not in allowed_pending_compatibility_lines
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


def verify_material_historical_default_name_boundary() -> list[str]:
    path = ADDONS / "smart_construction_core" / "models" / "core" / "material_acceptance.py"
    if not path.is_file():
        return [
            "smart_construction_core: material historical default-name anchor file missing"
        ]
    text = path.read_text(encoding="utf-8", errors="ignore")
    required_anchors = {
        'LEGACY_SYSTEM_DEFAULT_PROJECT_NAME = "系统默认项目（待完善）"',
        'LEGACY_SYSTEM_DEFAULT_SUPPLIER_NAME = "系统默认供应商（待完善）"',
    }
    errors: list[str] = []
    for anchor in sorted(required_anchors):
        if text.count(anchor) != 1:
            errors.append(
                "smart_construction_core: material historical default-name anchor "
                f"must appear exactly once: {anchor}"
            )
    scrubbed = text
    for anchor in required_anchors:
        scrubbed = scrubbed.replace(anchor, "")
    if "待完善" in scrubbed:
        errors.append(
            "smart_construction_core: material historical default-name anchor may only use "
            "pending wording inside explicit legacy system default constants"
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


def verify_project_execution_readiness_precheck_boundary() -> list[str]:
    module_root = ADDONS / "smart_construction_core"
    allowed_fragments_by_path = {
        "services/project_execution_service.py": {
            '"pilot_precheck": "block.project.execution_readiness_precheck"',
            "Compatibility key for older orchestration clients; new callers use readiness_precheck.",
        },
        "services/project_execution_builders/__init__.py": {
            "from .project_execution_readiness_precheck_builder import ProjectExecutionReadinessPrecheckBuilder",
        },
        "services/project_execution_builders/project_execution_next_actions_builder.py": {
            '"pilot_precheck_state": readiness_state',
            '"pilot_failed_count": readiness_failed_count',
            '"pilot_primary_reason_code": readiness_primary_reason_code',
            '"pilot_primary_message": readiness_primary_message',
            "Compatibility metrics for older consumers; new payloads use readiness_precheck_*.",
        },
        "services/project_execution_consistency_guard.py": {
            "def pilot_precheck(self, project) -> dict:",
            "Compatibility method for older callers; use readiness_precheck for new code.",
        },
    }
    errors: list[str] = []
    for relative, allowed_fragments in allowed_fragments_by_path.items():
        path = module_root / relative
        if not path.is_file():
            errors.append(
                "smart_construction_core: project execution readiness compatibility "
                f"anchor file missing: {relative}"
            )
            continue
        text = path.read_text(encoding="utf-8", errors="ignore")
        for fragment in allowed_fragments:
            if text.count(fragment) != 1:
                errors.append(
                    "smart_construction_core: project execution pilot_precheck compatibility "
                    f"anchor must appear exactly once in {relative}: {fragment!r}"
                )
    for path in module_root.rglob("*.py"):
        if any(part in {"tests", "migrations", "docs", "tools", "__pycache__"} for part in path.relative_to(module_root).parts):
            continue
        relative = path.relative_to(module_root).as_posix()
        text = path.read_text(encoding="utf-8", errors="ignore")
        for fragment in allowed_fragments_by_path.get(relative, set()):
            text = text.replace(fragment, "")
        if (
            "pilot_precheck" in text
            or "ProjectExecutionPilotPrecheck" in text
            or "project_execution_pilot_precheck_builder" in text
        ):
            errors.append(
                "smart_construction_core: project execution readiness precheck is the product "
                f"contract; pilot_precheck may only appear in explicit historical-readiness anchors: {relative}"
            )
    return errors


def verify_budget_historical_facade_boundary() -> list[str]:
    module_root = ADDONS / "smart_construction_core"
    core_init = module_root / "models" / "core" / "__init__.py"
    compat = module_root / "models" / "support" / "budget_compat.py"
    cost_domain = module_root / "models" / "core" / "cost_domain.py"
    readme = module_root / "README.md"
    errors: list[str] = []
    if not compat.is_file():
        errors.append("smart_construction_core: budget historical facade file missing")
        return errors
    core_text = core_init.read_text(encoding="utf-8", errors="ignore") if core_init.is_file() else ""
    compat_text = compat.read_text(encoding="utf-8", errors="ignore")
    cost_domain_text = cost_domain.read_text(encoding="utf-8", errors="ignore") if cost_domain.is_file() else ""
    readme_text = readme.read_text(encoding="utf-8", errors="ignore") if readme.is_file() else ""
    required_fragments = {
        "core import": "from ..support import budget_compat  # 历史 project.budget.line 模型门面，需在主模型前加载",
        "compat facade wording": "历史模型门面：将 project.budget.line 指向现用 project.budget.boq.line。",
        "compat description": '_description = "项目预算行历史模型门面"',
        "compat name": '_name = "project.budget.line"',
        "compat inherit": '_inherit = "project.budget.boq.line"',
        "compat table": '_table = "project_budget_boq_line"',
    }
    combined = "\n".join((core_text, compat_text))
    for label, fragment in required_fragments.items():
        if combined.count(fragment) != 1:
            errors.append(
                "smart_construction_core: budget historical facade anchor "
                f"must appear exactly once ({label}): {fragment!r}"
            )
    if "兼容旧 project.budget.line" in core_text:
        errors.append(
            "smart_construction_core: budget historical facade import must use historical-model "
            "boundary wording, not generic old-compatibility wording"
        )
    for fragment in ("兼容层：历史模型 project.budget.line", "项目预算行(兼容层)"):
        if fragment in compat_text:
            errors.append(
                "smart_construction_core: budget historical facade must use "
                f"historical-model facade wording, not generic compatibility wording {fragment!r}"
            )
    for path_label, text in (
        ("models/core/cost_domain.py", cost_domain_text),
        ("README.md", readme_text),
    ):
        for fragment in ("兼容模型", "兼容层", "ORM 元数据兼容"):
            if fragment in text:
                errors.append(
                    "smart_construction_core: budget historical facade documentation must "
                    f"avoid generic compatibility wording {fragment!r}: {path_label}"
                )
    if 'project.budget.line -> 现用 project.budget.boq.line' in cost_domain_text:
        errors.append(
            "smart_construction_core: cost_domain must not describe budget historical facade "
            "mapping details; keep that responsibility in models/support/budget_compat.py"
        )
    return errors


def verify_work_breakdown_historical_facade_boundary() -> list[str]:
    path = ADDONS / "smart_construction_core" / "models" / "support" / "work_breakdown.py"
    if not path.is_file():
        return ["smart_construction_core: work breakdown historical model facade missing"]
    text = path.read_text(encoding="utf-8", errors="ignore")
    required_fragments = {
        "class ProjectWbs(models.Model):",
        "历史模型门面：将 project.wbs 指向统一的工程结构表。",
        '_name = "project.wbs"',
        '_description = "工程结构历史模型门面"',
        '_inherit = "construction.work.breakdown"',
        '_table = "construction_work_breakdown"',
    }
    errors: list[str] = []
    for fragment in sorted(required_fragments):
        if text.count(fragment) != 1:
            errors.append(
                "smart_construction_core: project.wbs historical facade anchor "
                f"must appear exactly once: {fragment!r}"
            )
    forbidden_fragments = (
        "兼容层：将历史的 project.wbs",
        "工程结构兼容层",
    )
    for fragment in forbidden_fragments:
        if fragment in text:
            errors.append(
                "smart_construction_core: project.wbs facade must use historical-model "
                f"boundary wording, not generic compatibility wording {fragment!r}"
            )
    return errors


def verify_state_machine_historical_alias_boundary() -> list[str]:
    path = ADDONS / "smart_construction_core" / "models" / "support" / "state_machine.py"
    if not path.is_file():
        return ["smart_construction_core: state machine module missing"]
    text = path.read_text(encoding="utf-8", errors="ignore")
    required_fragments = {
        "# Historical constant aliases for existing imports; new code uses ScStateMachine.*.",
        "PROJECT_LIFECYCLE_STATES = ScStateMachine.PROJECT_STATES",
        "PROJECT_LIFECYCLE_TRANSITIONS = ScStateMachine.PROJECT_TRANSITIONS",
        "CONTRACT_STATES = ScStateMachine.CONTRACT_STATES",
        "CONTRACT_TRANSITIONS = ScStateMachine.CONTRACT_TRANSITIONS",
        "SETTLEMENT_ORDER_STATES = ScStateMachine.SETTLEMENT_ORDER_STATES",
        "SETTLEMENT_ORDER_TRANSITIONS = ScStateMachine.SETTLEMENT_ORDER_TRANSITIONS",
        "SETTLEMENT_STATES = ScStateMachine.SETTLEMENT_STATES",
        "SETTLEMENT_TRANSITIONS = ScStateMachine.SETTLEMENT_TRANSITIONS",
        "PAYMENT_REQUEST_STATES = ScStateMachine.PAYMENT_REQUEST_STATES",
        "PAYMENT_REQUEST_TRANSITIONS = ScStateMachine.PAYMENT_REQUEST_TRANSITIONS",
        "BOQ_SOURCE_TYPES = ScStateMachine.BOQ_SOURCE_TYPES",
    }
    errors: list[str] = []
    for fragment in sorted(required_fragments):
        if text.count(fragment) != 1:
            errors.append(
                "smart_construction_core: state machine historical alias must remain "
                f"a direct ScStateMachine alias, missing anchor {fragment!r}"
            )
    if "Legacy exports for backward compatibility" in text:
        errors.append(
            "smart_construction_core: state machine aliases must use historical-alias "
            "boundary wording, not generic legacy export wording"
        )
    return errors


def verify_sc_workflow_historical_runtime_boundary() -> list[str]:
    path = ADDONS / "smart_construction_core" / "models" / "support" / "sc_workflow.py"
    if not path.is_file():
        return ["smart_construction_core: historical sc.workflow runtime file missing"]
    text = path.read_text(encoding="utf-8", errors="ignore")
    required_fragments = {
        'LEGACY_WORKFLOW_RUNTIME_PARAM = "sc.workflow.legacy_runtime_enabled"',
        'LEGACY_WORKFLOW_RUNTIME_CONTEXT = "allow_legacy_workflow_runtime"',
        "SC workflow is a historical workflow runtime. ",
        "Use base_tier_validation for approval runtime, or enable %s explicitly.",
        "SC workflow runtime is disabled because approval runtime is base_tier_validation. ",
        "Enable %s only for historical workflow runtime recovery.",
    }
    errors: list[str] = []
    for fragment in sorted(required_fragments):
        if text.count(fragment) != 1:
            errors.append(
                "smart_construction_core: sc.workflow historical runtime boundary "
                f"must keep explicit runtime-gate anchor {fragment!r}"
            )
    forbidden_fragments = (
        "SC workflow is retained for legacy compatibility",
        "Enable %s only for legacy compatibility",
    )
    for fragment in forbidden_fragments:
        if fragment in text:
            errors.append(
                "smart_construction_core: sc.workflow runtime must use historical-runtime "
                f"wording, not generic legacy compatibility wording {fragment!r}"
            )
    return errors


def verify_legacy_purchase_contract_recovery_approval_boundary() -> list[str]:
    path = ADDONS / "smart_construction_core" / "models" / "support" / "legacy_purchase_contract_fact.py"
    if not path.is_file():
        return ["smart_construction_core: legacy purchase contract fact model missing"]
    text = path.read_text(encoding="utf-8", errors="ignore")
    required_fragments = {
        "allow_legacy_contract_workflow",
        "历史采购/一般合同事实只作为旧库承载，不再发起新系统审批。",
        "历史采购/一般合同事实尚未完成历史事实审批恢复流程。",
        "历史采购/一般合同事实已启用历史事实审批恢复，但没有匹配的统一审批规则，请检查业务审批配置。",
        "历史采购/一般合同事实已经在历史事实审批恢复流程中，请等待审批完成。",
    }
    errors: list[str] = []
    for fragment in sorted(required_fragments):
        if text.count(fragment) < 1:
            errors.append(
                "smart_construction_core: legacy purchase contract approval recovery "
                f"boundary missing anchor {fragment!r}"
            )
    if text.count("历史采购/一般合同事实尚未完成历史事实审批恢复流程。") != 2:
        errors.append(
            "smart_construction_core: legacy purchase contract approval recovery "
            "must guard both manual approval and tier callback paths"
        )
    forbidden_fragments = (
        "兼容审批流程",
        "兼容审批",
    )
    for fragment in forbidden_fragments:
        if fragment in text:
            errors.append(
                "smart_construction_core: legacy purchase contract fact must use "
                f"historical approval recovery wording, not generic compatibility wording {fragment!r}"
            )
    return errors


def verify_platform_admin_facade_boundary() -> list[str]:
    path = ADDONS / "smart_construction_core" / "services" / "platform_admin.py"
    if not path.is_file():
        return ["smart_construction_core: platform admin historical import facade missing"]
    text = path.read_text(encoding="utf-8", errors="ignore")
    exact_once_fragments = {
        '"""Historical import facade for canonical smart_core platform-admin checks."""',
        "from odoo.addons.smart_core.security.platform_admin import (",
    }
    required_fragments = {
        "PLATFORM_ADMIN_GROUP",
        "platform_admin_group_xmlids",
        "platform_admin_groups",
        "user_is_platform_admin",
    }
    errors: list[str] = []
    for fragment in sorted(exact_once_fragments):
        if text.count(fragment) != 1:
            errors.append(
                "smart_construction_core: platform_admin facade must delegate to "
                f"smart_core.security.platform_admin, missing anchor {fragment!r}"
            )
    for fragment in sorted(required_fragments):
        if fragment not in text:
            errors.append(
                "smart_construction_core: platform_admin facade must re-export "
                f"smart_core platform-admin contract fragment {fragment!r}"
            )
    forbidden_fragments = (
        "Compatibility shim",
        "def user_is_platform_admin",
        "has_group(",
    )
    for fragment in forbidden_fragments:
        if fragment in text:
            errors.append(
                "smart_construction_core: platform_admin facade must not carry local "
                f"platform-admin logic or shim wording: {fragment!r}"
            )
    return errors


def verify_project_showcase_legacy_alias_boundary() -> list[str]:
    path = ADDONS / "smart_construction_core" / "models" / "core" / "project_core.py"
    if not path.is_file():
        return ["smart_construction_core: project showcase legacy alias file missing"]
    text = path.read_text(encoding="utf-8", errors="ignore")
    required_lines = {
        "    sc_demo_showcase = fields.Boolean(",
        "        related='sc_project_showcase',",
        "    sc_demo_showcase_ready = fields.Boolean(",
        "        related='sc_project_showcase_ready',",
    }
    errors: list[str] = []
    for line in sorted(required_lines):
        if text.count(line) != 1:
            errors.append(
                "smart_construction_core: project showcase legacy alias anchor "
                f"must appear exactly once: {line.strip()}"
            )
    scrubbed = text
    for line in required_lines:
        scrubbed = scrubbed.replace(line, "")
    if "sc_demo_showcase" in scrubbed:
        errors.append(
            "smart_construction_core: sc_demo_showcase legacy aliases must stay limited "
            "to the explicit related field anchors in project_core"
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
    for token in ("Legacy loader shim", "Legacy hook shim"):
        if token in text:
            errors.append(
                "smart_construction_core: core_extension platform hooks must use "
                f"compatibility hook wording, not {token!r}"
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


def verify_seed_product_language_boundary() -> list[str]:
    paths = (
        ADDONS / "smart_construction_seed" / "__manifest__.py",
        ADDONS / "smart_construction_seed" / "hooks.py",
    )
    steps_dir = ADDONS / "smart_construction_seed" / "seed" / "steps"
    forbidden_tokens = (
        "placeholder hook",
        "Extend with real seed data later",
        "Extend with seed data as needed",
        "verify/demo",
        "demo-only steps",
        "demo env",
        "placeholder marker",
        "Placeholder marker",
        "placeholder for future",
        "Placeholder for",
    )
    errors: list[str] = []
    scan_paths = list(paths)
    if steps_dir.is_dir():
        scan_paths.extend(sorted(steps_dir.glob("step_*.py")))
    for path in scan_paths:
        if not path.is_file():
            continue
        text = path.read_text(encoding="utf-8", errors="ignore")
        for token in forbidden_tokens:
            if token in text:
                errors.append(
                    "smart_construction_seed: production seed metadata and hook must use "
                    f"baseline/scenario language, not development wording {token!r}: "
                    f"{path.relative_to(ROOT).as_posix()}"
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
    try:
        module_ast = ast.parse(text, filename=str(path))
        alias_node = next(
            node.value
            for node in module_ast.body
            if isinstance(node, ast.Assign)
            for target in node.targets
            if isinstance(target, ast.Name) and target.id == "LEGACY_ROLE_LOGIN_ALIASES"
        )
        alias_map = ast.literal_eval(alias_node)
    except Exception as exc:
        errors.append(f"smart_construction_custom: unable to parse legacy role login aliases: {exc}")
        return errors
    expected_alias_map = {
        login: (login.replace("sc_", "demo_", 1),)
        for login in required_formal_logins
    }
    if alias_map != expected_alias_map:
        errors.append(
            "smart_construction_custom: legacy role login aliases must exactly match "
            "the formal role login compatibility map"
        )
    return errors


def main() -> int:
    errors: list[str] = []
    errors.extend(verify_manifest_shape())
    errors.extend(verify_guard_metadata_product_language())
    errors.extend(verify_production_token_boundary())
    errors.extend(verify_custom_user_payload_boundary())
    errors.extend(verify_legacy_temporary_account_boundary())
    errors.extend(verify_python_package_boundaries())
    errors.extend(verify_portal_execute_demo_boundary())
    errors.extend(verify_portal_execute_legacy_method_anchor_boundary())
    errors.extend(verify_static_navigation_product_labels())
    errors.extend(verify_static_style_product_language_boundary())
    errors.extend(verify_capability_registry_role_boundary())
    errors.extend(verify_security_group_historical_boundary())
    errors.extend(verify_handler_product_language_boundary())
    errors.extend(verify_my_work_historical_todo_boundary())
    errors.extend(verify_core_model_legacy_product_message_boundary())
    errors.extend(verify_scene_provider_historical_entry_wording())
    errors.extend(verify_project_dashboard_open_alias_boundary())
    errors.extend(verify_handler_historical_wrapper_boundary())
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
    errors.extend(verify_material_historical_default_name_boundary())
    errors.extend(verify_dashboard_focus_scene_runtime_contract())
    errors.extend(verify_scene_registry_engine_fallback_observability())
    errors.extend(verify_core_docs_product_examples())
    errors.extend(verify_core_runtime_demo_residual_allowlist())
    errors.extend(verify_project_execution_readiness_precheck_boundary())
    errors.extend(verify_budget_historical_facade_boundary())
    errors.extend(verify_work_breakdown_historical_facade_boundary())
    errors.extend(verify_state_machine_historical_alias_boundary())
    errors.extend(verify_sc_workflow_historical_runtime_boundary())
    errors.extend(verify_legacy_purchase_contract_recovery_approval_boundary())
    errors.extend(verify_platform_admin_facade_boundary())
    errors.extend(verify_project_showcase_legacy_alias_boundary())
    errors.extend(verify_core_extension_legacy_label_boundary())
    errors.extend(verify_seed_showcase_product_fields())
    errors.extend(verify_seed_product_language_boundary())
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
