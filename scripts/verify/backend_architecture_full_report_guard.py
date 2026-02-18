#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

import json
import os
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[2]
BASELINE_JSON = ROOT / "scripts" / "verify" / "baselines" / "backend_architecture_full_report_guard.json"
DEFAULT_ARTIFACT = ROOT / "artifacts" / "backend" / "backend_architecture_full_report.json"


def _resolve_artifact_path() -> Path:
    candidates = []
    raw_dir = str(os.getenv("ARTIFACTS_DIR") or "").strip()
    if raw_dir:
        candidates.append(Path(raw_dir) / "backend" / "backend_architecture_full_report.json")
    candidates.append(Path("/mnt/artifacts/backend/backend_architecture_full_report.json"))
    candidates.append(DEFAULT_ARTIFACT)
    for path in candidates:
        if path.is_file():
            return path
    return DEFAULT_ARTIFACT


def _resolve_artifacts_dir() -> Path:
    candidates = [
        str(os.getenv("ARTIFACTS_DIR") or "").strip(),
        "/mnt/artifacts",
        str(ROOT / "artifacts"),
    ]
    for raw in candidates:
        if not raw:
            continue
        path = Path(raw)
        try:
            path.mkdir(parents=True, exist_ok=True)
            probe = path / ".probe_write"
            probe.write_text("ok", encoding="utf-8")
            probe.unlink(missing_ok=True)
            return path
        except Exception:
            continue
    raise RuntimeError("no writable artifacts dir available")


def _load_json(path: Path) -> dict:
    if not path.is_file():
        return {}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}
    return payload if isinstance(payload, dict) else {}


def _safe_int(value, default: int = 0) -> int:
    try:
        return int(value)
    except Exception:
        return default


def _safe_float(value, default: float = 0.0) -> float:
    try:
        return float(value)
    except Exception:
        return default


