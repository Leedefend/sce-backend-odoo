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
    "smart_construction_core": ("smart_construction_demo.", "sc_demo_", "Demo-", "演示项目"),
    "smart_construction_bundle": ("smart_construction_demo.", "sc_demo_", "Demo-", "演示项目"),
    "smart_construction_portal": ("smart_construction_demo.", "sc_demo_", "Demo-", "演示项目"),
    "smart_construction_scene": ("smart_construction_demo.", "sc_demo_", "Demo-", "演示项目", "（演示）"),
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


def main() -> int:
    errors: list[str] = []
    errors.extend(verify_manifest_shape())
    errors.extend(verify_production_token_boundary())
    errors.extend(verify_custom_user_payload_boundary())
    errors.extend(verify_python_package_boundaries())
    errors.extend(verify_portal_execute_demo_boundary())
    errors.extend(verify_static_navigation_product_labels())
    errors.extend(verify_capability_registry_role_boundary())

    if errors:
        print("[industry_module_product_boundary_guard] FAIL", file=sys.stderr)
        for error in errors:
            print(f"- {error}", file=sys.stderr)
        return 1

    print("[industry_module_product_boundary_guard] PASS modules=%s" % len(INDUSTRY_MODULES))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
