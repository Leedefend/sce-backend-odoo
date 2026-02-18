#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

import json
import os
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_ARTIFACT = ROOT / "artifacts" / "backend" / "boundary_import_guard_report.json"
BASELINE_JSON = ROOT / "scripts" / "verify" / "baselines" / "boundary_import_guard_schema_guard.json"


def _resolve_artifact_path() -> Path:
    candidates = []
    raw_dir = str(os.getenv("ARTIFACTS_DIR") or "").strip()
    if raw_dir:
        candidates.append(Path(raw_dir) / "backend" / "boundary_import_guard_report.json")
    candidates.append(Path("/mnt/artifacts/backend/boundary_import_guard_report.json"))
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
    baseline = _load_json(BASELINE_JSON)
    required_summary_keys = {
        str(item).strip()
        for item in (baseline.get("required_summary_keys") if isinstance(baseline.get("required_summary_keys"), list) else [])
        if str(item).strip()
    }
    required_top_keys = {
        str(item).strip()
        for item in (baseline.get("required_top_keys") if isinstance(baseline.get("required_top_keys"), list) else [])
        if str(item).strip()
    }
    min_tracked_module_count = int(baseline.get("min_tracked_module_count") or 1)
    if not required_summary_keys or not required_top_keys:
        print("[boundary_import_guard_schema_guard] FAIL")
        print(f"invalid baseline: {BASELINE_JSON.relative_to(ROOT).as_posix()}")
        return 1

    path = _resolve_artifact_path()
    payload = _load_json(path)
    if not payload:
        print("[boundary_import_guard_schema_guard] FAIL")
        print(f"missing or invalid artifact: {path}")
        return 1

    errors: list[str] = []
    for key in sorted(required_top_keys):
        if key not in payload:
            errors.append(f"missing top-level key: {key}")

    summary = payload.get("summary") if isinstance(payload.get("summary"), dict) else {}
    if not summary:
        errors.append("summary must be object")
    else:
        for key in sorted(required_summary_keys):
            if key not in summary:
                errors.append(f"summary missing key: {key}")
        tracked_module_count = int(summary.get("tracked_module_count") or 0)
        if tracked_module_count < min_tracked_module_count:
            errors.append(
                f"summary.tracked_module_count too small: {tracked_module_count} < {min_tracked_module_count}"
            )

    warnings = payload.get("warnings")
    if not isinstance(warnings, list):
        errors.append("warnings must be list")
    violations = payload.get("violations")
    if not isinstance(violations, list):
        errors.append("violations must be list")
    manifest_depends = payload.get("manifest_depends")
    if not isinstance(manifest_depends, dict):
        errors.append("manifest_depends must be object")

    if errors:
        print("[boundary_import_guard_schema_guard] FAIL")
        for item in errors:
            print(item)
        return 1

    print("[boundary_import_guard_schema_guard] PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())

