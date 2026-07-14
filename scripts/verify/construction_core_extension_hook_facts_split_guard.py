#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CORE_EXTENSION = ROOT / "addons/smart_construction_core/core_extension.py"
FACTS = ROOT / "addons/smart_construction_core/core_extension_hook_facts.py"
CI = ROOT / "make/ci.mk"

MAX_CORE_EXTENSION_LINES = 2884


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="ignore") if path.is_file() else ""


def _load(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"unable to load {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def main() -> int:
    errors: list[str] = []
    core_text = _read(CORE_EXTENSION)
    facts_text = _read(FACTS)
    ci_text = _read(CI)

    if not core_text:
        errors.append(f"missing core extension file: {CORE_EXTENSION.relative_to(ROOT)}")
    if not facts_text:
        errors.append(f"missing hook facts module: {FACTS.relative_to(ROOT)}")

    if core_text:
        line_count = len(core_text.splitlines())
        if line_count > MAX_CORE_EXTENSION_LINES:
            errors.append(f"core_extension.py line budget exceeded: {line_count} > {MAX_CORE_EXTENSION_LINES}")
        for token in [
            "core_extension_hook_facts as _hook_facts",
            "return _hook_facts.business_config_admin_group_xmlids()",
            "return _hook_facts.lowcode_system_config_menu_xmlids()",
            "return _hook_facts.product_policy_catalog_source(source_env=source_env)",
            "return _hook_facts.app_shell_contract()",
            "return _hook_facts.scene_entry_orchestrator_specs()",
            "return _hook_facts.user_data_acceptance_nav_contract()",
        ]:
            if token not in core_text:
                errors.append(f"core_extension.py missing hook facts split token: {token}")

    if facts_text:
        for token in [
            "def business_config_admin_group_xmlids(",
            "def lowcode_system_config_menu_xmlids(",
            "def business_nav_group_display_order(",
            "def product_policy_catalog_source(",
            "def product_policy_catalog_label(",
            "def app_shell_contract(",
            "def scene_entry_orchestrator_specs(",
            "def user_data_acceptance_nav_contract(",
            '"smart_construction_core.menu_sc_business_config_center"',
            '"ProjectDashboardSceneOrchestrator"',
        ]:
            if token not in facts_text:
                errors.append(f"hook facts module missing token: {token}")
        for forbidden in ("env[", ".search(", ".write(", ".create(", ".unlink(", "requests.", "register_", "from odoo"):
            if forbidden in facts_text:
                errors.append(f"hook facts module must remain static facts; forbidden token: {forbidden}")

    if "python3 scripts/verify/construction_core_extension_hook_facts_split_guard.py" not in ci_text:
        errors.append("ci.local.quick must run construction_core_extension_hook_facts_split_guard.py")

    if not errors:
        facts = _load(FACTS, "construction_core_extension_hook_facts_under_guard")
        if "smart_construction_core.group_sc_cap_business_config_admin" not in facts.business_config_admin_group_xmlids():
            errors.append("hook facts must preserve business config admin group")
        if facts.native_config_root_menu_xmlid() != "smart_construction_core.menu_sc_business_config_center":
            errors.append("hook facts must preserve native config root menu")
        if facts.product_policy_catalog_label({"edition_key": "preview"}) != "施工管理预览版":
            errors.append("hook facts must preserve preview product label")
        if facts.app_shell_contract().get("taxonomy", {}).get("projects", {}).get("primary_scene") != "projects.list":
            errors.append("hook facts must preserve app shell project scene")
        if "ProjectDashboardSceneOrchestrator" not in facts.scene_entry_orchestrator_specs():
            errors.append("hook facts must preserve scene orchestrator specs")
        if "客户" not in facts.user_data_acceptance_nav_contract().get("formal_group_child_labels", []):
            errors.append("hook facts must preserve user data acceptance labels")

    if errors:
        print("[construction_core_extension_hook_facts_split_guard] FAIL")
        for error in errors:
            print(f"- {error}")
        return 1
    print("[construction_core_extension_hook_facts_split_guard] PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
