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
BACKEND_BOUNDARY_FILE = ROOT / "addons/smart_core/utils/backend_contract_boundaries.py"
FRONTEND_BOUNDARY_FILE = ROOT / "frontend/apps/web/src/app/businessConfigBoundaries.ts"


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

DEPRECATED_INTENT_MARKERS = (
    "ui.menu_configuration.",
    "sc.approval_policy_configuration.",
)

EXPECTED_CAPABILITY_AUTHORING_INTENTS = {
    "menu_orchestration": {
        "ui.menu_config.panel.get",
        "ui.menu_config.panel.set",
        "ui.menu_config.menu.create",
        "ui.menu_config.menu.delete",
        "ui.menu_config.audit",
        "ui.menu_config.rollback",
        "ui.menu_config.versions",
    },
    "approval_policy_configuration": {
        "sc.approval_policy.config.get",
        "sc.approval_policy.config.set",
        "sc.approval_policy.steps.set",
    },
    "form_field_structure": {
        "ui.form_field_policy.set",
        "ui.form_custom_field.create",
        "ui.form_field_order.set",
        "ui.form_field_config.batch_set",
        "ui.business_config.lowcode.apply",
        "ui.business_config.contract.save",
        "ui.business_config.contract.get",
        "ui.business_config.contract.publish",
        "ui.business_config.contract.versions",
        "ui.business_config.contract.rollback",
    },
    "list_search_configuration": {
        "ui.business_config.list_search.audit",
        "ui.business_config.list_search.set",
        "ui.business_config.list_search.bootstrap",
        "ui.business_config.contract.save",
    },
    "version_snapshot_rollback": {
        "ui.business_config.snapshot.summary",
        "ui.business_config.snapshot.export",
        "ui.business_config.snapshot.compare",
        "ui.business_config.contract.publish",
        "ui.business_config.contract.versions",
        "ui.business_config.contract.rollback",
    },
    "capability_boundary_and_coverage": {
        "ui.business_config.surface.get",
        "ui.business_config.coverage.scan",
        "ui.business_config.coverage.bootstrap_list_search",
        "ui.business_config.coverage.bootstrap_missing",
    },
}


FULL_ACCEPTANCE_TARGETS = {
    "verify.business_config.guard_inventory",
    "verify.business_config.unit",
    "verify.frontend.build",
    "verify.business_config.coverage",
    "verify.business_config.list_config_boundary",
    "verify.business_config.snapshot",
    "verify.business_config.approval_runtime",
    "verify.business_config.browser_acceptance",
    "verify.business_config.low_code_acceptance",
    "verify.business_config.low_code_runtime_consistency",
    "verify.business_config.low_code_group_matrix",
    "verify.business_config.low_code_layout_runtime",
    "verify.business_config.low_code_menu_navigation_alignment",
    "verify.business_config.low_code_global_stability",
    "verify.user_menu.reachability.guard",
    "verify.full_product_capability_scope",
}

FULL_ACCEPTANCE_TARGETS_WITHOUT_CAPABILITY_OWNER = {
    "verify.frontend.build",
    "verify.user_menu.reachability.guard",
    "verify.full_product_capability_scope",
}

