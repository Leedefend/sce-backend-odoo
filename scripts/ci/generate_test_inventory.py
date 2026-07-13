#!/usr/bin/env python3
from __future__ import annotations

import csv
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_OUTPUT = ROOT / "docs" / "engineering_convergence" / "test_inventory.csv"

SCAN_ROOTS = [
    ROOT / "scripts" / "audit",
    ROOT / "scripts" / "ci",
    ROOT / "scripts" / "diag",
    ROOT / "scripts" / "e2e",
    ROOT / "scripts" / "migration",
    ROOT / "scripts" / "ops",
    ROOT / "scripts" / "prod",
    ROOT / "scripts" / "verify",
    ROOT / "frontend" / "apps" / "web" / "scripts",
]

VALID_EXTENSIONS = {".py", ".js", ".cjs", ".mjs", ".sh"}
KEYWORDS = (
    "test",
    "verify",
    "guard",
    "acceptance",
    "smoke",
    "audit",
    "contract",
    "e2e",
)

MANUAL_ENTRIES = [
    {
        "id": "T-GATE-000",
        "layer": "gate",
        "entrypoint": "make ci.local.quick",
        "purpose": (
            "Local inner-loop gate for frontend and architecture-boundary iteration, "
            "covering split-plan growth locks, frontend contract boundary guards, lint, "
            "strict typecheck, and whitespace checks."
        ),
        "estimated_runtime": "<5m",
        "owner": "frontend owner",
        "status": "active",
        "decision_gate": "local_iteration",
        "disposition": "canonical_entry",
        "aggregate_target": "make ci.local.quick",
        "notes": "Use during small local iterations; does not replace the full PR gate.",
    },
    {
        "id": "T-GATE-001",
        "layer": "gate",
        "entrypoint": "make ci",
        "purpose": "PR quality gate combining secret scan, Python syntax, frontend checks, and contract checks.",
        "estimated_runtime": "10-15m",
        "owner": "test owner",
        "status": "active",
        "decision_gate": "pr_required",
        "disposition": "canonical_entry",
        "aggregate_target": "make ci",
        "notes": "Mandatory local and GitHub PR gate.",
    },
    {
        "id": "T-GATE-002",
        "layer": "e2e",
        "entrypoint": "make test.e2e",
        "purpose": "Full browser productization acceptance.",
        "estimated_runtime": "30-60m",
        "owner": "qa owner",
        "status": "active",
        "decision_gate": "release_required",
        "disposition": "canonical_entry",
        "aggregate_target": "make test.e2e",
        "notes": "Release/full verification gate, not required for every small PR.",
    },
    {
        "id": "T-ODOO-001",
        "layer": "odoo_integration",
        "entrypoint": "make test.odoo.integration",
        "purpose": "Odoo smoke and runtime integration gate through existing ci.smoke target.",
        "estimated_runtime": "30-60m",
        "owner": "backend owner",
        "status": "active",
        "decision_gate": "integration_required",
        "disposition": "canonical_entry",
        "aggregate_target": "make test.odoo.integration",
        "notes": "Requires Docker/Odoo runtime.",
    },
    {
        "id": "T-E2E-ODOO-001",
        "layer": "e2e",
        "entrypoint": "make test.e2e.fixed_data.odoo",
        "purpose": (
            "Fixed-data Odoo post-test gate for BOQ import, BOQ-to-WBS/task generation, "
            "and settlement approval journeys."
        ),
        "estimated_runtime": "10-30m",
        "owner": "qa owner",
        "status": "active",
        "decision_gate": "release_required",
        "disposition": "canonical_entry",
        "aggregate_target": "make test.e2e.fixed_data.odoo",
        "notes": "Runs TEST_TAGS=e2e_fixed_journey on a clean Odoo test database.",
    },
]

AUTO_SCAN_EXCLUDED: set[str] = set()


def classify_layer(path: Path) -> str:
    text = path.as_posix().lower()
    name = path.name.lower()
    if "/e2e/" in text or "full_browser" in name or "browser" in name:
        return "e2e"
    if "/migration/" in text or "asset_verify" in name or "replay" in name:
        return "data_migration"
    if "contract" in name or "schema" in name or "intent" in name:
        return "contract"
    if "permission" in name or "role" in name or "auth" in name:
        return "security"
    if "/ops/" in text or "/prod/" in text or "runtime" in name or "deploy" in name:
        return "odoo_integration"
    if "/frontend/apps/web/scripts/" in text:
        return "frontend_acceptance"
    if "audit" in name or "guard" in name or "verify" in name:
        return "governance"
    return "unit"


