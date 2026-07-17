#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

import importlib.util
import json
from pathlib import Path

from make_source_inventory import combined_make_source, make_logical_lines


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
                "parent_mismatch_count",
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
            "frontend/apps/web/src/views/businessConfigSurface/snapshotRemediation.ts": (
                "business_config_snapshot_remediation_plan.v1",
            ),
            "frontend/apps/web/src/views/businessConfigSurface/useBusinessConfigSnapshots.ts": (
                "downloadSnapshotRemediationPlan",
            ),
            "frontend/apps/web/src/views/businessConfigSurface/BusinessConfigAdvancedAuditPanels.vue": (
                "下载整改清单",
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
VERIFY_INDEX_DOC = ROOT / "docs" / "ops" / "verify" / "README.md"
PRODUCTION_UPGRADE_STANDARD_DOC = ROOT / "docs" / "ops" / "production_upgrade_standard_v1.md"


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
    for line in make_logical_lines(makefile_text):
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
    makefile_text, _ = combined_make_source(ROOT)
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


def _validate_lowcode_release_verification_docs(errors: list[dict]) -> None:
    makefile_text, _ = combined_make_source(ROOT)
    product_surface_deps = _target_deps(makefile_text, "verify.product.surface.clean")
    verify_index_text = _read(VERIFY_INDEX_DOC)
    production_standard_text = _read(PRODUCTION_UPGRADE_STANDARD_DOC)
    for target in (
        "verify.lowcode_config.boundary.guard",
        "verify.lowcode_config.runtime_boundary.guard",
        "verify.business_config.snapshot",
    ):
        if target not in product_surface_deps:
            errors.append({
                "category": "lowcode_release_verification_gate",
                "path": "Makefile",
                "message": "product surface gate must include the complete low-code release evidence chain",
                "target": target,
            })
    verify_index_tokens = (
        "make verify.lowcode_config.boundary.guard",
        "make verify.lowcode_config.runtime_boundary.guard",
        "make verify.business_config.snapshot",
        "lowcode_customer_config_baseline_manifest.v1",
        "LOWCODE_CONFIG_RUNTIME_SOURCE_STATUS_STRICT=1",
        "BUSINESS_CONFIG_SNAPSHOT_COMPARE_PATH",
        "smart_construction_custom",
        "source-status",
        "ordinary business",
        "global low-code configuration entries",
    )
    for token in verify_index_tokens:
        if token not in verify_index_text:
            errors.append({
                "category": "lowcode_release_verification_docs",
                "path": VERIFY_INDEX_DOC.relative_to(ROOT).as_posix(),
                "message": "verification index must document the complete low-code release evidence chain",
                "token": token,
            })
    production_standard_tokens = (
        "make verify.lowcode_config.boundary.guard",
        "make verify.lowcode_config.runtime_boundary.guard",
        "make verify.business_config.snapshot",
        "PROD_READONLY_VERIFY=1",
        "python3 scripts/verify/business_config_guard_inventory.py",
        "python3 scripts/verify/backend_contract_boundary_guard.py",
    )
    for token in production_standard_tokens:
        if token not in production_standard_text:
            errors.append({
                "category": "lowcode_release_verification_docs",
                "path": PRODUCTION_UPGRADE_STANDARD_DOC.relative_to(ROOT).as_posix(),
                "message": "production upgrade standard must require static, runtime, snapshot, and backend low-code evidence",
                "token": token,
            })


def _validate_customer_config_baseline_manifest(errors: list[dict]) -> None:
    manifest_path = ROOT / "addons" / "smart_construction_custom" / "data" / "lowcode_customer_config_baseline_manifest_v1.json"
    custom_module_path = ROOT / "addons" / "smart_construction_custom"
    if not manifest_path.is_file():
        errors.append({
            "category": "customer_config_baseline_manifest",
            "message": "customer-confirmed low-code configuration baseline manifest is missing",
            "path": manifest_path.relative_to(ROOT).as_posix(),
        })
        return
    try:
        payload = json.loads(_read(manifest_path))
    except json.JSONDecodeError as exc:
        errors.append({
            "category": "customer_config_baseline_manifest",
            "message": "customer low-code baseline manifest is invalid JSON",
            "error": str(exc),
        })
        return
    if payload.get("schema_version") != "lowcode_customer_config_baseline_manifest.v1":
        errors.append({
            "category": "customer_config_baseline_manifest",
            "message": "customer low-code baseline manifest schema_version drifted",
        })
    required_top_level = {
        "extraction_assistant",
        "module_boundary",
        "promotion_rule",
        "replayable_surfaces",
        "required_module_assets",
        "required_guards",
        "acceptance_policy",
    }
    missing_top_level = sorted(required_top_level - set(payload))
    if missing_top_level:
        errors.append({
            "category": "customer_config_baseline_manifest",
            "message": "customer low-code baseline manifest missing required sections",
            "missing": missing_top_level,
        })
    module_boundary = payload.get("module_boundary") if isinstance(payload.get("module_boundary"), dict) else {}
    if module_boundary.get("owner_module") != "smart_construction_custom":
        errors.append({
            "category": "customer_config_baseline_manifest",
            "message": "customer low-code baseline manifest must be owned by smart_construction_custom",
        })
    promotion_rule = payload.get("promotion_rule") if isinstance(payload.get("promotion_rule"), dict) else {}
    for token in ("tenant_runtime", "product_release", "smart_construction_custom"):
        if token not in json.dumps(promotion_rule, ensure_ascii=False):
            errors.append({
                "category": "customer_config_baseline_manifest",
                "message": "promotion rule must preserve low-code runtime to replayable customer baseline semantics",
                "token": token,
            })
    extraction = payload.get("extraction_assistant") if isinstance(payload.get("extraction_assistant"), dict) else {}
    expected_extraction = {
        "schema_version": "lowcode_customer_config_baseline_candidate.v1",
        "make_target": "make verify.lowcode_config.customer_baseline.candidate",
        "script": "scripts/verify/lowcode_customer_config_baseline_candidate.py",
        "artifact": "artifacts/backend/lowcode_customer_config_baseline_candidate.json",
        "module_asset_draft_schema_version": "lowcode_customer_config_module_asset_draft.v1",
        "module_asset_draft_make_target": "make verify.lowcode_config.customer_module_asset.draft",
        "module_asset_draft_script": "scripts/verify/lowcode_customer_config_module_asset_draft.py",
        "module_asset_draft_artifact": "artifacts/backend/lowcode_customer_config_module_asset_draft.json",
        "acceptance_decision_schema_version": "lowcode_customer_config_acceptance_decisions.v1",
        "acceptance_decision_template_make_target": "make verify.lowcode_config.customer_module_asset.acceptance_template",
        "acceptance_decision_template_script": "scripts/verify/lowcode_customer_config_acceptance_decision_template.py",
        "acceptance_decision_template_artifact": "artifacts/backend/lowcode_customer_config_acceptance_decisions_template.json",
        "acceptance_apply_dry_run_make_target": "make verify.lowcode_config.customer_module_asset.acceptance_apply.dry_run",
        "acceptance_apply_script": "scripts/verify/lowcode_customer_config_apply_acceptance_decisions.py",
        "acceptance_apply_dry_run_artifact": "artifacts/backend/lowcode_customer_config_contracts_candidate.json",
        "accepted_module_asset_schema_version": "lowcode_customer_config_contracts.v1",
        "accepted_module_asset": "addons/smart_construction_custom/data/lowcode_customer_config_contracts_v1.json",
        "accepted_module_asset_replay_guard": "make verify.lowcode_config.customer_module_asset.replay.guard",
        "customer_module_asset_pipeline_make_target": "make verify.lowcode_config.customer_module_asset.pipeline",
        "customer_module_asset_release_hardening_guard_make_target": "make verify.lowcode_config.customer_module_asset.release_hardening.guard",
    }
    for key, expected in expected_extraction.items():
        if extraction.get(key) != expected:
            errors.append({
                "category": "customer_config_baseline_manifest",
                "message": "customer low-code baseline manifest must declare the extraction assistant",
                "key": key,
                "expected": expected,
                "actual": extraction.get(key),
            })
    extraction_script = ROOT / expected_extraction["script"]
    if not extraction_script.is_file():
        errors.append({
            "category": "customer_config_baseline_manifest",
            "message": "customer low-code baseline extraction assistant script is missing",
            "path": expected_extraction["script"],
        })
    else:
        extraction_text = _read(extraction_script)
        for token in (
            "lowcode_customer_config_baseline_candidate.v1",
            "LOWCODE_CUSTOMER_BASELINE_SOURCE_STATUSES",
            "target_module",
            "smart_construction_custom",
            "review_required",
            "not_a_direct_module_asset",
        ):
            if token not in extraction_text:
                errors.append({
                    "category": "customer_config_baseline_extraction",
                    "message": "customer low-code baseline extraction assistant must preserve review-only module promotion semantics",
                    "token": token,
                })
    draft_script = ROOT / expected_extraction["module_asset_draft_script"]
    if not draft_script.is_file():
        errors.append({
            "category": "customer_config_baseline_manifest",
            "message": "customer low-code module asset draft script is missing",
            "path": expected_extraction["module_asset_draft_script"],
        })
    else:
        draft_text = _read(draft_script)
        for token in (
            "lowcode_customer_config_module_asset_draft.v1",
            "lowcode_customer_config_baseline_candidate.v1",
            "smart_construction_custom",
            "review_required",
            "not_applied_to_module",
            "proposed_assets",
        ):
            if token not in draft_text:
                errors.append({
                    "category": "customer_config_baseline_module_asset_draft",
                    "message": "customer low-code module asset draft must preserve review-only promotion semantics",
                    "token": token,
                })
    decision_template_script = ROOT / expected_extraction["acceptance_decision_template_script"]
    if not decision_template_script.is_file():
        errors.append({
            "category": "customer_config_baseline_manifest",
            "message": "customer low-code acceptance decision template script is missing",
            "path": expected_extraction["acceptance_decision_template_script"],
        })
    else:
        decision_template_text = _read(decision_template_script)
        for token in (
            "lowcode_customer_config_acceptance_decisions.v1",
            "lowcode_customer_config_module_asset_draft.v1",
            "review_decision_template",
            "pending",
            "accepted",
            "rejected",
            "reviewer",
            "review_note",
        ):
            if token not in decision_template_text:
                errors.append({
                    "category": "customer_config_baseline_acceptance_template",
                    "message": "customer low-code acceptance decision template must preserve manual review semantics",
                    "token": token,
                })
    acceptance_apply_script = ROOT / expected_extraction["acceptance_apply_script"]
    if not acceptance_apply_script.is_file():
        errors.append({
            "category": "customer_config_baseline_manifest",
            "message": "customer low-code acceptance apply script is missing",
            "path": expected_extraction["acceptance_apply_script"],
        })
    else:
        acceptance_apply_text = _read(acceptance_apply_script)
        for token in (
            "lowcode_customer_config_acceptance_decisions.v1",
            "lowcode_customer_config_contracts.v1",
            "LOWCODE_CUSTOMER_CONFIG_APPLY_ACCEPTANCE",
            "LOWCODE_CUSTOMER_CONFIG_ACCEPTED_ASSET_OUTPUT",
            "accepted",
            "reviewer",
            "review_note",
            "payload_hash",
            "tenant_runtime",
            "apply_to_module",
        ):
            if token not in acceptance_apply_text:
                errors.append({
                    "category": "customer_config_baseline_acceptance_apply",
                    "message": "customer low-code acceptance apply script must preserve explicit manual acceptance semantics",
                    "token": token,
                })
    acceptance_apply_test = ROOT / "scripts" / "verify" / "lowcode_customer_config_apply_acceptance_decisions_test.py"
    if not acceptance_apply_test.is_file():
        errors.append({
            "category": "customer_config_baseline_acceptance_apply",
            "message": "customer low-code acceptance apply safety tests are missing",
        })
    else:
        acceptance_apply_test_text = _read(acceptance_apply_test)
        for token in (
            "test_accepts_reviewed_matching_tenant_runtime_record",
            "test_pending_decision_does_not_enter_asset",
            "test_rejects_accepted_without_reviewer",
            "test_rejects_accepted_without_review_note",
            "test_rejects_payload_hash_mismatch",
            "test_rejects_non_tenant_runtime_record",
            "test_rejects_unknown_decision",
            "test_rejects_duplicate_decisions",
        ):
            if token not in acceptance_apply_test_text:
                errors.append({
                    "category": "customer_config_baseline_acceptance_apply",
                    "message": "customer low-code acceptance apply safety tests must cover strict acceptance gates",
                    "token": token,
                })
    accepted_asset_path = ROOT / expected_extraction["accepted_module_asset"]
    if not accepted_asset_path.is_file():
        errors.append({
            "category": "customer_config_baseline_manifest",
            "message": "accepted customer low-code module asset is missing",
            "path": expected_extraction["accepted_module_asset"],
        })
    else:
        try:
            accepted_asset = json.loads(_read(accepted_asset_path))
        except json.JSONDecodeError as exc:
            errors.append({
                "category": "customer_config_baseline_module_asset",
                "message": "accepted customer low-code module asset is invalid JSON",
                "error": str(exc),
            })
            accepted_asset = {}
        for key, expected in (
            ("schema_version", "lowcode_customer_config_contracts.v1"),
            ("source_draft_schema", "lowcode_customer_config_module_asset_draft.v1"),
            ("target_module", "smart_construction_custom"),
            ("artifact_status", "accepted_module_asset"),
        ):
            if accepted_asset.get(key) != expected:
                errors.append({
                    "category": "customer_config_baseline_module_asset",
                    "message": "accepted customer low-code module asset metadata drifted",
                    "key": key,
                    "expected": expected,
                    "actual": accepted_asset.get(key),
                })
    replay_guard_path = ROOT / "scripts" / "verify" / "lowcode_customer_config_module_asset_replay_guard.py"
    if not replay_guard_path.is_file():
        errors.append({
            "category": "customer_config_baseline_module_asset",
            "message": "accepted customer low-code module asset replay guard is missing",
        })
    surfaces = payload.get("replayable_surfaces") if isinstance(payload.get("replayable_surfaces"), list) else []
    surface_names = {str(item.get("surface") or "").strip() for item in surfaces if isinstance(item, dict)}
    for surface in ("menu_preferences", "form_preferences", "user_data_baseline"):
        if surface not in surface_names:
            errors.append({
                "category": "customer_config_baseline_manifest",
                "message": "customer low-code baseline manifest missing replayable surface",
                "surface": surface,
            })
    for item in surfaces:
        if not isinstance(item, dict):
            errors.append({
                "category": "customer_config_baseline_manifest",
                "message": "customer low-code baseline manifest replayable surface must be an object",
                "surface": item,
            })
            continue
        surface = str(item.get("surface") or "").strip()
        if not surface:
            errors.append({
                "category": "customer_config_baseline_manifest",
                "message": "customer low-code baseline manifest replayable surface must be named",
            })
            continue
        for key in ("runtime_carriers", "baseline_carrier", "install_hook"):
            value = item.get(key)
            if not value or (isinstance(value, list) and not all(str(entry).strip() for entry in value)):
                errors.append({
                    "category": "customer_config_baseline_manifest",
                    "message": "customer low-code baseline manifest replayable surface missing binding field",
                    "surface": surface,
                    "field": key,
                })
        if surface == "form_preferences":
            markers = item.get("source_markers")
            if not isinstance(markers, list) or not all(str(marker).strip() for marker in markers):
                errors.append({
                    "category": "customer_config_baseline_manifest",
                    "message": "form preferences surface must declare replayable source markers",
                    "surface": surface,
                })
        elif not str(item.get("source_marker") or "").strip():
            errors.append({
                "category": "customer_config_baseline_manifest",
                "message": "customer low-code baseline manifest replayable surface missing source marker",
                "surface": surface,
            })
    required_assets = payload.get("required_module_assets") if isinstance(payload.get("required_module_assets"), list) else []
    for rel_path in required_assets:
        path = ROOT / str(rel_path)
        if not path.is_file():
            errors.append({
                "category": "customer_config_baseline_manifest",
                "message": "customer low-code baseline manifest references missing asset",
                "path": str(rel_path),
            })
    custom_manifest_text = _read(custom_module_path / "__manifest__.py")
    for asset in (
        '"data/user_data_baseline.xml"',
        '"data/user_preferences.xml"',
        '"data/user_menu_preferences.xml"',
        '"post_init_hook": "post_init_hook"',
    ):
        if asset not in custom_manifest_text:
            errors.append({
                "category": "customer_config_baseline_module_binding",
                "message": "smart_construction_custom manifest must install the customer low-code baseline binding",
                "asset": asset,
            })
    custom_hook_text = _read(custom_module_path / "hooks.py")
    for token in (
        "def apply_user_preferences",
        "apply_user_menu_preferences()",
        "apply_user_form_preferences()",
        "apply_customer_lowcode_contract_assets()",
        "backfill_lowcode_contract_source_status(env)",
        "def apply_user_data_baseline",
        "apply_user_data_baseline()",
        "def post_init_hook",
    ):
        if token not in custom_hook_text:
            errors.append({
                "category": "customer_config_baseline_hook_binding",
                "message": "smart_construction_custom hooks must replay customer low-code baselines on fresh install",
                "token": token,
            })
    user_pref_xml = _read(custom_module_path / "data" / "user_preferences.xml")
    if 'model="sc.user.preference.initialization" name="apply_user_form_preferences"' not in user_pref_xml:
        errors.append({
            "category": "customer_config_baseline_xml_binding",
            "message": "user_preferences.xml must replay form preferences during module install/update",
        })
    user_menu_pref_xml = _read(custom_module_path / "data" / "user_menu_preferences.xml")
    for token in (
        'model="sc.user.preference.initialization" name="apply_user_menu_preferences"',
        'model="sc.user.preference.initialization" name="backfill_lowcode_contract_source_status"',
        'model="sc.user.preference.initialization" name="enforce_product_menu_runtime_cleanup"',
    ):
        if token not in user_menu_pref_xml:
            errors.append({
                "category": "customer_config_baseline_xml_binding",
                "message": "user_menu_preferences.xml must replay menu preferences and cleanup/backfill during module install/update",
                "token": token,
            })
    user_pref_model_text = _read(custom_module_path / "models" / "user_preferences.py")
    for token in (
        'PARTNER_FORM_PREFERENCE_SOURCE = "smart_construction_custom.partner_form_preference"',
        'USER_FORM_PREFERENCE_SOURCE = "smart_construction_custom.user_form_preference"',
        '"productization_source": "smart_construction_custom.user_menu_preference"',
        'CUSTOMER_LOWCODE_CONTRACT_ASSET_SOURCE = "smart_construction_custom.lowcode_customer_config_contracts"',
        "apply_customer_lowcode_contract_assets",
        "_upsert_customer_lowcode_contract_asset_record",
        "ensure_lowcode_contract_source_status",
        "_upsert_form_contract",
    ):
        if token not in user_pref_model_text:
            errors.append({
                "category": "customer_config_baseline_source_binding",
                "message": "customer low-code baseline generators must stamp replayable source markers and contract status",
                "token": token,
            })
    required_guards = set(map(str, payload.get("required_guards") if isinstance(payload.get("required_guards"), list) else []))
    for guard in (
        "make verify.lowcode_config.boundary.guard",
        "make verify.lowcode_config.runtime_boundary.guard",
        "make verify.lowcode_config.customer_baseline.candidate",
        "make verify.lowcode_config.customer_module_asset.draft",
        "make verify.lowcode_config.customer_module_asset.acceptance_template",
        "make verify.lowcode_config.customer_module_asset.acceptance_apply.dry_run",
        "make verify.lowcode_config.customer_module_asset.pipeline",
        "make verify.lowcode_config.customer_module_asset.release_hardening.guard",
        "make verify.lowcode_config.customer_module_asset.replay.guard",
        "make verify.business_config.unit",
        "make verify.business_config.snapshot",
    ):
        if guard not in required_guards:
            errors.append({
                "category": "customer_config_baseline_manifest",
                "message": "customer low-code baseline manifest must require guard",
                "guard": guard,
            })
    acceptance_policy = payload.get("acceptance_policy") if isinstance(payload.get("acceptance_policy"), dict) else {}
    for policy in ("fresh_install", "upgrade", "runtime", "cross_environment"):
        if not str(acceptance_policy.get(policy) or "").strip():
            errors.append({
                "category": "customer_config_baseline_manifest",
                "message": "customer low-code baseline manifest must define acceptance policy",
                "policy": policy,
            })


def _validate_menu_config_runtime_authority(errors: list[dict]) -> None:
    frontend_path = ROOT / "frontend" / "apps" / "web" / "src" / "views" / "MenuConfigView.vue"
    handler_path = ROOT / "addons" / "smart_core" / "handlers" / "menu_configuration.py"
    runtime_path = ROOT / "addons" / "smart_core" / "model" / "ui_menu_config_policy.py"
    delivery_path = ROOT / "addons" / "smart_core" / "delivery" / "menu_service.py"
    defaults_path = ROOT / "addons" / "smart_core" / "core" / "delivery_menu_defaults.py"

    frontend_text = _read(frontend_path)
    handler_text = _read(handler_path)
    runtime_text = _read(runtime_path)
    delivery_text = _read(delivery_path)
    defaults_text = _read(defaults_path)

    frontend_forbidden = {
        "appShellVisibleMenuIds": "front-end must not infer menu runtime state from AppShell rendered ids",
        "appShellVisibleLabels": "front-end must not infer menu runtime state from AppShell rendered labels",
        "alignRuntimeStateWithAppShellNavigation": "front-end must not synthesize runtime states",
        "collectRuntimeVisibleLabelsFromNav": "front-end must not label-match final navigation",
        "canMatchNavigationGroupByLabel": "front-end must not map navigation groups by label",
        "visible_app_shell_navigation": "front-end must not invent AppShell visibility reasons",
        "menuId < 800000000": "front-end must not classify synthetic menu ids by numeric ranges",
        "menuId >= 800000000": "front-end must not classify synthetic menu ids by numeric ranges",
    }
    for token, message in frontend_forbidden.items():
        if token in frontend_text:
            errors.append({
                "category": "menu_config_frontend_runtime_authority",
                "path": frontend_path.relative_to(ROOT).as_posix(),
                "message": message,
                "token": token,
            })

    for token in (
        "navConfigMenuId",
        "config_menu_id",
        "config_ref",
        "runtimeState.value = payload.runtime || null",
        "runtimeNavigationTreeFromPayload(payload)",
        "payload.runtime?.tree",
        "throw new Error('菜单配置缺少最终运行时导航树，已阻止回退到原生菜单结构。')",
    ):
        if token not in frontend_text:
            errors.append({
                "category": "menu_config_frontend_runtime_authority",
                "path": frontend_path.relative_to(ROOT).as_posix(),
                "message": "menu config front-end must consume backend navigation/config/runtime facts directly",
                "token": token,
            })
    runtime_tree_function = frontend_text[
        frontend_text.find("function runtimeNavigationTreeFromPayload"):
        frontend_text.find("function collectNavigationMenuIds")
    ]
    if "scopedNavigationTree()" in runtime_tree_function:
        errors.append({
            "category": "menu_config_frontend_runtime_authority",
            "path": frontend_path.relative_to(ROOT).as_posix(),
            "message": "menu config display tree must fail closed when backend runtime.tree is missing, not fall back to session/AppShell navigation",
            "token": "scopedNavigationTree()",
        })

    handler_forbidden = {
        "menu_labels_by_id": "runtime navigation state must not map release groups by label",
        "label_to_configured_ids": "runtime navigation state must not map release groups by label",
        "matched_by_release_group": "runtime navigation state must be driven by config_menu_id/config_ref, not label matching",
    }
    for token, message in handler_forbidden.items():
        if token in handler_text:
            errors.append({
                "category": "menu_config_backend_runtime_authority",
                "path": handler_path.relative_to(ROOT).as_posix(),
                "message": message,
                "token": token,
            })

    for token in (
        "def _nav_node_config_menu_id",
        "node.get(\"config_menu_id\")",
        "meta.get(\"config_menu_id\")",
        "config_ref.get(\"id\")",
        "runtime[\"tree\"] = nav_tree",
    ):
        if token not in handler_text:
            errors.append({
                "category": "menu_config_backend_runtime_authority",
                "path": handler_path.relative_to(ROOT).as_posix(),
                "message": "menu config runtime states must be keyed by backend explicit config references",
                "token": token,
            })

    for token in (
        "annotate_config_contract_node",
        "config_menu_id",
        "configurable",
        "config_ref",
        "node_kind",
    ):
        if token not in runtime_text:
            errors.append({
                "category": "menu_config_backend_runtime_authority",
                "path": runtime_path.relative_to(ROOT).as_posix(),
                "message": "final navigation overlay must annotate every node with backend config contract facts",
                "token": token,
            })

    for token in (
        "_native_group_config_menu_ids_by_label",
        "build_delivery_menu_group",
        "config_menu_id=int(row.get(\"config_menu_id\") or 0)",
    ):
        if token not in delivery_text:
            errors.append({
                "category": "menu_config_delivery_group_authority",
                "path": delivery_path.relative_to(ROOT).as_posix(),
                "message": "delivery navigation groups must resolve real Odoo group menu references in backend",
                "token": token,
            })

    for token in (
        "config_menu_id: int = 0",
        "\"node_kind\": \"navigation_group\"",
        "\"configurable\": bool(config_menu_id)",
        "meta[\"config_ref\"] = {\"model\": \"ir.ui.menu\", \"id\": config_menu_id}",
        "node[\"config_ref\"] = {\"model\": \"ir.ui.menu\", \"id\": config_menu_id}",
    ):
        if token not in defaults_text:
            errors.append({
                "category": "menu_config_delivery_group_authority",
                "path": defaults_path.relative_to(ROOT).as_posix(),
                "message": "delivery menu defaults must expose group configurability as backend facts",
                "token": token,
            })


def build_report() -> dict:
    errors: list[dict] = []
    boundaries = _load_boundaries()
    source_statuses = set(getattr(boundaries, "LOWCODE_SOURCE_STATUSES", set()))
    system_config_menu_xmlids = set(getattr(boundaries, "LOWCODE_SYSTEM_CONFIG_MENU_XMLIDS", set()))
    capability_ids = _validate_lowcode_capability_boundaries(errors)
    _validate_customer_config_baseline_manifest(errors)
    _validate_lowcode_release_verification_docs(errors)
    _validate_menu_config_runtime_authority(errors)

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
    runtime_guard_text = _read(ROOT / "scripts" / "verify" / "lowcode_config_runtime_boundary_guard.py")
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
    for token in (
        "LOWCODE_SYSTEM_CONFIG_MENU_XMLIDS_PARAM",
        "smart_core_lowcode_system_config_menu_xmlids",
        "smart_core_lowcode_config_recovery_parent_menu_xmlids",
        "_lowcode_system_config_menu_xmlids",
        "_lowcode_global_config_entry_xmlids",
    ):
        if token not in runtime_guard_text:
            errors.append({
                "category": "runtime_boundary_guard_source",
                "message": "runtime low-code boundary guard must use the same protected config menu sources as runtime overlay",
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

    construction_extension_text = "\n".join((
        _read(ROOT / "addons" / "smart_construction_core" / "core_extension.py"),
        _read(ROOT / "addons" / "smart_construction_core" / "core_extension_hook_facts.py"),
    ))
    construction_init_text = _read(ROOT / "addons" / "smart_construction_core" / "__init__.py")
    for token in (
        "def smart_core_lowcode_system_config_menu_xmlids",
        "def smart_core_lowcode_config_recovery_parent_menu_xmlids",
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
    if "smart_core_lowcode_config_recovery_parent_menu_xmlids" not in construction_init_text:
        errors.append({
            "category": "industry_lowcode_config_recovery_hook",
            "message": "industry module must export the low-code recovery parent menu hook",
        })

    makefile_text, _ = combined_make_source(ROOT)
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
    negative_deps = _target_deps(
        "verify.business_config.full_acceptance: verify.business_config.unit",
        "verify.business_config.full_acceptance",
    )
    negative_self_test_passed = "verify.business_config.low_code_acceptance" not in negative_deps
    report["negative_self_test"] = "pass" if negative_self_test_passed else "fail"
    if not negative_self_test_passed:
        report["errors"].append({
            "category": "negative_self_test",
            "message": "deliberately incomplete acceptance aggregate was not detected",
        })
        report["error_count"] = len(report["errors"])
    print(json.dumps(report, ensure_ascii=False, sort_keys=True))
    if report["error_count"]:
        print("[lowcode_config_boundary_guard] FAIL")
        return 1
    print("[lowcode_config_boundary_guard] PASS negative_self_test=PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
