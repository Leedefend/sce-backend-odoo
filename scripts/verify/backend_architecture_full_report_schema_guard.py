#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

import json
import os
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_ARTIFACT = ROOT / "artifacts" / "backend" / "backend_architecture_full_report.json"
REQUIRED_CHECKS = {
    "role_capability_prod_like",
    "contract_assembler_semantic_smoke",
    "runtime_surface_dashboard",
    "contract_governance_coverage",
    "controller_boundary_report",
    "scene_catalog_runtime_alignment",
}


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


def _load_json(path: Path) -> dict:
    if not path.is_file():
        return {}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}
    return payload if isinstance(payload, dict) else {}


def main() -> int:
    path = _resolve_artifact_path()
    payload = _load_json(path)
    if not payload:
        print("[backend_architecture_full_report_schema_guard] FAIL")
        print(f"missing or invalid artifact: {path}")
        return 1

    errors: list[str] = []
    if not isinstance(payload.get("ok"), bool):
        errors.append("ok must be bool")
    summary = payload.get("summary") if isinstance(payload.get("summary"), dict) else {}
    if not summary:
        errors.append("summary must be object")
    checks = payload.get("checks") if isinstance(payload.get("checks"), list) else None
    if checks is None:
        errors.append("checks must be list")
        checks = []

    for key in ("check_count", "failed_check_count", "warning_check_count", "failed_checks", "warning_checks", "artifacts_dir"):
        if key not in summary:
            errors.append(f"summary missing key: {key}")

    names: set[str] = set()
    for idx, row in enumerate(checks):
        if not isinstance(row, dict):
            errors.append(f"checks[{idx}] must be object")
            continue
        name = str(row.get("name") or "").strip()
        if not name:
            errors.append(f"checks[{idx}].name is required")
            continue
        names.add(name)
        if not isinstance(row.get("ok"), bool):
            errors.append(f"checks[{idx}].ok must be bool")
        if not str(row.get("source") or "").strip():
            errors.append(f"checks[{idx}].source is required")

    missing_checks = sorted(REQUIRED_CHECKS - names)
    if missing_checks:
        errors.append(f"required checks missing: {', '.join(missing_checks)}")

    if isinstance(summary.get("check_count"), int) and int(summary.get("check_count")) != len(checks):
        errors.append(f"summary.check_count mismatch: {summary.get('check_count')} != {len(checks)}")
    if isinstance(summary.get("failed_checks"), list):
        failed_actual = sorted([str(row.get("name") or "") for row in checks if isinstance(row, dict) and row.get("ok") is False])
        failed_summary = sorted([str(v) for v in summary.get("failed_checks") if isinstance(v, str)])
        if failed_actual != failed_summary:
            errors.append(f"summary.failed_checks mismatch: {failed_summary} != {failed_actual}")
    if isinstance(summary.get("warning_checks"), list):
        warning_actual = sorted(
            [
                str(row.get("name") or "")
                for row in checks
                if isinstance(row, dict) and int(row.get("warning_count") or 0) > 0
            ]
        )
        warning_summary = sorted([str(v) for v in summary.get("warning_checks") if isinstance(v, str)])
        if warning_actual != warning_summary:
            errors.append(f"summary.warning_checks mismatch: {warning_summary} != {warning_actual}")

    if errors:
        print("[backend_architecture_full_report_schema_guard] FAIL")
        for item in errors:
            print(item)
        return 1
    print("[backend_architecture_full_report_schema_guard] PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
