#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

import json
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[2]
EVIDENCE_JSON = ROOT / "artifacts" / "contract" / "phase11_1_contract_evidence.json"
BASELINE_JSON = ROOT / "scripts" / "verify" / "baselines" / "contract_evidence_guard_baseline.json"


def _load_json(path: Path) -> dict:
    if not path.is_file():
        return {}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}
    return payload if isinstance(payload, dict) else {}


def _ratio_to_float(raw: object) -> float:
    if isinstance(raw, (int, float)):
        return float(raw)
    if not isinstance(raw, str) or "/" not in raw:
        return 0.0
    left, right = raw.split("/", 1)
    try:
        left_f = float(left.strip())
        right_f = float(right.strip())
    except Exception:
        return 0.0
    if right_f <= 0:
        return 0.0
    return left_f / right_f


def _to_abs_report_path(raw: object) -> Path | None:
    text = str(raw or "").strip()
    if not text:
        return None
    path = Path(text)
    if path.is_absolute():
        return path
    return (ROOT / path).resolve()


def _load_text(path: Path | None) -> str:
    if not isinstance(path, Path) or not path.is_file():
        return ""
    try:
        return path.read_text(encoding="utf-8")
    except Exception:
        return ""


def main() -> int:
    policy = {
        "max_errors": 0,
        "min_business_capability_check_count": 1,
        "min_business_required_intent_count": 0,
        "min_business_required_role_count": 0,
        "min_business_catalog_runtime_ratio": 0.0,
        "min_scene_catalog_runtime_ratio": 0.0,
        "min_prod_like_fixture_count": 0,
        "max_contract_assembler_semantic_error_count": 0,
        "require_alignment_ok": True,
        "require_business_capability_ok": True,
        "require_prod_like_ok": True,
        "require_contract_assembler_semantic_ok": True,
        "require_scene_capability_matrix_ok": True,
        "max_scene_capability_matrix_error_count": 0,
        "require_capability_core_health_ok": True,
        "max_capability_core_health_error_count": 0,
        "require_backend_architecture_full_ok": True,
        "max_backend_architecture_failed_check_count": 0,
        "require_backend_evidence_manifest_ok": True,
        "max_backend_evidence_manifest_missing_count": 0,
        "require_boundary_import_report_ok": True,
        "max_boundary_import_warning_count": 0,
        "max_boundary_import_violation_count": 0,
        "require_load_view_access_ok": True,
        "require_load_view_forbidden_status_403": True,
        "require_load_view_forbidden_error_code": "PERMISSION_DENIED",
        "require_scene_contract_coverage_ok": True,
        "min_scene_contract_coverage_scene_count_actual": 1,
        "min_scene_contract_coverage_intent_count_actual": 1,
        "min_scene_contract_coverage_renderable_ratio": 0.0,
        "min_scene_contract_coverage_interaction_ready_ratio": 0.0,
        "require_grouped_pagination_contract_section": True,
        "require_grouped_pagination_route_state_key": "group_page",
        "require_grouped_supports_group_key": True,
        "require_grouped_supports_page_has_prev": True,
        "require_grouped_supports_page_has_next": True,
        "require_grouped_supports_page_window": True,
        "require_grouped_window_range_consistency": True,
        "require_grouped_consistency_ok": True,
        "min_grouped_consistency_score": 1.0,
        "require_grouped_drift_summary_ok": True,
        "min_grouped_drift_e2e_case_count": 1,
        "require_grouped_drift_export_marker_full_hit": True,
        "require_grouped_governance_brief_ok": True,
        "min_grouped_governance_coverage_ratio": 1.0,
        "min_grouped_governance_total_file_count": 1,
        "min_grouped_governance_covered_file_count": 1,
        "max_grouped_governance_failure_count": 0,
        "min_grouped_governance_e2e_case_count": 1,
        "require_grouped_governance_coverage_count_consistent": True,
        "max_grouped_governance_coverage_ratio_delta_abs": 0.000001,
        "require_grouped_governance_export_marker_full_hit": True,
        "require_grouped_governance_export_marker_bounds": True,
        "require_grouped_governance_report_alignment": True,
        "max_grouped_governance_alignment_ratio_delta_abs": 0.000001,
        "require_grouped_governance_report_json_prefix": "artifacts/",
        "require_grouped_governance_report_json_suffix": "grouped_governance_brief_guard.json",
        "require_grouped_governance_report_md_alignment": True,
        "require_grouped_governance_report_md_prefix": "artifacts/",
        "require_grouped_governance_report_md_suffix": "grouped_governance_brief_guard.md",
        "require_grouped_governance_report_md_title": "# Grouped Governance Brief Guard",
    }
    policy_payload = _load_json(BASELINE_JSON)
    if policy_payload:
        policy.update(policy_payload)
    payload = _load_json(EVIDENCE_JSON)
    if not payload:
        print("[contract_evidence_guard] FAIL")
        print(f"missing or invalid evidence: {EVIDENCE_JSON.relative_to(ROOT).as_posix()}")
        return 1

    errors: list[str] = []
    for key in (
        "intent_catalog",
        "scene_catalog",
        "shape_guard",
        "intent_surface",
        "scene_runtime_alignment",
        "business_capability_baseline",
        "role_capability_prod_like",
        "contract_assembler_semantic",
        "runtime_surface_dashboard",
        "scene_capability_matrix",
        "capability_core_health",
        "boundary_import_report",
        "load_view_access_contract",
        "backend_architecture_full",
        "backend_evidence_manifest",
        "scene_contract_coverage",
        "grouped_pagination_contract",
        "grouped_drift_summary",
        "grouped_governance_brief",
    ):
        if not isinstance(payload.get(key), dict):
            errors.append(f"missing section: {key}")

    scene_catalog = payload.get("scene_catalog") if isinstance(payload.get("scene_catalog"), dict) else {}
    if not str(scene_catalog.get("catalog_scope") or "").strip():
        errors.append("scene_catalog.catalog_scope is required")

    align = payload.get("scene_runtime_alignment") if isinstance(payload.get("scene_runtime_alignment"), dict) else {}
    if not isinstance(align.get("ok"), bool):
        errors.append("scene_runtime_alignment.ok must be bool")
    if bool(policy.get("require_alignment_ok", True)) and not bool(align.get("ok")):
        errors.append("scene_runtime_alignment.ok must be true under baseline policy")
    min_ratio = float(policy.get("min_scene_catalog_runtime_ratio", 0.0) or 0.0)
    if float(align.get("catalog_runtime_ratio") or 0.0) < min_ratio:
        errors.append(f"scene_runtime_alignment.catalog_runtime_ratio must be >= {min_ratio}")

    capability_baseline = payload.get("business_capability_baseline") if isinstance(payload.get("business_capability_baseline"), dict) else {}
    if not isinstance(capability_baseline.get("ok"), bool):
        errors.append("business_capability_baseline.ok must be bool")
    if bool(policy.get("require_business_capability_ok", True)) and not bool(capability_baseline.get("ok")):
        errors.append("business_capability_baseline.ok must be true under baseline policy")
    min_checks = int(policy.get("min_business_capability_check_count", 1) or 1)
    if int(capability_baseline.get("check_count") or 0) < min_checks:
        errors.append(f"business_capability_baseline.check_count must be >= {min_checks}")
    min_required_intent_count = int(policy.get("min_business_required_intent_count", 0) or 0)
    if int(capability_baseline.get("required_intent_count") or 0) < min_required_intent_count:
        errors.append(f"business_capability_baseline.required_intent_count must be >= {min_required_intent_count}")
    min_required_role_count = int(policy.get("min_business_required_role_count", 0) or 0)
    if int(capability_baseline.get("required_role_count") or 0) < min_required_role_count:
        errors.append(f"business_capability_baseline.required_role_count must be >= {min_required_role_count}")
    min_business_ratio = float(policy.get("min_business_catalog_runtime_ratio", 0.0) or 0.0)
    if float(capability_baseline.get("catalog_runtime_ratio") or 0.0) < min_business_ratio:
        errors.append(f"business_capability_baseline.catalog_runtime_ratio must be >= {min_business_ratio}")

    prod_like = payload.get("role_capability_prod_like") if isinstance(payload.get("role_capability_prod_like"), dict) else {}
    if not isinstance(prod_like.get("ok"), bool):
        errors.append("role_capability_prod_like.ok must be bool")
    if bool(policy.get("require_prod_like_ok", True)) and not bool(prod_like.get("ok")):
        errors.append("role_capability_prod_like.ok must be true under baseline policy")
    min_prod_fixtures = int(policy.get("min_prod_like_fixture_count", 0) or 0)
    if int(prod_like.get("fixture_count") or 0) < min_prod_fixtures:
        errors.append(f"role_capability_prod_like.fixture_count must be >= {min_prod_fixtures}")

    semantic = payload.get("contract_assembler_semantic") if isinstance(payload.get("contract_assembler_semantic"), dict) else {}
    if not isinstance(semantic.get("ok"), bool):
        errors.append("contract_assembler_semantic.ok must be bool")
    if bool(policy.get("require_contract_assembler_semantic_ok", True)) and not bool(semantic.get("ok")):
        errors.append("contract_assembler_semantic.ok must be true under baseline policy")
    max_semantic_errors = int(policy.get("max_contract_assembler_semantic_error_count", 0) or 0)
    if int(semantic.get("error_count") or 0) > max_semantic_errors:
        errors.append(
            "contract_assembler_semantic.error_count must be <= "
            f"{max_semantic_errors}"
        )
    scene_capability_matrix = payload.get("scene_capability_matrix") if isinstance(payload.get("scene_capability_matrix"), dict) else {}
    if not isinstance(scene_capability_matrix.get("ok"), bool):
        errors.append("scene_capability_matrix.ok must be bool")
    if bool(policy.get("require_scene_capability_matrix_ok", True)) and not bool(scene_capability_matrix.get("ok")):
        errors.append("scene_capability_matrix.ok must be true under baseline policy")
    max_scene_matrix_errors = int(policy.get("max_scene_capability_matrix_error_count", 0) or 0)
    if int(scene_capability_matrix.get("missing_capability_ref_count") or 0) > max_scene_matrix_errors:
        errors.append(
            "scene_capability_matrix.missing_capability_ref_count must be <= "
            f"{max_scene_matrix_errors}"
        )
    capability_core_health = payload.get("capability_core_health") if isinstance(payload.get("capability_core_health"), dict) else {}
    if not isinstance(capability_core_health.get("ok"), bool):
        errors.append("capability_core_health.ok must be bool")
    if bool(policy.get("require_capability_core_health_ok", True)) and not bool(capability_core_health.get("ok")):
        errors.append("capability_core_health.ok must be true under baseline policy")
    max_capability_core_health_errors = int(policy.get("max_capability_core_health_error_count", 0) or 0)
    if int(capability_core_health.get("error_count") or 0) > max_capability_core_health_errors:
        errors.append(
            "capability_core_health.error_count must be <= "
            f"{max_capability_core_health_errors}"
        )

    backend_full = payload.get("backend_architecture_full") if isinstance(payload.get("backend_architecture_full"), dict) else {}
    if not isinstance(backend_full.get("ok"), bool):
        errors.append("backend_architecture_full.ok must be bool")
    if bool(policy.get("require_backend_architecture_full_ok", True)) and not bool(backend_full.get("ok")):
        errors.append("backend_architecture_full.ok must be true under baseline policy")
    max_failed_checks = int(policy.get("max_backend_architecture_failed_check_count", 0) or 0)
    if int(backend_full.get("failed_check_count") or 0) > max_failed_checks:
        errors.append(
            "backend_architecture_full.failed_check_count must be <= "
            f"{max_failed_checks}"
        )

    backend_manifest = payload.get("backend_evidence_manifest") if isinstance(payload.get("backend_evidence_manifest"), dict) else {}
    if not isinstance(backend_manifest.get("ok"), bool):
        errors.append("backend_evidence_manifest.ok must be bool")
    if bool(policy.get("require_backend_evidence_manifest_ok", True)) and not bool(backend_manifest.get("ok")):
        errors.append("backend_evidence_manifest.ok must be true under baseline policy")
    max_manifest_missing = int(policy.get("max_backend_evidence_manifest_missing_count", 0) or 0)
    if int(backend_manifest.get("missing_count") or 0) > max_manifest_missing:
        errors.append(
            "backend_evidence_manifest.missing_count must be <= "
            f"{max_manifest_missing}"
        )
    boundary_import_report = payload.get("boundary_import_report") if isinstance(payload.get("boundary_import_report"), dict) else {}
    if not isinstance(boundary_import_report.get("ok"), bool):
        errors.append("boundary_import_report.ok must be bool")
    if bool(policy.get("require_boundary_import_report_ok", True)) and not bool(boundary_import_report.get("ok")):
        errors.append("boundary_import_report.ok must be true under baseline policy")
    max_boundary_import_warning_count = int(policy.get("max_boundary_import_warning_count", 0) or 0)
    max_boundary_import_violation_count = int(policy.get("max_boundary_import_violation_count", 0) or 0)
    if int(boundary_import_report.get("warning_count") or 0) > max_boundary_import_warning_count:
        errors.append(
            "boundary_import_report.warning_count must be <= "
            f"{max_boundary_import_warning_count}"
        )
    if int(boundary_import_report.get("violation_count") or 0) > max_boundary_import_violation_count:
        errors.append(
            "boundary_import_report.violation_count must be <= "
            f"{max_boundary_import_violation_count}"
        )

    load_view_access = payload.get("load_view_access_contract") if isinstance(payload.get("load_view_access_contract"), dict) else {}
    if not isinstance(load_view_access.get("ok"), bool):
        errors.append("load_view_access_contract.ok must be bool")
    if bool(policy.get("require_load_view_access_ok", True)) and not bool(load_view_access.get("ok")):
        errors.append("load_view_access_contract.ok must be true under baseline policy")
    if bool(policy.get("require_load_view_forbidden_status_403", True)):
        if int(load_view_access.get("forbidden_status") or 0) != 403:
            errors.append("load_view_access_contract.forbidden_status must be 403")
    required_forbidden_code = str(policy.get("require_load_view_forbidden_error_code") or "").strip()
    if required_forbidden_code:
        actual_forbidden_code = str(load_view_access.get("forbidden_error_code") or "").strip()
        if actual_forbidden_code != required_forbidden_code:
            errors.append(
                "load_view_access_contract.forbidden_error_code must be "
                f"{required_forbidden_code}, got {actual_forbidden_code or '-'}"
            )

    scene_contract_coverage = payload.get("scene_contract_coverage") if isinstance(payload.get("scene_contract_coverage"), dict) else {}
    if not isinstance(scene_contract_coverage.get("ok"), bool):
        errors.append("scene_contract_coverage.ok must be bool")
    if bool(policy.get("require_scene_contract_coverage_ok", True)) and not bool(scene_contract_coverage.get("ok")):
        errors.append("scene_contract_coverage.ok must be true under baseline policy")

    min_scene_cov_scene_count = int(policy.get("min_scene_contract_coverage_scene_count_actual", 1) or 1)
    if int(scene_contract_coverage.get("scene_count_actual") or 0) < min_scene_cov_scene_count:
        errors.append(
            "scene_contract_coverage.scene_count_actual must be >= "
            f"{min_scene_cov_scene_count}"
        )

    min_scene_cov_intent_count = int(policy.get("min_scene_contract_coverage_intent_count_actual", 1) or 1)
    if int(scene_contract_coverage.get("intent_count_actual") or 0) < min_scene_cov_intent_count:
        errors.append(
            "scene_contract_coverage.intent_count_actual must be >= "
            f"{min_scene_cov_intent_count}"
        )

    min_scene_cov_renderable_ratio = float(policy.get("min_scene_contract_coverage_renderable_ratio", 0.0) or 0.0)
    if float(scene_contract_coverage.get("renderable_ratio") or 0.0) < min_scene_cov_renderable_ratio:
        errors.append(
            "scene_contract_coverage.renderable_ratio must be >= "
            f"{min_scene_cov_renderable_ratio}"
        )

    min_scene_cov_interaction_ready_ratio = float(
        policy.get("min_scene_contract_coverage_interaction_ready_ratio", 0.0) or 0.0
    )
    if float(scene_contract_coverage.get("interaction_ready_ratio") or 0.0) < min_scene_cov_interaction_ready_ratio:
        errors.append(
            "scene_contract_coverage.interaction_ready_ratio must be >= "
            f"{min_scene_cov_interaction_ready_ratio}"
        )

    grouped = payload.get("grouped_pagination_contract") if isinstance(payload.get("grouped_pagination_contract"), dict) else {}
    if bool(policy.get("require_grouped_pagination_contract_section", True)) and not grouped:
        errors.append("grouped_pagination_contract section is required under baseline policy")
    if grouped:
        for key in (
            "supports_group_key",
            "supports_page_has_prev",
            "supports_page_has_next",
            "supports_page_window",
            "window_range_consistency",
        ):
            if key in grouped and not isinstance(grouped.get(key), bool):
                errors.append(f"grouped_pagination_contract.{key} must be bool")
        route_state_key = str(grouped.get("route_state_key") or "").strip()
        expected_route_state_key = str(policy.get("require_grouped_pagination_route_state_key") or "").strip()
        if expected_route_state_key and route_state_key != expected_route_state_key:
            errors.append(
                "grouped_pagination_contract.route_state_key must be "
                f"{expected_route_state_key}, got {route_state_key or '-'}"
            )
        if bool(policy.get("require_grouped_supports_group_key", True)) and not bool(grouped.get("supports_group_key")):
            errors.append("grouped_pagination_contract.supports_group_key must be true under baseline policy")
        if bool(policy.get("require_grouped_supports_page_has_prev", True)) and not bool(
            grouped.get("supports_page_has_prev")
        ):
            errors.append("grouped_pagination_contract.supports_page_has_prev must be true under baseline policy")
        if bool(policy.get("require_grouped_supports_page_has_next", True)) and not bool(
            grouped.get("supports_page_has_next")
        ):
            errors.append("grouped_pagination_contract.supports_page_has_next must be true under baseline policy")
        if bool(policy.get("require_grouped_supports_page_window", True)) and not bool(
            grouped.get("supports_page_window")
        ):
            errors.append("grouped_pagination_contract.supports_page_window must be true under baseline policy")
        if bool(policy.get("require_grouped_window_range_consistency", True)) and not bool(
            grouped.get("window_range_consistency")
        ):
            errors.append("grouped_pagination_contract.window_range_consistency must be true under baseline policy")
        if int(grouped.get("consistency_signals_total") or 0) < 1:
            errors.append("grouped_pagination_contract.consistency_signals_total must be >= 1")
        if int(grouped.get("consistency_signals_passed") or 0) > int(grouped.get("consistency_signals_total") or 0):
            errors.append("grouped_pagination_contract.consistency_signals_passed must be <= consistency_signals_total")
        min_grouped_consistency_score = float(policy.get("min_grouped_consistency_score", 1.0) or 1.0)
        if float(grouped.get("consistency_score") or 0.0) < min_grouped_consistency_score:
            errors.append(
                "grouped_pagination_contract.consistency_score must be >= "
                f"{min_grouped_consistency_score}"
            )
        if bool(policy.get("require_grouped_consistency_ok", True)) and not bool(grouped.get("consistency_ok")):
            errors.append("grouped_pagination_contract.consistency_ok must be true under baseline policy")

    grouped_drift = payload.get("grouped_drift_summary") if isinstance(payload.get("grouped_drift_summary"), dict) else {}
    if bool(policy.get("require_grouped_drift_summary_ok", True)) and not bool(grouped_drift.get("ok")):
        errors.append("grouped_drift_summary.ok must be true under baseline policy")
    min_grouped_drift_e2e_case_count = int(policy.get("min_grouped_drift_e2e_case_count", 1) or 1)
    if int(grouped_drift.get("e2e_case_count") or 0) < min_grouped_drift_e2e_case_count:
        errors.append(
            "grouped_drift_summary.e2e_case_count must be >= "
            f"{min_grouped_drift_e2e_case_count}"
        )
    if bool(policy.get("require_grouped_drift_export_marker_full_hit", True)):
        if int(grouped_drift.get("export_marker_hits") or 0) != int(grouped_drift.get("export_marker_total") or 0):
            errors.append("grouped_drift_summary export markers must be fully hit under baseline policy")

    grouped_governance = (
        payload.get("grouped_governance_brief")
        if isinstance(payload.get("grouped_governance_brief"), dict)
        else {}
    )
    if bool(policy.get("require_grouped_governance_brief_ok", True)) and not bool(grouped_governance.get("ok")):
        errors.append("grouped_governance_brief.ok must be true under baseline policy")
    min_grouped_governance_coverage_ratio = float(policy.get("min_grouped_governance_coverage_ratio", 1.0) or 1.0)
    if _ratio_to_float(grouped_governance.get("governance_coverage_ratio")) < min_grouped_governance_coverage_ratio:
        errors.append(
            "grouped_governance_brief.governance_coverage_ratio must be >= "
            f"{min_grouped_governance_coverage_ratio}"
        )
    min_grouped_governance_total_file_count = int(policy.get("min_grouped_governance_total_file_count", 1) or 1)
    if int(grouped_governance.get("governance_total_file_count") or 0) < min_grouped_governance_total_file_count:
        errors.append(
            "grouped_governance_brief.governance_total_file_count must be >= "
            f"{min_grouped_governance_total_file_count}"
        )
    min_grouped_governance_covered_file_count = int(policy.get("min_grouped_governance_covered_file_count", 1) or 1)
    if int(grouped_governance.get("governance_covered_file_count") or 0) < min_grouped_governance_covered_file_count:
        errors.append(
            "grouped_governance_brief.governance_covered_file_count must be >= "
            f"{min_grouped_governance_covered_file_count}"
        )
    max_grouped_governance_failure_count = int(policy.get("max_grouped_governance_failure_count", 0) or 0)
    if int(grouped_governance.get("governance_failure_count") or 0) > max_grouped_governance_failure_count:
        errors.append(
            "grouped_governance_brief.governance_failure_count must be <= "
            f"{max_grouped_governance_failure_count}"
        )
    min_grouped_governance_e2e_case_count = int(policy.get("min_grouped_governance_e2e_case_count", 1) or 1)
    if int(grouped_governance.get("grouped_e2e_case_count") or 0) < min_grouped_governance_e2e_case_count:
        errors.append(
            "grouped_governance_brief.grouped_e2e_case_count must be >= "
            f"{min_grouped_governance_e2e_case_count}"
        )
    if bool(policy.get("require_grouped_governance_export_marker_full_hit", True)):
        if int(grouped_governance.get("grouped_export_marker_hits") or 0) != int(
            grouped_governance.get("grouped_export_marker_total") or 0
        ):
            errors.append("grouped_governance_brief export markers must be fully hit under baseline policy")
    if bool(policy.get("require_grouped_governance_coverage_count_consistent", True)):
        covered_count = int(grouped_governance.get("governance_covered_file_count") or 0)
        total_count = int(grouped_governance.get("governance_total_file_count") or 0)
        if covered_count > total_count:
            errors.append("grouped_governance_brief.governance_covered_file_count must be <= governance_total_file_count")
        expected_ratio = (float(covered_count) / float(total_count)) if total_count > 0 else 0.0
        actual_ratio = _ratio_to_float(grouped_governance.get("governance_coverage_ratio"))
        max_ratio_delta_abs = float(policy.get("max_grouped_governance_coverage_ratio_delta_abs", 0.000001) or 0.000001)
        if abs(actual_ratio - expected_ratio) > max_ratio_delta_abs:
            errors.append(
                "grouped_governance_brief.governance_coverage_ratio must match "
                "governance_covered_file_count/governance_total_file_count"
            )
    if bool(policy.get("require_grouped_governance_export_marker_bounds", True)):
        marker_hits = int(grouped_governance.get("grouped_export_marker_hits") or 0)
        marker_total = int(grouped_governance.get("grouped_export_marker_total") or 0)
        if marker_total < 1:
            errors.append("grouped_governance_brief.grouped_export_marker_total must be >= 1")
        if marker_hits > marker_total:
            errors.append("grouped_governance_brief.grouped_export_marker_hits must be <= grouped_export_marker_total")
    if bool(policy.get("require_grouped_governance_report_alignment", True)):
        report_json_raw = str(grouped_governance.get("report_json") or "").strip()
        require_report_json_prefix = str(policy.get("require_grouped_governance_report_json_prefix") or "").strip()
        require_report_json_suffix = str(policy.get("require_grouped_governance_report_json_suffix") or "").strip()
        if require_report_json_prefix and not report_json_raw.startswith(require_report_json_prefix):
            errors.append(
                "grouped_governance_brief.report_json must start with "
                f"{require_report_json_prefix}"
            )
        if require_report_json_suffix and not report_json_raw.endswith(require_report_json_suffix):
            errors.append(
                "grouped_governance_brief.report_json must end with "
                f"{require_report_json_suffix}"
            )
        report_path = _to_abs_report_path(grouped_governance.get("report_json"))
        source_report = _load_json(report_path) if isinstance(report_path, Path) else {}
        if not source_report:
            errors.append("grouped_governance_brief.report_json must point to a readable report")
        else:
            source_summary = source_report.get("summary") if isinstance(source_report.get("summary"), dict) else {}
            if bool(grouped_governance.get("ok")) != bool(source_report.get("ok")):
                errors.append("grouped_governance_brief.ok must align with source report ok")
            for key in (
                "governance_covered_file_count",
                "governance_total_file_count",
                "governance_failure_count",
                "grouped_e2e_case_count",
                "grouped_e2e_grouped_rows_case_count",
                "grouped_e2e_max_consistency_score",
                "grouped_export_marker_hits",
                "grouped_export_marker_total",
            ):
                source_v = int(source_summary.get(key) or 0)
                evidence_v = int(grouped_governance.get(key) or 0)
                if evidence_v != source_v:
                    errors.append(f"grouped_governance_brief.{key} must align with source report")
            source_ratio = _ratio_to_float(source_summary.get("governance_coverage_ratio"))
            evidence_ratio = _ratio_to_float(grouped_governance.get("governance_coverage_ratio"))
            max_align_ratio_delta_abs = float(
                policy.get("max_grouped_governance_alignment_ratio_delta_abs", 0.000001) or 0.000001
            )
            if abs(evidence_ratio - source_ratio) > max_align_ratio_delta_abs:
                errors.append("grouped_governance_brief.governance_coverage_ratio must align with source report")
    if bool(policy.get("require_grouped_governance_report_md_alignment", True)):
        report_md_raw = str(grouped_governance.get("report_md") or "").strip()
        require_report_md_prefix = str(policy.get("require_grouped_governance_report_md_prefix") or "").strip()
        require_report_md_suffix = str(policy.get("require_grouped_governance_report_md_suffix") or "").strip()
        if require_report_md_prefix and not report_md_raw.startswith(require_report_md_prefix):
            errors.append(
                "grouped_governance_brief.report_md must start with "
                f"{require_report_md_prefix}"
            )
        if require_report_md_suffix and not report_md_raw.endswith(require_report_md_suffix):
            errors.append(
                "grouped_governance_brief.report_md must end with "
                f"{require_report_md_suffix}"
            )
        report_md_path = _to_abs_report_path(grouped_governance.get("report_md"))
        report_md_text = _load_text(report_md_path)
        if not report_md_text:
            errors.append("grouped_governance_brief.report_md must point to a readable markdown report")
        else:
            expected_title = str(policy.get("require_grouped_governance_report_md_title") or "").strip()
            if expected_title and expected_title not in report_md_text:
                errors.append("grouped_governance_brief.report_md missing required governance title")

    if len(errors) > int(policy.get("max_errors", 0)):
        print("[contract_evidence_guard] FAIL")
        for item in errors:
            print(item)
        return 1

    print("[contract_evidence_guard] PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
