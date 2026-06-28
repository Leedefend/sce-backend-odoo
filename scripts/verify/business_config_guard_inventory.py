#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Guard the low-code business config verification inventory."""

from __future__ import annotations

import re
import sys
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
MAKEFILE = ROOT / "Makefile"
CAPABILITY_MATRIX = ROOT / "docs/architecture/low_code_business_config_capability_matrix_v1.json"


CAPABILITY_REQUIRED_FIELDS = {
    "id",
    "surface",
    "user_goal",
    "carrier",
    "authoring_intents",
    "runtime_consumers",
    "preview",
    "publish_versioning",
    "rollback",
    "audit",
    "acceptance",
    "status",
    "release_blockers",
}

CAPABILITY_STATUS_VALUES = {"ready", "partial", "blocked", "deferred"}


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
    "verify.business_config.low_code_layout_runtime",
    "verify.business_config.low_code_menu_navigation_alignment",
    "verify.business_config.low_code_global_stability",
}

FULL_ACCEPTANCE_TARGETS_WITHOUT_CAPABILITY_OWNER = {
    "verify.frontend.build",
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
    "verify.business_config.low_code_layout_runtime": (
        "scripts/low_code_form_layout_runtime_acceptance.mjs|frontend/apps/web/scripts/low_code_form_layout_runtime_acceptance.mjs",
    ),
    "verify.business_config.low_code_menu_navigation_alignment": (
        "scripts/low_code_menu_navigation_alignment_acceptance.mjs|frontend/apps/web/scripts/low_code_menu_navigation_alignment_acceptance.mjs",
    ),
    "verify.business_config.low_code_global_stability": (
        "scripts/low_code_global_stability_acceptance.mjs|frontend/apps/web/scripts/low_code_global_stability_acceptance.mjs",
    ),
}

TARGET_SOURCE_MARKER_REQUIREMENTS = {
    "verify.business_config.low_code_acceptance": {
        "frontend/apps/web/scripts/low_code_business_config_acceptance.mjs": (
            "auditLowCodeBoundaryParity",
            "boundaryParity",
            "FRONTEND_BOUNDARY_FILE",
            "BACKEND_BOUNDARY_FILE",
            "operationLogHasTechnicalFieldAfterDrag",
            "operationLogGroupColumnEntryCountAfterDrag",
            "defaultVersionGuideCount",
            "defaultVersionCurrentBadgeCount",
            "leakedDefaultVersionTerms",
            "listSearchAuditBoundary",
            "userPreferenceBoundary",
            "sc.user.view.preference",
            "approvalConfigEnvelope",
            "approvalBoundary",
            "approval_policy",
            "industry_policy_runtime",
        ),
    },
    "verify.business_config.low_code_layout_runtime": {
        "frontend/apps/web/scripts/low_code_form_layout_runtime_acceptance.mjs": (
            "DEFAULT_LAYOUT_SAMPLES",
            "LOW_CODE_LAYOUT_SAMPLES_JSON",
            "construction.contract",
            "sc.general.contract",
            "sampleCount",
        ),
    },
    "verify.business_config.low_code_global_stability": {
        "frontend/apps/web/scripts/low_code_global_stability_acceptance.mjs": (
            "sanitizedContractJson",
            "legacy_lowcode_draft",
            "contract_json: sanitizedContractJson",
        ),
    },
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


def _validate_capability_matrix(makefile: str, errors: list[str]) -> None:
    if not CAPABILITY_MATRIX.is_file():
        errors.append("missing low-code capability matrix %s" % CAPABILITY_MATRIX.relative_to(ROOT))
        return
    try:
        matrix = json.loads(CAPABILITY_MATRIX.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        errors.append("invalid low-code capability matrix json: %s" % exc)
        return
    if matrix.get("schema_version") != "low_code_business_config_capability_matrix.v1":
        errors.append("low-code capability matrix schema_version drifted")
    capabilities = matrix.get("capabilities")
    if not isinstance(capabilities, list) or not capabilities:
        errors.append("low-code capability matrix has no capabilities")
        return
    target_names = {
        match.group("target")
        for match in re.finditer(r"^(?P<target>[A-Za-z0-9_.-]+)\s*:", makefile, re.MULTILINE)
    }
    seen_ids: set[str] = set()
    matrix_acceptance_targets: set[str] = set()
    for index, capability in enumerate(capabilities):
        if not isinstance(capability, dict):
            errors.append("low-code capability matrix item %s is not an object" % index)
            continue
        capability_id = str(capability.get("id") or "").strip()
        if not capability_id:
            errors.append("low-code capability matrix item %s missing id" % index)
            continue
        if capability_id in seen_ids:
            errors.append("duplicate low-code capability id %s" % capability_id)
        seen_ids.add(capability_id)
        missing_fields = sorted(CAPABILITY_REQUIRED_FIELDS - set(capability))
        if missing_fields:
            errors.append("low-code capability %s missing fields %s" % (capability_id, missing_fields))
        status = str(capability.get("status") or "").strip()
        if status not in CAPABILITY_STATUS_VALUES:
            errors.append("low-code capability %s has invalid status %s" % (capability_id, status))
        for field in ("carrier", "authoring_intents", "runtime_consumers", "acceptance", "release_blockers"):
            value = capability.get(field)
            if not isinstance(value, list):
                errors.append("low-code capability %s field %s must be a list" % (capability_id, field))
                continue
            if field != "release_blockers" and not value:
                errors.append("low-code capability %s field %s must not be empty" % (capability_id, field))
        for target in capability.get("acceptance") or []:
            target_name = str(target or "").strip()
            if target_name.startswith("verify.") and target_name not in target_names:
                errors.append("low-code capability %s references missing acceptance target %s" % (capability_id, target_name))
            if target_name.startswith("verify.business_config."):
                matrix_acceptance_targets.add(target_name)
        blockers = capability.get("release_blockers") if isinstance(capability.get("release_blockers"), list) else []
        if status == "ready" and blockers:
            errors.append("low-code capability %s is ready but still has release_blockers" % capability_id)
    missing_matrix_targets = sorted(
        (FULL_ACCEPTANCE_TARGETS - FULL_ACCEPTANCE_TARGETS_WITHOUT_CAPABILITY_OWNER) - matrix_acceptance_targets
    )
    if missing_matrix_targets:
        errors.append("low-code capability matrix does not own full acceptance targets %s" % missing_matrix_targets)


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

    for target, artifacts in TARGET_SOURCE_MARKER_REQUIREMENTS.items():
        for artifact, markers in artifacts.items():
            path = ROOT / artifact
            if not path.is_file():
                errors.append("missing verification artifact %s" % artifact)
                continue
            text = path.read_text(encoding="utf-8")
            for marker in markers:
                if marker not in text:
                    errors.append("%s artifact %s missing required marker %s" % (target, artifact, marker))

    guard_body = _target_body(makefile, "verify.business_config.guard_inventory")
    if "scripts/verify/business_config_guard_inventory.py" not in guard_body:
        errors.append("verify.business_config.guard_inventory is not wired to its script")

    _validate_capability_matrix(makefile, errors)

    if errors:
        print("[business_config_guard_inventory] FAIL")
        for error in errors:
            print("- " + error)
        return 1
    print("[business_config_guard_inventory] PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
