#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Guard the low-code business config verification inventory."""

from __future__ import annotations

import re
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
MAKEFILE = ROOT / "Makefile"


FULL_ACCEPTANCE_TARGETS = {
    "verify.business_config.guard_inventory",
    "verify.business_config.unit",
    "verify.frontend.build",
    "verify.business_config.coverage",
    "verify.business_config.snapshot",
    "verify.business_config.approval_runtime",
    "verify.business_config.browser_acceptance",
    "verify.business_config.low_code_acceptance",
    "verify.business_config.low_code_runtime_consistency",
    "verify.business_config.low_code_group_matrix",
    "verify.business_config.low_code_global_stability",
}

TARGET_SCRIPT_REQUIREMENTS = {
    "verify.business_config.unit": (
        "scripts/verify/business_config_user_language_guard.py",
        "scripts/verify/backend_contract_boundary_guard.py",
        "addons/smart_core/tests/test_backend_contract_boundaries.py",
        "addons/smart_core/tests/test_backend_contract_boundary_guard.py",
        "addons/smart_core/tests/test_business_config_contract_schema.py",
        "addons/smart_core/tests/test_api_data_write_id_boundaries.py",
        "addons/smart_core/tests/test_form_field_configuration_params.py",
        "addons/smart_core/tests/test_business_config_surface.py",
        "addons/smart_core/tests/test_menu_configuration_audit.py",
        "addons/smart_construction_core/tests/test_approval_policy_configuration_handler.py",
    ),
    "verify.business_config.coverage": (
        "scripts/verify/business_config_coverage_gate.py",
    ),
    "verify.business_config.snapshot": (
        "scripts/verify/business_config_contract_snapshot.py",
    ),
    "verify.business_config.approval_runtime": (
        "scripts/verify/business_config_approval_runtime_smoke.py",
    ),
    "verify.business_config.browser_acceptance": (
        "scripts/verify/business_config_runtime_routes_browser_acceptance.mjs",
    ),
    "verify.business_config.low_code_acceptance": (
        "scripts/low_code_business_config_acceptance.mjs|frontend/apps/web/scripts/low_code_business_config_acceptance.mjs",
    ),
    "verify.business_config.low_code_runtime_consistency": (
        "scripts/low_code_form_runtime_consistency_acceptance.mjs|frontend/apps/web/scripts/low_code_form_runtime_consistency_acceptance.mjs",
    ),
    "verify.business_config.low_code_group_matrix": (
        "scripts/low_code_form_group_matrix_acceptance.mjs|frontend/apps/web/scripts/low_code_form_group_matrix_acceptance.mjs",
    ),
    "verify.business_config.low_code_global_stability": (
        "scripts/low_code_global_stability_acceptance.mjs|frontend/apps/web/scripts/low_code_global_stability_acceptance.mjs",
    ),
}


def _target_line(makefile: str, target: str) -> str:
    pattern = re.compile(rf"^{re.escape(target)}\s*:(?P<deps>[^\n]*)$", re.MULTILINE)
    match = pattern.search(makefile)
    return match.group("deps").strip() if match else ""


def _target_body(makefile: str, target: str) -> str:
    pattern = re.compile(
        rf"^{re.escape(target)}\s*:[^\n]*\n(?P<body>(?:\t[^\n]*\n|[ \t]*\n)*)",
        re.MULTILINE,
    )
    match = pattern.search(makefile)
    return match.group("body") if match else ""


def _deps(line: str) -> set[str]:
    return {item.strip() for item in line.split() if item.strip()}


def main() -> int:
    makefile = MAKEFILE.read_text(encoding="utf-8")
    errors: list[str] = []

    full_deps = _deps(_target_line(makefile, "verify.business_config.full_acceptance"))
    missing = sorted(FULL_ACCEPTANCE_TARGETS - full_deps)
    extra = sorted(full_deps - FULL_ACCEPTANCE_TARGETS)
    if missing or extra:
        errors.append(
            "verify.business_config.full_acceptance dependencies drifted; "
            "missing=%s extra=%s" % (missing, extra)
        )

    for target, scripts in TARGET_SCRIPT_REQUIREMENTS.items():
        body = _target_body(makefile, target)
        if not body:
            errors.append("Makefile missing command body for %s" % target)
            continue
        for requirement in scripts:
            invoke, _, artifact = requirement.partition("|")
            artifact = artifact or invoke
            if invoke not in body:
                errors.append("%s does not invoke %s" % (target, invoke))
            if not (ROOT / artifact).is_file():
                errors.append("missing verification artifact %s" % artifact)

    guard_body = _target_body(makefile, "verify.business_config.guard_inventory")
    if "scripts/verify/business_config_guard_inventory.py" not in guard_body:
        errors.append("verify.business_config.guard_inventory is not wired to its script")

    if errors:
        print("[business_config_guard_inventory] FAIL")
        for error in errors:
            print("- " + error)
        return 1
    print("[business_config_guard_inventory] PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
