#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

import json
import os
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_ARTIFACT = ROOT / "artifacts" / "backend" / "runtime_surface_dashboard_report.json"


def _resolve_artifact_path() -> Path:
    candidates = []
    raw_dir = str(os.getenv("ARTIFACTS_DIR") or "").strip()
    if raw_dir:
        candidates.append(Path(raw_dir) / "backend" / "runtime_surface_dashboard_report.json")
    candidates.append(Path("/mnt/artifacts/backend/runtime_surface_dashboard_report.json"))
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
    report = _load_json(path)
    if not report:
        print("[runtime_surface_dashboard_schema_guard] FAIL")
        print(f"missing or invalid artifact: {path}")
        return 1
    errors: list[str] = []
    summary = report.get("summary") if isinstance(report.get("summary"), dict) else {}
    warnings = report.get("warnings") if isinstance(report.get("warnings"), list) else None
    baseline = report.get("baseline") if isinstance(report.get("baseline"), dict) else {}
    baseline_snapshot = report.get("baseline_snapshot") if isinstance(report.get("baseline_snapshot"), dict) else {}
    delta_vs_baseline = report.get("delta_vs_baseline") if isinstance(report.get("delta_vs_baseline"), dict) else {}
    if not isinstance(report.get("ok"), bool):
        errors.append("ok must be bool")
    if not summary:
        errors.append("summary must be object")
    if warnings is None:
        errors.append("warnings must be list")
        warnings = []
    if not baseline:
        errors.append("baseline must be object")
    if not baseline_snapshot:
        errors.append("baseline_snapshot must be object")
    if not delta_vs_baseline:
        errors.append("delta_vs_baseline must be object")

    for key in (
        "catalog_scene_count",
        "runtime_scene_count",
        "scene_delta",
        "catalog_runtime_ratio",
        "runtime_capability_min",
        "runtime_capability_avg",
        "runtime_capability_max",
        "alignment_probe_login",
        "alignment_probe_source",
        "baseline_catalog_scene_count",
        "baseline_runtime_scene_count",
        "baseline_catalog_runtime_ratio",
        "baseline_runtime_capability_min",
        "baseline_runtime_capability_avg",
        "baseline_runtime_capability_max",
        "warning_count",
    ):
        if key not in summary:
            errors.append(f"summary missing key: {key}")

    for key in (
        "catalog_scene_count",
        "runtime_scene_count",
        "catalog_runtime_ratio",
        "runtime_capability_min",
        "runtime_capability_avg",
        "runtime_capability_max",
    ):
        if key not in baseline_snapshot:
            errors.append(f"baseline_snapshot missing key: {key}")

    for key in (
        "catalog_scene_count",
        "runtime_scene_count",
        "catalog_runtime_ratio",
        "runtime_capability_min",
        "runtime_capability_avg",
        "runtime_capability_max",
    ):
        if key not in delta_vs_baseline:
            errors.append(f"delta_vs_baseline missing key: {key}")

    if isinstance(summary.get("warning_count"), int) and len(warnings) != int(summary.get("warning_count")):
        errors.append(
            f"warning_count mismatch: summary={summary.get('warning_count')} actual={len(warnings)}"
        )
    for idx, item in enumerate(warnings):
        if not isinstance(item, str):
            errors.append(f"warnings[{idx}] must be string")

    if errors:
        print("[runtime_surface_dashboard_schema_guard] FAIL")
        for item in errors:
            print(item)
        return 1
    print("[runtime_surface_dashboard_schema_guard] PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
