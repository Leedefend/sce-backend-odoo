#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path


def load_json(path: Path) -> object:
    return json.loads(path.read_text(encoding="utf-8"))


def load_json_optional(path: Path, default: object) -> object:
    if not path.exists():
        return default
    return load_json(path)


def build_evidence(
    intent_catalog: dict,
    scene_catalog: dict,
    shape_report: dict,
    intent_surface: list[dict],
    scene_alignment_report: dict,
    business_capability_report: dict,
    role_capability_prod_like_report: dict,
    contract_assembler_semantic_report: dict,
    runtime_surface_dashboard_report: dict,
    scene_capability_matrix_report: dict,
    capability_core_health_report: dict,
    boundary_import_report: dict,
    load_view_access_contract_report: dict,
    backend_architecture_full_report: dict,
    backend_evidence_manifest_report: dict,
    scene_contract_coverage_report: dict,
    grouped_signature_report: dict,
    grouped_drift_summary_report: dict,
    grouped_governance_brief_report: dict,
    grouped_governance_policy_matrix_report: dict,
    grouped_governance_trend_consistency_report: dict,
    native_view_semantic_shape_report: dict,
    native_view_semantic_schema_report: dict,
) -> dict:
    intents = intent_catalog.get("intents") or []
    scenes = scene_catalog.get("scenes") or []

    reason_counter: Counter[str] = Counter()
    intents_with_examples = 0
    intents_with_inferred_examples = 0
    intents_with_idempotency_window = 0
    intents_with_aliases = 0
    for item in intents:
        if not isinstance(item, dict):
            continue
        aliases = item.get("aliases")
        if isinstance(aliases, list) and aliases:
            intents_with_aliases += 1
        if item.get("has_idempotency_window") is True:
            intents_with_idempotency_window += 1
        examples = item.get("examples")
        if isinstance(examples, list) and examples:
            intents_with_examples += 1
        inferred_example = item.get("inferred_example")
        if isinstance(inferred_example, dict) and inferred_example:
            intents_with_inferred_examples += 1
        codes = item.get("observed_reason_codes")
        if isinstance(codes, list):
            for code in codes:
                if isinstance(code, str) and code.strip():
                    reason_counter[code.strip()] += 1

    grouped_contract_fields = grouped_signature_report.get("grouped_contract_fields") or {}
    grouped_consistency = ((grouped_signature_report.get("grouped_pagination_semantic_summary") or {}).get("consistency")) or {}
    grouped_signals = [
        bool(grouped_contract_fields.get("group_key")),
        bool(grouped_contract_fields.get("page_has_prev")),
        bool(grouped_contract_fields.get("page_has_next")),
        bool(grouped_contract_fields.get("page_window")),
        bool(grouped_consistency.get("first_group_page_window_matches_range")),
    ]
    grouped_signals_total = len(grouped_signals)
    grouped_signals_passed = sum(1 for item in grouped_signals if item is True)

    evidence = {
        "intent_catalog": {
            "intent_count": len(intents),
            "with_aliases": intents_with_aliases,
            "with_idempotency_window": intents_with_idempotency_window,
            "with_examples": intents_with_examples,
            "with_inferred_examples": intents_with_inferred_examples,
            "top_observed_reason_codes": [{"reason_code": k, "count": v} for k, v in reason_counter.most_common(10)],
        },
        "scene_catalog": {
            "scene_count": len(scenes),
            "catalog_scope": ((scene_catalog.get("source") or {}).get("scene_catalog_scope") or ""),
            "layout_kind_counts": scene_catalog.get("layout_kind_counts") or {},
            "target_type_counts": scene_catalog.get("target_type_counts") or {},
            "renderability": scene_catalog.get("renderability") or {},
            "schema_version": scene_catalog.get("schema_version") or "",
            "scene_version": scene_catalog.get("scene_version") or "",
        },
        "shape_guard": {
            "ok": bool(shape_report.get("ok")),
            "error_count": len(shape_report.get("errors") or []),
            "report": "artifacts/scene_contract_shape_guard.json",
        },
        "intent_surface": {
            "rows": len(intent_surface),
        },
        "scene_runtime_alignment": {
            "ok": bool(scene_alignment_report.get("ok")),
            "catalog_scene_count": int((((scene_alignment_report.get("summary") or {}).get("catalog_scene_count")) or 0)),
            "runtime_scene_count": int((((scene_alignment_report.get("summary") or {}).get("runtime_scene_count")) or 0)),
            "catalog_runtime_ratio": float((((scene_alignment_report.get("summary") or {}).get("catalog_runtime_ratio")) or 0.0)),
            "probe_login": str((((scene_alignment_report.get("summary") or {}).get("probe_login")) or "")).strip(),
            "probe_source": str((((scene_alignment_report.get("summary") or {}).get("probe_source")) or "")).strip(),
            "report": "artifacts/scene_catalog_runtime_alignment_guard.json",
        },
        "business_capability_baseline": {
            "ok": bool(business_capability_report.get("ok")),
            "check_count": int((((business_capability_report.get("summary") or {}).get("check_count")) or 0)),
            "failed_check_count": int((((business_capability_report.get("summary") or {}).get("failed_check_count")) or 0)),
            "required_intent_count": int(
                (((business_capability_report.get("summary") or {}).get("required_intent_count")) or 0)
            ),
            "required_role_count": int(
                (((business_capability_report.get("summary") or {}).get("required_role_count")) or 0)
            ),
            "catalog_runtime_ratio": float(
                (((business_capability_report.get("summary") or {}).get("catalog_runtime_ratio")) or 0.0)
            ),
            "report": "artifacts/business_capability_baseline_report.json",
        },
        "role_capability_prod_like": {
            "ok": bool(role_capability_prod_like_report.get("ok")),
            "fixture_count": int((((role_capability_prod_like_report.get("summary") or {}).get("fixture_count")) or 0)),
            "failed_fixture_count": int(
                (((role_capability_prod_like_report.get("summary") or {}).get("failed_fixture_count")) or 0)
            ),
            "report": "artifacts/backend/role_capability_floor_prod_like.json",
        },
        "contract_assembler_semantic": {
            "ok": bool(contract_assembler_semantic_report.get("ok")),
            "role_count": int((((contract_assembler_semantic_report.get("summary") or {}).get("role_count")) or 0)),
            "error_count": int((((contract_assembler_semantic_report.get("summary") or {}).get("error_count")) or 0)),
            "report": "artifacts/backend/contract_assembler_semantic_smoke.json",
        },
        "runtime_surface_dashboard": {
            "ok": bool(runtime_surface_dashboard_report.get("ok", True)),
            "warning_count": int((((runtime_surface_dashboard_report.get("summary") or {}).get("warning_count")) or 0)),
            "scene_delta": int((((runtime_surface_dashboard_report.get("summary") or {}).get("scene_delta")) or 0)),
            "catalog_runtime_ratio": float(
                (((runtime_surface_dashboard_report.get("summary") or {}).get("catalog_runtime_ratio")) or 0.0)
            ),
            "report": "artifacts/backend/runtime_surface_dashboard_report.json",
        },
        "scene_capability_matrix": {
            "ok": bool(scene_capability_matrix_report.get("ok", False)),
            "scene_count": int((((scene_capability_matrix_report.get("summary") or {}).get("scene_count")) or 0)),
            "capability_count": int((((scene_capability_matrix_report.get("summary") or {}).get("capability_count")) or 0)),
            "scene_without_binding_count": int(
                (((scene_capability_matrix_report.get("summary") or {}).get("scene_without_binding_count")) or 0)
            ),
            "unused_capability_count": int(
                (((scene_capability_matrix_report.get("summary") or {}).get("unused_capability_count")) or 0)
            ),
            "missing_capability_ref_count": int(
                (((scene_capability_matrix_report.get("summary") or {}).get("missing_capability_ref_count")) or 0)
            ),
            "report": "artifacts/backend/scene_capability_matrix_report.json",
        },
        "capability_core_health": {
            "ok": bool(capability_core_health_report.get("ok", False)),
            "role_sample_count": int((((capability_core_health_report.get("summary") or {}).get("role_sample_count")) or 0)),
            "login_failure_count": int(
                (((capability_core_health_report.get("summary") or {}).get("login_failure_count")) or 0)
            ),
            "error_count": int((((capability_core_health_report.get("summary") or {}).get("error_count")) or 0)),
            "warning_count": int((((capability_core_health_report.get("summary") or {}).get("warning_count")) or 0)),
            "report": "artifacts/backend/capability_core_health_report.json",
        },
        "boundary_import_report": {
            "ok": bool(boundary_import_report.get("ok", False)),
            "warning_count": int((((boundary_import_report.get("summary") or {}).get("warning_count")) or 0)),
            "violation_count": int((((boundary_import_report.get("summary") or {}).get("violation_count")) or 0)),
            "tracked_module_count": int((((boundary_import_report.get("summary") or {}).get("tracked_module_count")) or 0)),
            "report": "artifacts/backend/boundary_import_guard_report.json",
        },
        "load_view_access_contract": {
            "ok": bool(load_view_access_contract_report.get("ok", False)),
            "fixture_login": str((((load_view_access_contract_report.get("summary") or {}).get("fixture_login")) or "")).strip(),
            "allowed_model": str((((load_view_access_contract_report.get("summary") or {}).get("allowed_model")) or "")).strip(),
            "forbidden_model": str((((load_view_access_contract_report.get("summary") or {}).get("forbidden_model")) or "")).strip(),
            "forbidden_status": int((((load_view_access_contract_report.get("summary") or {}).get("forbidden_status")) or 0)),
            "forbidden_error_code": str((((load_view_access_contract_report.get("summary") or {}).get("forbidden_error_code")) or "")).strip(),
            "report": "artifacts/backend/load_view_access_contract_guard.json",
        },
        "backend_architecture_full": {
            "ok": bool(backend_architecture_full_report.get("ok", False)),
            "check_count": int((((backend_architecture_full_report.get("summary") or {}).get("check_count")) or 0)),
            "failed_check_count": int(
                (((backend_architecture_full_report.get("summary") or {}).get("failed_check_count")) or 0)
            ),
            "warning_check_count": int(
                (((backend_architecture_full_report.get("summary") or {}).get("warning_check_count")) or 0)
            ),
            "report": "artifacts/backend/backend_architecture_full_report.json",
        },
        "backend_evidence_manifest": {
            "ok": bool(backend_evidence_manifest_report.get("ok", False)),
            "artifact_count": int((((backend_evidence_manifest_report.get("summary") or {}).get("artifact_count")) or 0)),
            "missing_count": int((((backend_evidence_manifest_report.get("summary") or {}).get("missing_count")) or 0)),
            "total_size_bytes": int(
                (((backend_evidence_manifest_report.get("summary") or {}).get("total_size_bytes")) or 0)
            ),
            "report": "artifacts/backend/backend_evidence_manifest.json",
        },
        "scene_contract_coverage": {
            "ok": bool(scene_contract_coverage_report.get("ok", False)),
            "scene_count_actual": int((((scene_contract_coverage_report.get("metrics") or {}).get("scene_count_actual")) or 0)),
            "intent_count_actual": int(
                (((scene_contract_coverage_report.get("metrics") or {}).get("intent_count_actual")) or 0)
            ),
            "renderable_ratio": float(
                (((scene_contract_coverage_report.get("metrics") or {}).get("renderable_ratio")) or 0.0)
            ),
            "interaction_ready_ratio": float(
                (((scene_contract_coverage_report.get("metrics") or {}).get("interaction_ready_ratio")) or 0.0)
            ),
            "report": "artifacts/scene_contract_coverage_brief.json",
        },
        "grouped_pagination_contract": {
            "version": str(grouped_signature_report.get("version") or "").strip(),
            "route_state_key": str(((grouped_signature_report.get("grouped_pagination_route_state") or {}).get("key")) or "").strip(),
            "supports_group_key": bool((grouped_signature_report.get("grouped_contract_fields") or {}).get("group_key")),
            "supports_page_has_prev": bool((grouped_signature_report.get("grouped_contract_fields") or {}).get("page_has_prev")),
            "supports_page_has_next": bool((grouped_signature_report.get("grouped_contract_fields") or {}).get("page_has_next")),
            "supports_page_window": bool((grouped_signature_report.get("grouped_contract_fields") or {}).get("page_window")),
            "window_range_consistency": bool(
                ((grouped_signature_report.get("grouped_pagination_semantic_summary") or {}).get("consistency") or {}).get(
                    "first_group_page_window_matches_range"
                )
            ),
            "consistency_signals_total": grouped_signals_total,
            "consistency_signals_passed": grouped_signals_passed,
            "consistency_score": round((grouped_signals_passed / grouped_signals_total), 4) if grouped_signals_total else 0.0,
            "consistency_ok": grouped_signals_passed == grouped_signals_total and grouped_signals_total > 0,
            "report": "scripts/verify/baselines/fe_tree_grouped_signature.json",
        },
        "grouped_drift_summary": {
            "ok": bool(grouped_drift_summary_report.get("ok", False)),
            "e2e_case_count": int((((grouped_drift_summary_report.get("summary") or {}).get("e2e_case_count")) or 0)),
            "e2e_grouped_rows_case_count": int(
                (((grouped_drift_summary_report.get("summary") or {}).get("e2e_grouped_rows_case_count")) or 0)
            ),
            "e2e_max_consistency_score": int(
                (((grouped_drift_summary_report.get("summary") or {}).get("e2e_max_consistency_score")) or 0)
            ),
            "export_marker_hits": int((((grouped_drift_summary_report.get("summary") or {}).get("export_marker_hits")) or 0)),
            "export_marker_total": int(
                (((grouped_drift_summary_report.get("summary") or {}).get("export_marker_total")) or 0)
            ),
            "report_json": "artifacts/grouped_drift_summary_guard.json",
            "report_md": "artifacts/grouped_drift_summary_guard.md",
        },
        "grouped_governance_brief": {
            "ok": bool(grouped_governance_brief_report.get("ok", False)),
            "governance_coverage_ratio": str(
                (((grouped_governance_brief_report.get("summary") or {}).get("governance_coverage_ratio")) or "")
            ).strip(),
            "governance_covered_file_count": int(
                (((grouped_governance_brief_report.get("summary") or {}).get("governance_covered_file_count")) or 0)
            ),
            "governance_total_file_count": int(
                (((grouped_governance_brief_report.get("summary") or {}).get("governance_total_file_count")) or 0)
            ),
            "governance_failure_count": int(
                (((grouped_governance_brief_report.get("summary") or {}).get("governance_failure_count")) or 0)
            ),
            "grouped_e2e_case_count": int(
                (((grouped_governance_brief_report.get("summary") or {}).get("grouped_e2e_case_count")) or 0)
            ),
            "grouped_e2e_grouped_rows_case_count": int(
                (((grouped_governance_brief_report.get("summary") or {}).get("grouped_e2e_grouped_rows_case_count")) or 0)
            ),
            "grouped_e2e_max_consistency_score": int(
                (((grouped_governance_brief_report.get("summary") or {}).get("grouped_e2e_max_consistency_score")) or 0)
            ),
            "grouped_export_marker_hits": int(
                (((grouped_governance_brief_report.get("summary") or {}).get("grouped_export_marker_hits")) or 0)
            ),
            "grouped_export_marker_total": int(
                (((grouped_governance_brief_report.get("summary") or {}).get("grouped_export_marker_total")) or 0)
            ),
            "has_previous": bool((grouped_governance_brief_report.get("trend") or {}).get("has_previous")),
            "delta_governance_coverage_ratio": (
                ((grouped_governance_brief_report.get("trend") or {}).get("delta") or {}).get(
                    "governance_coverage_ratio_delta"
                )
            ),
            "delta_governance_failure_count": (
                ((grouped_governance_brief_report.get("trend") or {}).get("delta") or {}).get(
                    "governance_failure_count"
                )
            ),
            "delta_grouped_e2e_max_consistency_score": (
                ((grouped_governance_brief_report.get("trend") or {}).get("delta") or {}).get(
                    "grouped_e2e_max_consistency_score"
                )
            ),
            "report_json": "artifacts/grouped_governance_brief_guard.json",
            "report_md": "artifacts/grouped_governance_brief_guard.md",
        },
        "grouped_governance_policy_matrix": {
            "ok": bool(grouped_governance_policy_matrix_report.get("ok", False)),
            "grouped_governance_brief_policy_count": int(
                (((grouped_governance_policy_matrix_report.get("summary") or {}).get("grouped_governance_brief_policy_count")) or 0)
            ),
            "grouped_drift_summary_policy_count": int(
                (((grouped_governance_policy_matrix_report.get("summary") or {}).get("grouped_drift_summary_policy_count")) or 0)
            ),
            "contract_evidence_grouped_governance_policy_count": int(
                (
                    ((grouped_governance_policy_matrix_report.get("summary") or {}).get(
                        "contract_evidence_grouped_governance_policy_count"
                    ))
                    or 0
                )
            ),
            "has_previous": bool((grouped_governance_policy_matrix_report.get("trend") or {}).get("has_previous")),
            "delta_grouped_governance_brief_policy_count": (
                ((grouped_governance_policy_matrix_report.get("trend") or {}).get("delta") or {}).get(
                    "grouped_governance_brief_policy_count"
                )
            ),
            "delta_grouped_drift_summary_policy_count": (
                ((grouped_governance_policy_matrix_report.get("trend") or {}).get("delta") or {}).get(
                    "grouped_drift_summary_policy_count"
                )
            ),
            "delta_contract_evidence_grouped_governance_policy_count": (
                ((grouped_governance_policy_matrix_report.get("trend") or {}).get("delta") or {}).get(
                    "contract_evidence_grouped_governance_policy_count"
                )
            ),
            "report_json": "artifacts/grouped_governance_policy_matrix.json",
            "report_md": "artifacts/grouped_governance_policy_matrix.md",
        },
        "grouped_governance_trend_consistency": {
            "ok": bool(grouped_governance_trend_consistency_report.get("ok", False)),
            "has_previous_aligned": bool(
                ((grouped_governance_trend_consistency_report.get("summary") or {}).get("has_previous_aligned"))
            ),
            "brief_delta_types_ok": bool(
                ((grouped_governance_trend_consistency_report.get("summary") or {}).get("brief_delta_types_ok"))
            ),
            "matrix_delta_types_ok": bool(
                ((grouped_governance_trend_consistency_report.get("summary") or {}).get("matrix_delta_types_ok"))
            ),
            "report_json": "artifacts/grouped_governance_trend_consistency_guard.json",
            "report_md": "artifacts/grouped_governance_trend_consistency_guard.md",
        },
        "native_view_semantic_guard": {
            "ok": bool(native_view_semantic_shape_report.get("ok", False)) and bool(native_view_semantic_schema_report.get("ok", False)),
            "shape_ok": bool(native_view_semantic_shape_report.get("ok", False)),
            "schema_ok": bool(native_view_semantic_schema_report.get("ok", False)),
            "snapshot_count": int(native_view_semantic_shape_report.get("snapshot_count") or 0),
            "shape_error_count": int(native_view_semantic_shape_report.get("error_count") or 0),
            "schema_error_count": int(native_view_semantic_schema_report.get("error_count") or 0),
            "shape_report": "artifacts/backend/native_view_semantic_page_shape_guard.json",
            "schema_report": "artifacts/backend/native_view_semantic_page_schema_guard.json",
        },
    }
    return evidence