def _read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8", errors="ignore").lower()
    except OSError:
        return ""


def runtime_class(path: Path, layer: str) -> str:
    name = path.name.lower()
    if layer == "e2e" or "full_browser" in name:
        return "30-60m"
    if layer in {"odoo_integration", "data_migration"}:
        return "10-30m"
    if path.suffix == ".sh":
        if "/diag/" in path.as_posix().lower():
            return "unknown"
        content = _read_text(path)
        if any(token in content for token in ("docker compose", "compose_", "compose ", "odoo", "jsonrpc", "/jsonrpc", "base_url", "db_name")):
            return "10-30m"
        return "<5m"
    return "<5m"


def owner_for(layer: str) -> str:
    return {
        "contract": "platform owner",
        "data_migration": "data owner",
        "e2e": "qa owner",
        "frontend_acceptance": "frontend owner",
        "governance": "architecture owner",
        "odoo_integration": "backend owner",
        "security": "security owner",
        "unit": "test owner",
    }.get(layer, "test owner")


def purpose_for(path: Path, layer: str) -> str:
    stem = path.stem.replace("_", " ").replace("-", " ")
    return f"{stem} validation asset classified as {layer}."


def status_for(path: Path) -> str:
    text = path.as_posix().lower()
    if "/demo/" in text or "/diag/" in text or "/test/" in text:
        return "review"
    return "active"


def decision_gate_for(path: Path, layer: str, runtime: str, status: str) -> str:
    if status != "active":
        return "manual_review"
    text = path.as_posix().lower()
    if "/diag/" in text:
        return "manual_review"
    if layer == "e2e" or runtime == "30-60m":
        return "release_candidate"
    if layer in {"odoo_integration", "data_migration"} or runtime == "10-30m":
        return "integration_candidate"
    if layer in {"security", "contract", "governance", "frontend_acceptance", "unit"}:
        return "pr_candidate"
    return "manual_review"