TARGET_SCRIPT_REQUIREMENTS = {
    "verify.business_config.unit": (
        "scripts/verify/business_config_user_language_guard.py",
        "scripts/verify/lowcode_config_boundary_guard.py",
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
    "verify.full_product_capability_scope": (
        "scripts/verify/full_product_capability_scope_audit.py",
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
    "verify.business_config.low_code_menu_navigation_alignment": {
        "frontend/apps/web/scripts/low_code_menu_navigation_alignment_acceptance.mjs": (
            "effectiveVisibleParentId",
            "configuredParentId",
            "policy.visible !== true",
            "navigation_config_only",
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

OBSERVABILITY_SOURCE_MARKER_REQUIREMENTS = {
    "menu configuration audit observability": {
        "addons/smart_core/handlers/menu_configuration.py": (
            '"runtime_source": runtime_source',
            '"configured_policy_count": len(policy_rows)',
            '"runtime_policy_count": len(applicable_by_menu)',
            '"contract_authoritative": runtime_source == MENU_CONFIG_RUNTIME_SOURCE_CONTRACT',
            '"applicable_policy_count": len(applicable_rows)',
            '"scope_root_valid": bool(scope_root_menu_id)',
        ),
        "frontend/apps/web/src/views/MenuConfigView.vue": (
            "auditSummary.configuredCount",
            "auditSummary.applicableCount",
            "auditSummary.runtimeSourceLabel",
            "auditMenuConfiguration",
        ),
        "addons/smart_core/tests/test_menu_configuration_audit.py": (
            "test_menu_config_audit_reports_applicable_policy_counts",
            "test_menu_config_audit_reports_runtime_contract_rows_not_legacy_policy_rows",
            "runtime_policy_count",
            "contract_authoritative",
            "scope_root_valid",
        ),
    },
    "form configuration operation observability": {
        "addons/smart_core/handlers/form_field_configuration.py": (
            "def _contract_reload_hint(",
            '"reason": "view_orchestration_config_changed"',
            '"precheck": precheck',
            '"contract_reload": _contract_reload_hint_for_record(rec)',
        ),
        "frontend/apps/web/src/pages/ContractFormPage.vue": (
            "formConfigOperationLog",
            "formatFormConfigOperationSummary",
            "lowCodePrecheckWarnings",
            "saveResult?.precheck?.warnings",
        ),
        "addons/smart_core/tests/test_form_field_configuration_params.py": (
            "test_contract_reload_hint_normalizes_scope",
            "test_business_config_contract_precheck_accepts_view_orchestration_without_legacy_objects",
            "test_business_config_contract_precheck_rejects_empty_view_orchestration_views",
        ),
    },
    "version snapshot diff observability": {
        "addons/smart_core/handlers/business_config_surface.py": (
            "BusinessConfigSnapshotCompareHandler",
            '"added_count"',
            '"removed_count"',
            '"changed_count"',
            '"previous_version_no"',
            '"current_version_no"',
        ),
        "frontend/apps/web/src/views/BusinessConfigSurfaceView.vue": (
            "snapshotCompareSummary",
            "snapshotCompareChangedRows",
            "snapshotCompareAddedRows",
            "snapshotCompareRemovedRows",
            "versionDeltaText",
        ),
        "addons/smart_core/tests/test_business_config_surface.py": (
            "test_snapshot_compare_reports_added_removed_and_changed_contracts",
            "added_count",
            "removed_count",
            "changed_count",
        ),
    },
    "low-code delivery readiness workbench": {
        "addons/smart_core/handlers/business_config_surface.py": (
            "DELIVERY_CAPABILITIES",
            "low_code_delivery_readiness.v1",
            '"delivery_readiness": self._delivery_readiness(sections, snapshot_summary)',
        ),
        "frontend/apps/web/src/api/businessConfig.ts": (
            "BusinessConfigDeliveryReadinessPayload",
            "delivery_readiness?: BusinessConfigDeliveryReadinessPayload",
        ),
        "frontend/apps/web/src/views/BusinessConfigSurfaceView.vue": (
            "data-lowcode-delivery-readiness=\"low_code_delivery_readiness.v1\"",
            "data-lowcode-workbench-ia=\"start\"",
            "data-lowcode-workbench-ia=\"three-column\"",
            "workbench-status-rail",
            "deliveryReadinessStatusText",
            "runDeliveryReadinessAction",
        ),
        "addons/smart_core/tests/test_business_config_surface.py": (
            "test_surface_delivery_readiness_marks_empty_authoring_sections_pending",
            "low_code_delivery_readiness.v1",
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
            if field == "authoring_intents":
                deprecated = [
                    str(item)
                    for item in value
                    if any(marker in str(item) for marker in DEPRECATED_INTENT_MARKERS)
                ]
                if deprecated:
                    errors.append(
                        "low-code capability %s uses deprecated authoring intents %s" % (capability_id, deprecated)
                    )
                expected_intents = EXPECTED_CAPABILITY_AUTHORING_INTENTS.get(capability_id)
                if expected_intents is not None and set(map(str, value)) != expected_intents:
                    errors.append(
                        "low-code capability %s authoring intents drifted; expected=%s actual=%s"
                        % (capability_id, sorted(expected_intents), sorted(map(str, value)))
                    )
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


def _quoted_values(path: Path) -> set[str]:
    if not path.is_file():
        return set()
    text = path.read_text(encoding="utf-8")
    return set(re.findall(r"""["']([^"']+)["']""", text))


def _validate_boundary_constant_parity(errors: list[str]) -> None:
    expected_intents = set().union(*EXPECTED_CAPABILITY_AUTHORING_INTENTS.values())
    backend_values = _quoted_values(BACKEND_BOUNDARY_FILE)
    frontend_values = _quoted_values(FRONTEND_BOUNDARY_FILE)
    missing_backend = sorted(expected_intents - backend_values)
    missing_frontend = sorted(expected_intents - frontend_values)
    if missing_backend:
        errors.append("backend business config boundary constants missing intents %s" % missing_backend)
    if missing_frontend:
        errors.append("frontend business config boundary constants missing intents %s" % missing_frontend)
    for path, values in ((BACKEND_BOUNDARY_FILE, backend_values), (FRONTEND_BOUNDARY_FILE, frontend_values)):
        deprecated = sorted(
            value
            for value in values
            if any(marker in value for marker in DEPRECATED_INTENT_MARKERS)
        )
        if deprecated:
            errors.append("%s contains deprecated low-code intents %s" % (path.relative_to(ROOT), deprecated))


def _validate_observability_source_markers(errors: list[str]) -> None:
    for capability, artifacts in OBSERVABILITY_SOURCE_MARKER_REQUIREMENTS.items():
        for artifact, markers in artifacts.items():
            path = ROOT / artifact
            if not path.is_file():
                errors.append("low-code observability %s missing artifact %s" % (capability, artifact))
                continue
            text = path.read_text(encoding="utf-8")
            for marker in markers:
                if marker not in text:
                    errors.append(
                        "low-code observability %s artifact %s missing required marker %s"
                        % (capability, artifact, marker)
                    )


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
    _validate_boundary_constant_parity(errors)
    _validate_observability_source_markers(errors)

    if errors:
        print("[business_config_guard_inventory] FAIL")
        for error in errors:
            print("- " + error)
        return 1
    print("[business_config_guard_inventory] PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
