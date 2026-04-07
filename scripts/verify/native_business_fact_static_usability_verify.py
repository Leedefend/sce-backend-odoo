#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]


def _must_exist(paths: list[str], label: str) -> None:
    missing = [path for path in paths if not (REPO_ROOT / path).is_file()]
    if missing:
        joined = ", ".join(missing)
        raise RuntimeError(f"[{label}] missing required files: {joined}")


def _must_contain(path: str, needles: list[str], label: str) -> None:
    file_path = REPO_ROOT / path
    if not file_path.is_file():
        raise RuntimeError(f"[{label}] file not found: {path}")
    text = file_path.read_text(encoding="utf-8")
    missing = [needle for needle in needles if needle not in text]
    if missing:
        joined = ", ".join(missing)
        raise RuntimeError(f"[{label}] file {path} missing required markers: {joined}")


def main() -> None:
    _must_exist(
        [
            "docs/audit/native/native_foundation_acceptance_matrix_v1.md",
            "docs/audit/native/native_manifest_load_chain_audit_v1.md",
            "docs/audit/native/native_menu_action_health_check_v1.md",
            "docs/audit/native/module_init_bootstrap_audit_v1.md",
            "docs/audit/native/master_data_field_binding_audit_v1.md",
            "docs/audit/native/role_capability_acl_rule_matrix_v1.md",
            "docs/audit/native/native_foundation_blockers_v1.md",
        ],
        label="native_audit_bundle",
    )

    _must_exist(
        [
            "addons/smart_core/controllers/intent_dispatcher.py",
            "addons/smart_core/controllers/platform_scenes_api.py",
            "addons/smart_construction_core/models/core/project_core.py",
            "addons/smart_construction_core/models/support/task_extend.py",
            "addons/smart_construction_core/models/core/project_budget.py",
            "addons/smart_construction_core/models/core/cost_domain.py",
            "addons/smart_construction_core/models/support/project_dictionary.py",
        ],
        label="business_fact_files",
    )

    _must_contain(
        "addons/smart_core/controllers/intent_dispatcher.py",
        ["@http.route('/api/v1/intent'", "def handle_intent"],
        label="native_entry_route",
    )
    _must_contain(
        "addons/smart_core/controllers/platform_scenes_api.py",
        ["@http.route(\"/api/scenes/my\"", "def my_scenes"],
        label="legacy_entry_route",
    )

    print("[native_business_fact_static_usability_verify] PASS")


if __name__ == "__main__":
    main()