def main() -> int:
    baseline = _load_json(BASELINE_JSON)
    if not baseline:
        print("[backend_architecture_full_report_guard] FAIL")
        print(f"missing or invalid baseline: {BASELINE_JSON.relative_to(ROOT).as_posix()}")
        return 1

    report_path = _resolve_artifact_path()
    report = _load_json(report_path)
    if not report:
        print("[backend_architecture_full_report_guard] FAIL")
        print(f"missing or invalid report: {report_path}")
        return 1

    artifacts_dir = _resolve_artifacts_dir() / "backend"
    artifacts_dir.mkdir(parents=True, exist_ok=True)
    artifact_json = artifacts_dir / "backend_architecture_full_report_guard.json"
    artifact_md = artifacts_dir / "backend_architecture_full_report_guard.md"

    summary = report.get("summary") if isinstance(report.get("summary"), dict) else {}
    checks = report.get("checks") if isinstance(report.get("checks"), list) else []
    checks_by_name = {str(row.get("name") or "").strip(): row for row in checks if isinstance(row, dict)}

    required_checks = [str(item).strip() for item in (baseline.get("required_checks") or []) if str(item).strip()]
    errors: list[str] = []
    if not required_checks:
        errors.append("baseline.required_checks is empty")

    min_check_count = _safe_int(baseline.get("min_check_count"), len(required_checks))
    max_failed_check_count = _safe_int(baseline.get("max_failed_check_count"), 0)
    max_warning_check_count = _safe_int(baseline.get("max_warning_check_count"), 0)
    min_coverage_ratio = _safe_float(baseline.get("min_contract_governance_coverage_ratio"), 0.0)
    min_alignment_ratio = _safe_float(baseline.get("min_scene_catalog_runtime_alignment_ratio"), 0.0)
    min_business_required_intent_count = _safe_int(baseline.get("min_business_required_intent_count"), 0)
    min_business_required_role_count = _safe_int(baseline.get("min_business_required_role_count"), 0)
    min_business_catalog_runtime_ratio = _safe_float(baseline.get("min_business_catalog_runtime_ratio"), 0.0)
    required_load_view_forbidden_status = _safe_int(baseline.get("required_load_view_forbidden_status"), 0)
    required_load_view_forbidden_error_code = str(baseline.get("required_load_view_forbidden_error_code") or "").strip()
    require_alignment_probe_login = bool(baseline.get("require_alignment_probe_login", False))
    require_alignment_probe_source = bool(baseline.get("require_alignment_probe_source", False))

    check_count = _safe_int(summary.get("check_count"), 0)
    failed_check_count = _safe_int(summary.get("failed_check_count"), 0)
    warning_check_count = _safe_int(summary.get("warning_check_count"), 0)

    if check_count < min_check_count:
        errors.append(f"check_count too small: {check_count} < {min_check_count}")
    if failed_check_count > max_failed_check_count:
        errors.append(f"failed_check_count exceeded: {failed_check_count} > {max_failed_check_count}")
    if warning_check_count > max_warning_check_count:
        errors.append(f"warning_check_count exceeded: {warning_check_count} > {max_warning_check_count}")

    missing_checks = [name for name in required_checks if name not in checks_by_name]
    if missing_checks:
        errors.append(f"required checks missing: {', '.join(sorted(missing_checks))}")

    coverage_row = checks_by_name.get("contract_governance_coverage") or {}
    coverage_ratio = _safe_float(coverage_row.get("coverage_ratio"), 0.0)
    if coverage_ratio < min_coverage_ratio:
        errors.append(
            f"contract_governance_coverage_ratio too small: {coverage_ratio} < {min_coverage_ratio}"
        )

    alignment_row = checks_by_name.get("scene_catalog_runtime_alignment") or {}
    alignment_ratio = _safe_float(alignment_row.get("catalog_runtime_ratio"), 0.0)
    alignment_probe_login = str(alignment_row.get("probe_login") or "").strip()
    alignment_probe_source = str(alignment_row.get("probe_source") or "").strip()
    if alignment_ratio < min_alignment_ratio:
        errors.append(
            f"scene_catalog_runtime_alignment_ratio too small: {alignment_ratio} < {min_alignment_ratio}"
        )
    if require_alignment_probe_login and not alignment_probe_login:
        errors.append("scene_catalog_runtime_alignment.probe_login must be non-empty")
    if require_alignment_probe_source and not alignment_probe_source:
        errors.append("scene_catalog_runtime_alignment.probe_source must be non-empty")

    business_row = checks_by_name.get("business_capability_baseline") or {}
    business_required_intent_count = _safe_int(business_row.get("required_intent_count"), 0)
    business_required_role_count = _safe_int(business_row.get("required_role_count"), 0)
    business_catalog_runtime_ratio = _safe_float(business_row.get("catalog_runtime_ratio"), 0.0)
    if business_required_intent_count < min_business_required_intent_count:
        errors.append(
            "business_required_intent_count too small: "
            f"{business_required_intent_count} < {min_business_required_intent_count}"
        )
    if business_required_role_count < min_business_required_role_count:
        errors.append(
            "business_required_role_count too small: "
            f"{business_required_role_count} < {min_business_required_role_count}"
        )
    if business_catalog_runtime_ratio < min_business_catalog_runtime_ratio:
        errors.append(
            "business_catalog_runtime_ratio too small: "
            f"{business_catalog_runtime_ratio} < {min_business_catalog_runtime_ratio}"
        )

    load_view_row = checks_by_name.get("load_view_access_contract") or {}
    load_view_forbidden_status = _safe_int(load_view_row.get("forbidden_status"), 0)
    load_view_forbidden_error_code = str(load_view_row.get("forbidden_error_code") or "").strip()
    if required_load_view_forbidden_status > 0 and load_view_forbidden_status != required_load_view_forbidden_status:
        errors.append(
            "load_view_access_contract.forbidden_status mismatch: "
            f"{load_view_forbidden_status} != {required_load_view_forbidden_status}"
        )
    if required_load_view_forbidden_error_code and (
        load_view_forbidden_error_code != required_load_view_forbidden_error_code
    ):
        errors.append(
            "load_view_access_contract.forbidden_error_code mismatch: "
            f"{load_view_forbidden_error_code or '-'} != {required_load_view_forbidden_error_code}"
        )

    payload = {
        "ok": len(errors) == 0,
        "summary": {
            "check_count": check_count,
            "failed_check_count": failed_check_count,
            "warning_check_count": warning_check_count,
            "required_check_count": len(required_checks),
            "missing_check_count": len(missing_checks),
            "error_count": len(errors),
            "artifacts_dir": str(artifacts_dir),
        },
        "baseline": baseline,
        "observed": {
            "contract_governance_coverage_ratio": coverage_ratio,
            "scene_catalog_runtime_alignment_ratio": alignment_ratio,
            "scene_catalog_runtime_alignment_probe_login": alignment_probe_login,
            "scene_catalog_runtime_alignment_probe_source": alignment_probe_source,
            "business_required_intent_count": business_required_intent_count,
            "business_required_role_count": business_required_role_count,
            "business_catalog_runtime_ratio": business_catalog_runtime_ratio,
            "load_view_forbidden_status": load_view_forbidden_status,
            "load_view_forbidden_error_code": load_view_forbidden_error_code,
        },
        "errors": errors,
    }
    artifact_json.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    lines = [
        "# Backend Architecture Full Report Guard",
        "",
        f"- status: {'PASS' if payload['ok'] else 'FAIL'}",
        f"- check_count: {check_count}",
        f"- failed_check_count: {failed_check_count}",
        f"- warning_check_count: {warning_check_count}",
        f"- required_check_count: {len(required_checks)}",
        f"- missing_check_count: {len(missing_checks)}",
        f"- contract_governance_coverage_ratio: {coverage_ratio}",
        f"- scene_catalog_runtime_alignment_ratio: {alignment_ratio}",
        f"- scene_catalog_runtime_alignment_probe_login: {alignment_probe_login or '-'}",
        f"- scene_catalog_runtime_alignment_probe_source: {alignment_probe_source or '-'}",
        f"- business_required_intent_count: {business_required_intent_count}",
        f"- business_required_role_count: {business_required_role_count}",
        f"- business_catalog_runtime_ratio: {business_catalog_runtime_ratio}",
        f"- load_view_forbidden_status: {load_view_forbidden_status}",
        f"- load_view_forbidden_error_code: {load_view_forbidden_error_code or '-'}",
        f"- error_count: {len(errors)}",
    ]
    if errors:
        lines.extend(["", "## Errors", ""])
        for item in errors[:200]:
            lines.append(f"- {item}")
    artifact_md.write_text("\n".join(lines) + "\n", encoding="utf-8")

    print(str(artifact_json))
    print(str(artifact_md))
    if errors:
        print("[backend_architecture_full_report_guard] FAIL")
        return 1
    print("[backend_architecture_full_report_guard] PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