def aggregate_target_for(path: Path, runtime: str) -> str:
    name = path.name.lower()
    if name.startswith("frontend_page_contract_"):
        return "verify.frontend.product.ready"
    if name in {
        "config_workbench_operation_coverage_guard.mjs",
        "config_workbench_operation_summary_guard.mjs",
    }:
        return "verify.business_config.config_workbench_operation_quick"
    if name == "config_workbench_operation_acceptance.mjs":
        return "verify.business_config.config_workbench_operation_acceptance"
    if name in {
        "business_form_user_perspective_acceptance.mjs",
        "business_form_user_perspective_summary_guard.mjs",
        "system_user_experience_shell_acceptance.mjs",
        "system_user_experience_shell_summary_guard.mjs",
        "system_user_experience_coverage_guard.py",
    }:
        return "verify.system_user_experience.full_browser"
    if name in {
        "backend_architecture_full_report_guard.py",
        "backend_architecture_full_report_guard_schema_guard.py",
        "backend_architecture_full_report_schema_guard.py",
    }:
        return "verify.backend.architecture.full.report.guard.schema.guard"
    if name in {
        "backend_evidence_manifest_guard.py",
        "backend_evidence_manifest_schema_guard.py",
    }:
        return "verify.backend.evidence.manifest.guard"
    if name.startswith("boundary_import_guard"):
        return "verify.boundary.import_guard.strict.guard"
    if name.startswith("business_capability_baseline_report_"):
        return "verify.business.capability_baseline.guard"
    if name.startswith("business_form_productization_"):
        return "verify.business_form.productization.audit"
    if name in {
        "contract_assembler_semantic_schema_guard.py",
        "contract_assembler_semantic_smoke.py",
    }:
        return "verify.contract.assembler.semantic.schema.guard"
    if name.startswith("backend_contract_closure_"):
        return "verify.backend.contract.closure.mainline"
    if name in {
        "company_contractor_responsibility_fact_audit.py",
        "company_contractor_responsibility_summary_audit.py",
        "company_contractor_responsibility_http_smoke.py",
    }:
        return "verify.finance_interfund.position.all"
    if name in {
        "lowcode_customer_config_acceptance_decision_template.py",
        "lowcode_customer_config_apply_acceptance_decisions.py",
        "lowcode_customer_config_apply_acceptance_decisions_test.py",
        "lowcode_customer_config_module_asset_replay_guard.py",
    }:
        return "verify.lowcode_config.customer_module_asset.pipeline"
    if name == "lowcode_customer_config_release_hardening_guard.py":
        return "verify.lowcode_config.customer_module_asset.release_hardening.guard"
    if name.startswith("scene_base_contract_"):
        return "verify.scene.runtime_boundary.gate"
    if name.startswith("scene_action_surface_strategy_"):
        return "verify.scene.runtime_boundary.gate"
    if name == "fe_scene_contract_smoke.js":
        return "verify.portal.scene_contract_smoke.container"
    if name == "fe_scene_contract_export_smoke.js":
        return "verify.portal.scene_contract_export_smoke.container"
    if name == "fe_scene_contract_export.js":
        return "scene.contract.export"
    if name == "fe_ar_ap_company_summary_smoke.js":
        return "verify.portal.ar_ap_company_summary_smoke.container"
    if name == "fe_ar_ap_project_summary_smoke.js":
        return "verify.portal.ar_ap_project_summary_smoke.container"
    if name == "fe_list_shell_no_meta_smoke.js":
        return "verify.portal.list_shell_no_meta_smoke.container"
    if name == "fe_list_shell_title_smoke.js":
        return "verify.portal.list_shell_title_smoke.container"
    if name == "fe_menu_scene_key_smoke.js":
        return "verify.portal.menu_scene_key_smoke.container"
    if name == "fe_menu_scene_resolve_smoke.js":
        return "verify.menu.scene_resolve.container"
    if name == "fe_portal_scene_governance_action_smoke.js":
        return "verify.portal.scene_governance_action_strict.container"
    if name == "fe_portal_scene_package_ui_smoke.js":
        return "verify.portal.scene_package_ui_smoke.container"
    if name == "fe_scene_auto_degrade_notify_smoke.js":
        return "verify.portal.scene_auto_degrade_notify_strict.container"
    if name == "fe_scene_auto_degrade_smoke.js":
        return "verify.portal.scene_auto_degrade_strict.container"
    if name == "fe_scene_health_contract_smoke.js":
        return "verify.portal.scene_health_contract_smoke.container"
    if name == "fe_scene_health_pagination_smoke.js":
        return "verify.portal.scene_health_pagination_smoke.container"
    if name == "fe_scene_registry_validate_smoke.js":
        return "verify.portal.scene_registry"
    if name == "fe_view_contract_coverage_smoke.js":
        return "verify.portal.view_contract_coverage_smoke.container"
    if name == "fe_view_contract_shape_smoke.js":
        return "verify.portal.view_contract_shape.container"
    if name in {
        "frontend_scene_contract_auto_render_guard.py",
        "frontend_scene_contract_v1_consumption_guard.py",
    }:
        return "verify.frontend.quick.gate"
    if name == "formal_list_surface_no_test_placeholder_guard.py":
        return "verify.formal_list_surface.no_test_placeholder_guard"
    if name == "smart_core_boundary_guard.py":
        return "verify.smart_core.boundary_guard"
    if name in {
        "form_view_scope_action_projection_audit.py",
        "form_view_scope_boundary_guard.py",
    }:
        return "verify.form_structure.contract"
    if name in {
        "form_structure_contract_runtime_audit.py",
        "form_structure_contract_standardizer_guard.py",
    }:
        return "verify.form_structure.contract"
    if name == "fe_scene_package_dry_run_smoke.js":
        return "verify.portal.scene_package_dry_run_smoke.container"
    if name == "fe_scene_package_import_smoke.js":
        return "verify.portal.scene_observability_strict.container"
    if name == "fe_scene_package_installed_smoke.js":
        return "verify.portal.scene_package_installed_smoke.container"
    if name.startswith("frontend_page_block_"):
        return {
            "frontend_page_block_registry_guard.py": "verify.frontend.page_block_registry_guard",
            "frontend_page_block_renderer_smoke_guard.py": "verify.frontend.page_block_renderer_smoke",
            "frontend_page_block_visual_snapshot_guard.py": "verify.frontend.page_block_visual_snapshot_guard",
        }.get(name, "")
    if name.startswith("grouped_governance_brief_"):
        return "verify.frontend.grouped_governance_brief.baseline.guard"
    if name.startswith("grouped_drift_summary_"):
        return "verify.frontend.grouped_drift_summary.baseline.guard"
    if name.startswith("grouped_governance_trend_consistency_"):
        return "verify.frontend.grouped_governance_trend_consistency.baseline.guard"
    if name.startswith("grouped_pagination_semantic_"):
        return "verify.grouped.governance.bundle"
    if name.startswith("intent_canonical_alias_snapshot_"):
        return "verify.intent.canonical_alias.snapshot.guard"
    if name in {
        "native_view_semantic_page_schema_guard.py",
        "native_view_semantic_page_shape_guard.py",
    }:
        return "verify.native_view.semantic_page"
    if name.startswith("non_demo_data_contamination_guard"):
        return "verify.non_demo_data_contamination"
    if name in {
        "ops_batch_smoke.py",
        "ops_batch_smoke.sh",
    }:
        return "verify.e2e.ops_batch_smoke"
    if name in {
        "portal_entry_registry_guard.py",
        "portal_entry_registry_quality_guard.py",
    }:
        return "verify.portal.entry_registry_quality_guard"
    if name in {
        "product_delivery_governance_truth_guard.py",
        "product_delivery_governance_truth_schema_guard.py",
    }:
        return "verify.product.delivery.governance_truth"
    if name in {
        "project_dashboard_block_payload_guard.py",
        "project_dashboard_block_schema_guard.py",
    }:
        return "verify.project.dashboard.contract"
    if name in {
        "project_dashboard_snapshot_freshness_guard.py",
        "project_dashboard_snapshot_schema_guard.py",
    }:
        return "verify.project.dashboard.snapshot"
    if name in {
        "project_management_productization_acceptance_export.py",
        "project_management_productization_flow_guard.py",
    }:
        return "verify.project.management.acceptance"
    if name == "page_contract_role_orchestration_variance_guard.py":
        return "verify.page_contract.role_orchestration_variance.guard"
    if name == "page_contract_role_strategy_provider_split_guard.py":
        return "verify.page_contract.role_strategy_provider_split.guard"
    if name in {
        "payment_request_approval_field_consumer_audit.py",
        "payment_request_approval_handoff_smoke.py",
        "payment_request_approval_smoke.py",
    }:
        return "verify.portal.payment_request_approval_all_smoke.container"
    if name == "material_settlement_payment_execution_traceability_audit.py":
        return "verify.delivery.material.cross_document_progress"
    if name in {
        "p1_daily_business_form_usability_audit.py",
        "p1_formal_relationship_continuity_audit.py",
        "p1_formal_relationship_scope_block_smoke.py",
    }:
        return "verify.business_capability.productization_p1"
    if name == "p1_daily_business_visible_contract_audit.py":
        return "verify.p1.daily_business_visible_contract.audit"
    if name in {
        "finance_business_fact_projection_audit.py",
        "finance_business_fact_scope_audit.py",
    }:
        return "verify.finance_interfund.position.all"
    if name.startswith("release_v2_0_0_"):
        return "verify.release.v2_0_0.governance.guard"
    if name.startswith("release_capability_audit"):
        return "verify.release.capability.audit.schema.guard"
    if name == "role_capability_floor_guard.py":
        return "verify.role.capability_floor.guard"
    if name == "role_capability_floor_prod_like_schema_guard.py":
        return "verify.role.capability_floor.prod_like.schema.guard"
    if name.startswith("scene_contract_coverage_"):
        return "verify.contract.scene_coverage.guard"
    if name.startswith("scene_governance_history_"):
        return "verify.scene.runtime_boundary.gate"
    if name == "scene_provider_registry_guard.py":
        return "verify.scene.provider.registry.guard"
    if name == "scene_provider_registry_consumer_guard.py":
        return "verify.scene.provider.registry.consumer.guard"
    if name == "scene_ready_strict_contract_guard.py":
        return "verify.scene.runtime_boundary.gate"
    if name == "scene_ready_strict_gap_full_audit.py":
        return "verify.scene.delivery.readiness"
    if name.startswith("scene_sample_registry_diff_"):
        return "verify.scene.runtime_boundary.gate"
    if name.startswith("scene_validation_recovery_strategy_"):
        return "verify.scene.runtime_boundary.gate"
    if name.startswith("smart_core_minimum_"):
        return "verify.smart_core.minimum_surface"
    if name == "scbs55_user_acceptance_asset_manifest_guard.py":
        return "migration.assets.user_acceptance_manifest_guard.evidence"
    if name == "scbs55_user_acceptance_online_probe.py":
        return "migration.assets.user_acceptance_online_probe"
    if name == "scbsly_direct_project_acceptance_menu_probe.py":
        return "migration.assets.scbsly_direct_project_menu_probe"
    if name in {
        "scene_admin_smoke.py",
        "scene_admin_smoke.sh",
    }:
        return "verify.e2e.scene_admin"
    if name in {
        "subscription_smoke.py",
        "subscription_smoke.sh",
    }:
        return "verify.e2e.subscription_smoke"
    if name in {
        "user_confirmed_form_capability_audit.py",
        "user_confirmed_form_data_alignment_audit.py",
    }:
        return "verify.formal_business.release_gate"
    if name == "unified_page_contract_v2_harmony_h5_compile_acceptance_guard.py":
        return "verify.unified_page_contract.v2.harmony_h5_compile_acceptance.host"
    if name == "unified_page_contract_v2_regression_audit.py":
        return "verify.unified_page_contract.v2.regression_audit.host"
    if name == "unified_page_contract_v2_web_visual_acceptance.js":
        return "verify.unified_page_contract.v2.web_visual_acceptance.host"
    if name == "web_unified_page_contract_v2_guard.py":
        return "verify.unified_page_contract.v2"
    if name.startswith("unified_page_contract_v2_"):
        host_only_markers = (
            "harmony_h5_compile_acceptance",
            "regression_audit",
            "web_visual_acceptance",
        )
        if any(marker in name for marker in host_only_markers):
            return ""
        return "verify.unified_page_contract.v2"
    if name.startswith("unified_page_contract_lite_") and runtime != "30-60m":
        return "verify.unified_page_contract.lite"
    return ""


