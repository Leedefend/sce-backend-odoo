#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

import json
import os
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_ARTIFACT = ROOT / "artifacts" / "backend" / "scene_capability_matrix_report.json"


def _resolve_artifact_path() -> Path:
    candidates = []
    raw_dir = str(os.getenv("ARTIFACTS_DIR") or "").strip()
    if raw_dir:
        candidates.append(Path(raw_dir) / "backend" / "scene_capability_matrix_report.json")
    candidates.append(Path("/mnt/artifacts/backend/scene_capability_matrix_report.json"))
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
    payload = _load_json(_resolve_artifact_path())
    if not payload:
        print("[scene_capability_matrix_report_schema_guard] FAIL")
        print("missing or invalid artifact")
        return 1

    errors: list[str] = []
    if not isinstance(payload.get("ok"), bool):
        errors.append("ok must be bool")
    summary = payload.get("summary")
    if not isinstance(summary, dict):
        errors.append("summary must be object")
        summary = {}
    for key in (
        "probe_login",
        "probe_source",
        "scene_count",
        "capability_count",
        "scene_without_binding_count",
        "unused_capability_count",
        "missing_capability_ref_count",
        "warning_count",
        "error_count",
        "role_sample_count",
    ):
        if key not in summary:
            errors.append(f"summary missing key: {key}")

    for key in ("role_samples", "capability_keys", "scene_keys", "scene_without_binding", "unused_capabilities", "matrix", "errors"):
        if key not in payload:
            errors.append(f"payload missing key: {key}")

    matrix = payload.get("matrix") if isinstance(payload.get("matrix"), list) else []
    for idx, item in enumerate(matrix):
        if not isinstance(item, dict):
            errors.append(f"matrix[{idx}] must be object")
            continue
        for key in ("scene_key", "declared_capabilities", "required_capabilities", "all_capabilities", "missing_capabilities"):
            if key not in item:
                errors.append(f"matrix[{idx}] missing key: {key}")

    scene_keys = payload.get("scene_keys") if isinstance(payload.get("scene_keys"), list) else []
    if scene_keys != sorted(scene_keys):
        errors.append("scene_keys must be sorted")
    capability_keys = payload.get("capability_keys") if isinstance(payload.get("capability_keys"), list) else []
    if capability_keys != sorted(capability_keys):
        errors.append("capability_keys must be sorted")
    matrix_keys = [str(item.get("scene_key") or "") for item in matrix if isinstance(item, dict)]
    if matrix_keys != sorted(matrix_keys):
        errors.append("matrix must be sorted by scene_key")

    if errors:
        print("[scene_capability_matrix_report_schema_guard] FAIL")
        for item in errors:
            print(item)
        return 1
    print("[scene_capability_matrix_report_schema_guard] PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
