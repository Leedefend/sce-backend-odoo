#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

import json
import os
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_MANIFEST = ROOT / "artifacts" / "backend" / "backend_evidence_manifest.json"


def _resolve_manifest_path() -> Path:
    candidates = []
    raw_dir = str(os.getenv("ARTIFACTS_DIR") or "").strip()
    if raw_dir:
        candidates.append(Path(raw_dir) / "backend" / "backend_evidence_manifest.json")
    candidates.append(Path("/mnt/artifacts/backend/backend_evidence_manifest.json"))
    candidates.append(DEFAULT_MANIFEST)
    for path in candidates:
        if path.is_file():
            return path
    return DEFAULT_MANIFEST


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


def main() -> int:
    path = _resolve_manifest_path()
    payload = _load_json(path)
    if not payload:
        print("[backend_evidence_manifest_schema_guard] FAIL")
        print(f"missing or invalid manifest: {path}")
        return 1

    errors: list[str] = []
    if not isinstance(payload.get("ok"), bool):
        errors.append("ok must be bool")
    summary = payload.get("summary") if isinstance(payload.get("summary"), dict) else {}
    baseline = payload.get("baseline") if isinstance(payload.get("baseline"), dict) else {}
    artifacts = payload.get("artifacts") if isinstance(payload.get("artifacts"), list) else None
    missing = payload.get("missing") if isinstance(payload.get("missing"), list) else None
    if not summary:
        errors.append("summary must be object")
    if not baseline:
        errors.append("baseline must be object")
    if artifacts is None:
        errors.append("artifacts must be list")
        artifacts = []
    if missing is None:
        errors.append("missing must be list")
        missing = []

    for key in ("artifact_count", "present_count", "missing_count", "total_size_bytes", "artifacts_dir"):
        if key not in summary:
            errors.append(f"summary missing key: {key}")

    rows_missing = []
    rows_present = 0
    total_size_bytes = 0
    paths = []
    for idx, row in enumerate(artifacts):
        if not isinstance(row, dict):
            errors.append(f"artifacts[{idx}] must be object")
            continue
        for key in ("path", "exists", "size_bytes", "sha256"):
            if key not in row:
                errors.append(f"artifacts[{idx}] missing key: {key}")
        row_path = str(row.get("path") or "").strip()
        if not row_path:
            errors.append(f"artifacts[{idx}].path is required")
        paths.append(row_path)
        exists = bool(row.get("exists"))
        size_bytes = _safe_int(row.get("size_bytes"), -1)
        if exists:
            rows_present += 1
            if size_bytes < 1:
                errors.append(f"artifacts[{idx}].size_bytes must be > 0 when exists=true")
        else:
            rows_missing.append(row_path)
            if size_bytes != 0:
                errors.append(f"artifacts[{idx}].size_bytes must be 0 when exists=false")
        if size_bytes > 0:
            total_size_bytes += size_bytes

    if paths != sorted(paths):
        errors.append("artifacts must be sorted by path for deterministic diff")
    missing_sorted = sorted([str(item).strip() for item in missing if str(item).strip()])
    if missing_sorted != sorted(rows_missing):
        errors.append("missing list mismatch with artifacts rows")

    if _safe_int(summary.get("artifact_count"), -1) != len(artifacts):
        errors.append("summary.artifact_count mismatch")
    if _safe_int(summary.get("present_count"), -1) != rows_present:
        errors.append("summary.present_count mismatch")
    if _safe_int(summary.get("missing_count"), -1) != len(rows_missing):
        errors.append("summary.missing_count mismatch")
    if _safe_int(summary.get("total_size_bytes"), -1) != total_size_bytes:
        errors.append("summary.total_size_bytes mismatch")

    if errors:
        print("[backend_evidence_manifest_schema_guard] FAIL")
        for item in errors:
            print(item)
        return 1
    print("[backend_evidence_manifest_schema_guard] PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