def disposition_for(
    layer: str,
    runtime: str,
    status: str,
    decision_gate: str,
    aggregate_target: str,
) -> str:
    if status != "active":
        return "review_or_archive"
    if runtime == "unknown":
        return "classify_runtime_before_gate"
    if aggregate_target:
        return "covered_by_aggregate"
    if decision_gate == "pr_candidate":
        return "deduplicate_before_required"
    if decision_gate == "integration_candidate":
        return "keep_integration_or_release_only"
    if decision_gate == "release_candidate":
        return "keep_release_only"
    return "needs_owner_decision"


def iter_assets() -> list[Path]:
    assets: list[Path] = []
    for root in SCAN_ROOTS:
        if not root.exists():
            continue
        for path in root.rglob("*"):
            if not path.is_file() or path.suffix not in VALID_EXTENSIONS:
                continue
            if path.relative_to(ROOT).as_posix() in AUTO_SCAN_EXCLUDED:
                continue
            if "__pycache__" in path.parts:
                continue
            lowered = path.name.lower()
            if any(keyword in lowered for keyword in KEYWORDS):
                assets.append(path)
    return sorted(set(assets), key=lambda p: p.relative_to(ROOT).as_posix())


def build_rows() -> list[dict[str, str]]:
    rows: list[dict[str, str]] = list(MANUAL_ENTRIES)
    for index, path in enumerate(iter_assets(), start=1):
        rel = path.relative_to(ROOT).as_posix()
        layer = classify_layer(path)
        runtime = runtime_class(path, layer)
        status = status_for(path)
        decision_gate = decision_gate_for(path, layer, runtime, status)
        aggregate_target = aggregate_target_for(path, runtime)
        rows.append(
            {
                "id": f"T-ASSET-{index:03d}",
                "layer": layer,
                "entrypoint": rel,
                "purpose": purpose_for(path, layer),
                "estimated_runtime": runtime,
                "owner": owner_for(layer),
                "status": status,
                "decision_gate": decision_gate,
                "disposition": disposition_for(layer, runtime, status, decision_gate, aggregate_target),
                "aggregate_target": aggregate_target,
                "notes": "Generated by scripts/ci/generate_test_inventory.py",
            }
        )
    return rows


def write_csv(path: Path) -> None:
    rows = build_rows()
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=[
                "id",
                "layer",
                "entrypoint",
                "purpose",
                "estimated_runtime",
                "owner",
                "status",
                "decision_gate",
                "disposition",
                "aggregate_target",
                "notes",
            ],
            lineterminator="\n",
        )
        writer.writeheader()
        writer.writerows(rows)


def check_csv(path: Path) -> int:
    expected = build_rows()
    if not path.exists():
        print(f"[ERROR] inventory file missing: {path.relative_to(ROOT)}", file=sys.stderr)
        return 1
    with path.open(newline="", encoding="utf-8") as handle:
        actual = list(csv.DictReader(handle))
    if actual != expected:
        print(
            "[ERROR] test inventory is stale. Run: "
            "python3 scripts/ci/generate_test_inventory.py --write",
            file=sys.stderr,
        )
        return 1
    print(f"[OK] test inventory is current ({len(actual)} entries)")
    return 0


def main(argv: list[str]) -> int:
    output = DEFAULT_OUTPUT
    if "--write" in argv:
        write_csv(output)
        print(f"[OK] wrote {output.relative_to(ROOT)}")
        return 0
    return check_csv(output)


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