def to_markdown(evidence: dict) -> str:
    i = evidence["intent_catalog"]
    s = evidence["scene_catalog"]
    g = evidence["shape_guard"]
    t = evidence["intent_surface"]
    a = evidence["scene_runtime_alignment"]
    b = evidence["business_capability_baseline"]
    p = evidence["role_capability_prod_like"]
    c = evidence["contract_assembler_semantic"]
    r = evidence["runtime_surface_dashboard"]
    scm = evidence["scene_capability_matrix"]
    cch = evidence["capability_core_health"]
    bi = evidence["boundary_import_report"]
    lv = evidence["load_view_access_contract"]
    a2 = evidence["backend_architecture_full"]
    m2 = evidence["backend_evidence_manifest"]
    scb = evidence["scene_contract_coverage"]
    gpc = evidence["grouped_pagination_contract"]
    gds = evidence["grouped_drift_summary"]
    ggb = evidence["grouped_governance_brief"]
    ggpm = evidence["grouped_governance_policy_matrix"]
    ggtc = evidence["grouped_governance_trend_consistency"]
    nv = evidence["native_view_semantic_guard"]
    lines = [
        "# Phase 11.1 Contract Evidence",
        "",
        "## Contract Surface",
        f"- intents: {i['intent_count']}",
        f"- intents with aliases: {i['with_aliases']}",
        f"- intents with idempotency window: {i['with_idempotency_window']}",
        f"- intents with snapshot examples: {i['with_examples']}",
        f"- intents with inferred examples: {i['with_inferred_examples']}",
        f"- intent surface rows: {t['rows']}",
        "",
        "## Scene Orchestration",
        f"- scenes: {s['scene_count']}",
        f"- catalog_scope: {s['catalog_scope']}",
        f"- schema_version: {s['schema_version']}",
        f"- scene_version: {s['scene_version']}",
        f"- layout kinds: {json.dumps(s['layout_kind_counts'], ensure_ascii=False)}",
        f"- target types: {json.dumps(s['target_type_counts'], ensure_ascii=False)}",
        f"- renderability: {json.dumps(s.get('renderability') or {}, ensure_ascii=False)}",
        "",
        "## Runtime Alignment",
        f"- ok: {a['ok']}",
        f"- catalog_scene_count: {a['catalog_scene_count']}",
        f"- runtime_scene_count: {a['runtime_scene_count']}",
        f"- catalog_runtime_ratio: {a['catalog_runtime_ratio']}",
        f"- probe_login: {a['probe_login'] or '-'}",
        f"- probe_source: {a['probe_source'] or '-'}",
        f"- report: `{a['report']}`",
        "",
        "## Business Capability Baseline",
        f"- ok: {b['ok']}",
        f"- check_count: {b['check_count']}",
        f"- failed_check_count: {b['failed_check_count']}",
        f"- required_intent_count: {b['required_intent_count']}",
        f"- required_role_count: {b['required_role_count']}",
        f"- catalog_runtime_ratio: {b['catalog_runtime_ratio']}",
        f"- report: `{b['report']}`",
        "",
        "## Shape Guard",
        f"- ok: {g['ok']}",
        f"- error_count: {g['error_count']}",
        f"- report: `{g['report']}`",
        "",
        "## Prod-like Role Fixtures",
        f"- ok: {p['ok']}",
        f"- fixture_count: {p['fixture_count']}",
        f"- failed_fixture_count: {p['failed_fixture_count']}",
        f"- report: `{p['report']}`",
        "",
        "## Contract Assembler Semantic",
        f"- ok: {c['ok']}",
        f"- role_count: {c['role_count']}",
        f"- error_count: {c['error_count']}",
        f"- report: `{c['report']}`",
        "",
        "## Runtime Surface Dashboard",
        f"- ok: {r['ok']}",
        f"- warning_count: {r['warning_count']}",
        f"- scene_delta: {r['scene_delta']}",
        f"- catalog_runtime_ratio: {r['catalog_runtime_ratio']}",
        f"- report: `{r['report']}`",
        "",
        "## Scene Capability Matrix",
        f"- ok: {scm['ok']}",
        f"- scene_count: {scm['scene_count']}",
        f"- capability_count: {scm['capability_count']}",
        f"- scene_without_binding_count: {scm['scene_without_binding_count']}",
        f"- unused_capability_count: {scm['unused_capability_count']}",
        f"- missing_capability_ref_count: {scm['missing_capability_ref_count']}",
        f"- report: `{scm['report']}`",
        "",
        "## Capability Core Health",
        f"- ok: {cch['ok']}",
        f"- role_sample_count: {cch['role_sample_count']}",
        f"- login_failure_count: {cch['login_failure_count']}",
        f"- error_count: {cch['error_count']}",
        f"- warning_count: {cch['warning_count']}",
        f"- report: `{cch['report']}`",
        "",
        "## Boundary Import Report",
        f"- ok: {bi['ok']}",
        f"- warning_count: {bi['warning_count']}",
        f"- violation_count: {bi['violation_count']}",
        f"- tracked_module_count: {bi['tracked_module_count']}",
        f"- report: `{bi['report']}`",
        "",
        "## Load View Access Contract",
        f"- ok: {lv['ok']}",
        f"- fixture_login: {lv['fixture_login'] or '-'}",
        f"- allowed_model: {lv['allowed_model'] or '-'}",
        f"- forbidden_model: {lv['forbidden_model'] or '-'}",
        f"- forbidden_status: {lv['forbidden_status']}",
        f"- forbidden_error_code: {lv['forbidden_error_code'] or '-'}",
        f"- report: `{lv['report']}`",
        "",
        "## Backend Architecture Full",
        f"- ok: {a2['ok']}",
        f"- check_count: {a2['check_count']}",
        f"- failed_check_count: {a2['failed_check_count']}",
        f"- warning_check_count: {a2['warning_check_count']}",
        f"- report: `{a2['report']}`",
        "",
        "## Backend Evidence Manifest",
        f"- ok: {m2['ok']}",
        f"- artifact_count: {m2['artifact_count']}",
        f"- missing_count: {m2['missing_count']}",
        f"- total_size_bytes: {m2['total_size_bytes']}",
        f"- report: `{m2['report']}`",
        "",
        "## Scene Contract Coverage Brief",
        f"- ok: {scb['ok']}",
        f"- scene_count_actual: {scb['scene_count_actual']}",
        f"- intent_count_actual: {scb['intent_count_actual']}",
        f"- renderable_ratio: {scb['renderable_ratio']}",
        f"- interaction_ready_ratio: {scb['interaction_ready_ratio']}",
        f"- report: `{scb['report']}`",
        "",
        "## Grouped Pagination Contract",
        f"- version: {gpc['version'] or '-'}",
        f"- route_state_key: {gpc['route_state_key'] or '-'}",
        f"- supports_group_key: {gpc['supports_group_key']}",
        f"- supports_page_has_prev: {gpc['supports_page_has_prev']}",
        f"- supports_page_has_next: {gpc['supports_page_has_next']}",
        f"- supports_page_window: {gpc['supports_page_window']}",
        f"- window_range_consistency: {gpc['window_range_consistency']}",
        f"- consistency_signals_passed: {gpc['consistency_signals_passed']} / {gpc['consistency_signals_total']}",
        f"- consistency_score: {gpc['consistency_score']}",
        f"- consistency_ok: {gpc['consistency_ok']}",
        f"- report: `{gpc['report']}`",
        "",
        "## Grouped Drift Summary",
        f"- ok: {gds['ok']}",
        f"- e2e_case_count: {gds['e2e_case_count']}",
        f"- e2e_grouped_rows_case_count: {gds['e2e_grouped_rows_case_count']}",
        f"- e2e_max_consistency_score: {gds['e2e_max_consistency_score']}",
        f"- export_marker_hits: {gds['export_marker_hits']} / {gds['export_marker_total']}",
        f"- report_json: `{gds['report_json']}`",
        f"- report_md: `{gds['report_md']}`",
        "",
        "## Grouped Governance Brief",
        f"- ok: {ggb['ok']}",
        f"- governance_coverage_ratio: {ggb['governance_coverage_ratio'] or '-'}",
        f"- governance_covered_file_count: {ggb['governance_covered_file_count']}",
        f"- governance_total_file_count: {ggb['governance_total_file_count']}",
        f"- governance_failure_count: {ggb['governance_failure_count']}",
        f"- grouped_e2e_case_count: {ggb['grouped_e2e_case_count']}",
        f"- grouped_e2e_grouped_rows_case_count: {ggb['grouped_e2e_grouped_rows_case_count']}",
        f"- grouped_e2e_max_consistency_score: {ggb['grouped_e2e_max_consistency_score']}",
        f"- grouped_export_marker_hits: {ggb['grouped_export_marker_hits']} / {ggb['grouped_export_marker_total']}",
        f"- has_previous: {ggb['has_previous']}",
        f"- delta_governance_coverage_ratio: {ggb['delta_governance_coverage_ratio']}",
        f"- delta_governance_failure_count: {ggb['delta_governance_failure_count']}",
        f"- delta_grouped_e2e_max_consistency_score: {ggb['delta_grouped_e2e_max_consistency_score']}",
        f"- report_json: `{ggb['report_json']}`",
        f"- report_md: `{ggb['report_md']}`",
        "",
        "## Grouped Governance Policy Matrix",
        f"- ok: {ggpm['ok']}",
        f"- grouped_governance_brief_policy_count: {ggpm['grouped_governance_brief_policy_count']}",
        f"- grouped_drift_summary_policy_count: {ggpm['grouped_drift_summary_policy_count']}",
        (
            "- contract_evidence_grouped_governance_policy_count: "
            f"{ggpm['contract_evidence_grouped_governance_policy_count']}"
        ),
        f"- has_previous: {ggpm['has_previous']}",
        (
            "- delta_grouped_governance_brief_policy_count: "
            f"{ggpm['delta_grouped_governance_brief_policy_count']}"
        ),
        (
            "- delta_grouped_drift_summary_policy_count: "
            f"{ggpm['delta_grouped_drift_summary_policy_count']}"
        ),
        (
            "- delta_contract_evidence_grouped_governance_policy_count: "
            f"{ggpm['delta_contract_evidence_grouped_governance_policy_count']}"
        ),
        f"- report_json: `{ggpm['report_json']}`",
        f"- report_md: `{ggpm['report_md']}`",
        "",
        "## Grouped Governance Trend Consistency",
        f"- ok: {ggtc['ok']}",
        f"- has_previous_aligned: {ggtc['has_previous_aligned']}",
        f"- brief_delta_types_ok: {ggtc['brief_delta_types_ok']}",
        f"- matrix_delta_types_ok: {ggtc['matrix_delta_types_ok']}",
        f"- report_json: `{ggtc['report_json']}`",
        f"- report_md: `{ggtc['report_md']}`",
        "",
        "## Native View Semantic Guard",
        f"- ok: {nv['ok']}",
        f"- shape_ok: {nv['shape_ok']}",
        f"- schema_ok: {nv['schema_ok']}",
        f"- snapshot_count: {nv['snapshot_count']}",
        f"- shape_error_count: {nv['shape_error_count']}",
        f"- schema_error_count: {nv['schema_error_count']}",
        f"- shape_report: `{nv['shape_report']}`",
        f"- schema_report: `{nv['schema_report']}`",
        "",
        "## Top Observed reason_code",
    ]
    top_codes = i.get("top_observed_reason_codes") or []
    if not top_codes:
        lines.append("- (none)")
    else:
        for row in top_codes:
            lines.append(f"- `{row['reason_code']}`: {row['count']}")
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description="Export phase 11.1 contract evidence summary.")
    parser.add_argument("--intent-catalog", default="docs/contract/exports/intent_catalog.json")
    parser.add_argument("--scene-catalog", default="docs/contract/exports/scene_catalog.json")
    parser.add_argument("--shape-report", default="artifacts/scene_contract_shape_guard.json")
    parser.add_argument("--intent-surface", default="artifacts/intent_surface_report.json")
    parser.add_argument("--scene-alignment-report", default="artifacts/scene_catalog_runtime_alignment_guard.json")
    parser.add_argument("--business-capability-report", default="artifacts/business_capability_baseline_report.json")
    parser.add_argument("--role-capability-prod-like-report", default="artifacts/backend/role_capability_floor_prod_like.json")
    parser.add_argument("--contract-assembler-semantic-report", default="artifacts/backend/contract_assembler_semantic_smoke.json")
    parser.add_argument("--runtime-surface-dashboard-report", default="artifacts/backend/runtime_surface_dashboard_report.json")
    parser.add_argument("--scene-capability-matrix-report", default="artifacts/backend/scene_capability_matrix_report.json")
    parser.add_argument("--capability-core-health-report", default="artifacts/backend/capability_core_health_report.json")
    parser.add_argument("--boundary-import-report", default="artifacts/backend/boundary_import_guard_report.json")
    parser.add_argument("--load-view-access-contract-report", default="artifacts/backend/load_view_access_contract_guard.json")
    parser.add_argument("--backend-architecture-full-report", default="artifacts/backend/backend_architecture_full_report.json")
    parser.add_argument("--backend-evidence-manifest-report", default="artifacts/backend/backend_evidence_manifest.json")
    parser.add_argument("--scene-contract-coverage-report", default="artifacts/scene_contract_coverage_brief.json")
    parser.add_argument("--grouped-signature-report", default="scripts/verify/baselines/fe_tree_grouped_signature.json")
    parser.add_argument("--grouped-drift-summary-report", default="artifacts/grouped_drift_summary_guard.json")
    parser.add_argument("--grouped-governance-brief-report", default="artifacts/grouped_governance_brief_guard.json")
    parser.add_argument("--grouped-governance-policy-matrix-report", default="artifacts/grouped_governance_policy_matrix.json")
    parser.add_argument(
        "--grouped-governance-trend-consistency-report",
        default="artifacts/grouped_governance_trend_consistency_guard.json",
    )
    parser.add_argument("--native-view-semantic-shape-report", default="artifacts/backend/native_view_semantic_page_shape_guard.json")
    parser.add_argument("--native-view-semantic-schema-report", default="artifacts/backend/native_view_semantic_page_schema_guard.json")
    parser.add_argument("--output-json", default="artifacts/contract/phase11_1_contract_evidence.json")
    parser.add_argument("--output-md", default="artifacts/contract/phase11_1_contract_evidence.md")
    args = parser.parse_args()

    intent_catalog = load_json(Path(args.intent_catalog))
    scene_catalog = load_json(Path(args.scene_catalog))
    shape_report = load_json(Path(args.shape_report))
    intent_surface = load_json(Path(args.intent_surface))
    scene_alignment_report = load_json_optional(Path(args.scene_alignment_report), {})
    business_capability_report = load_json_optional(Path(args.business_capability_report), {})
    role_capability_prod_like_report = load_json_optional(Path(args.role_capability_prod_like_report), {})
    contract_assembler_semantic_report = load_json_optional(Path(args.contract_assembler_semantic_report), {})
    runtime_surface_dashboard_report = load_json_optional(Path(args.runtime_surface_dashboard_report), {})
    scene_capability_matrix_report = load_json_optional(Path(args.scene_capability_matrix_report), {})
    capability_core_health_report = load_json_optional(Path(args.capability_core_health_report), {})
    boundary_import_report = load_json_optional(Path(args.boundary_import_report), {})
    load_view_access_contract_report = load_json_optional(Path(args.load_view_access_contract_report), {})
    backend_architecture_full_report = load_json_optional(Path(args.backend_architecture_full_report), {})
    backend_evidence_manifest_report = load_json_optional(Path(args.backend_evidence_manifest_report), {})
    scene_contract_coverage_report = load_json_optional(Path(args.scene_contract_coverage_report), {})
    grouped_signature_report = load_json_optional(Path(args.grouped_signature_report), {})
    grouped_drift_summary_report = load_json_optional(Path(args.grouped_drift_summary_report), {})
    grouped_governance_brief_report = load_json_optional(Path(args.grouped_governance_brief_report), {})
    grouped_governance_policy_matrix_report = load_json_optional(Path(args.grouped_governance_policy_matrix_report), {})
    grouped_governance_trend_consistency_report = load_json_optional(
        Path(args.grouped_governance_trend_consistency_report), {}
    )
    native_view_semantic_shape_report = load_json_optional(Path(args.native_view_semantic_shape_report), {})
    native_view_semantic_schema_report = load_json_optional(Path(args.native_view_semantic_schema_report), {})

    if not isinstance(intent_catalog, dict):
        raise SystemExit("intent catalog must be object")
    if not isinstance(scene_catalog, dict):
        raise SystemExit("scene catalog must be object")
    if not isinstance(shape_report, dict):
        raise SystemExit("shape report must be object")
    if not isinstance(intent_surface, list):
        raise SystemExit("intent surface report must be list")
    if not isinstance(scene_alignment_report, dict):
        raise SystemExit("scene alignment report must be object")
    if not isinstance(business_capability_report, dict):
        raise SystemExit("business capability report must be object")
    if not isinstance(role_capability_prod_like_report, dict):
        raise SystemExit("role capability prod-like report must be object")
    if not isinstance(contract_assembler_semantic_report, dict):
        raise SystemExit("contract assembler semantic report must be object")
    if not isinstance(runtime_surface_dashboard_report, dict):
        raise SystemExit("runtime surface dashboard report must be object")
    if not isinstance(scene_capability_matrix_report, dict):
        raise SystemExit("scene capability matrix report must be object")
    if not isinstance(capability_core_health_report, dict):
        raise SystemExit("capability core health report must be object")
    if not isinstance(load_view_access_contract_report, dict):
        raise SystemExit("load view access contract report must be object")
    if not isinstance(backend_architecture_full_report, dict):
        raise SystemExit("backend architecture full report must be object")
    if not isinstance(backend_evidence_manifest_report, dict):
        raise SystemExit("backend evidence manifest report must be object")
    if not isinstance(scene_contract_coverage_report, dict):
        raise SystemExit("scene contract coverage report must be object")
    if not isinstance(grouped_signature_report, dict):
        raise SystemExit("grouped signature report must be object")
    if not isinstance(grouped_drift_summary_report, dict):
        raise SystemExit("grouped drift summary report must be object")
    if not isinstance(grouped_governance_brief_report, dict):
        raise SystemExit("grouped governance brief report must be object")
    if not isinstance(grouped_governance_policy_matrix_report, dict):
        raise SystemExit("grouped governance policy matrix report must be object")
    if not isinstance(grouped_governance_trend_consistency_report, dict):
        raise SystemExit("grouped governance trend consistency report must be object")
    if not isinstance(native_view_semantic_shape_report, dict):
        raise SystemExit("native view semantic shape report must be object")
    if not isinstance(native_view_semantic_schema_report, dict):
        raise SystemExit("native view semantic schema report must be object")

    evidence = build_evidence(
        intent_catalog,
        scene_catalog,
        shape_report,
        intent_surface,
        scene_alignment_report,
        business_capability_report,
        role_capability_prod_like_report,
        contract_assembler_semantic_report,
        runtime_surface_dashboard_report,
        scene_capability_matrix_report,
        capability_core_health_report,
        boundary_import_report,
        load_view_access_contract_report,
        backend_architecture_full_report,
        backend_evidence_manifest_report,
        scene_contract_coverage_report,
        grouped_signature_report,
        grouped_drift_summary_report,
        grouped_governance_brief_report,
        grouped_governance_policy_matrix_report,
        grouped_governance_trend_consistency_report,
        native_view_semantic_shape_report,
        native_view_semantic_schema_report,
    )
    out_json = Path(args.output_json)
    out_md = Path(args.output_md)
    out_json.parent.mkdir(parents=True, exist_ok=True)
    out_md.parent.mkdir(parents=True, exist_ok=True)
    out_json.write_text(json.dumps(evidence, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    out_md.write_text(to_markdown(evidence), encoding="utf-8")
    print(str(out_json))
    print(str(out_md))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
