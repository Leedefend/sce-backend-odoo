#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

import json
import os
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_ARTIFACT = ROOT / "artifacts" / "backend" / "boundary_import_guard_report.json"
BASELINE_JSON = ROOT / "scripts" / "verify" / "baselines" / "boundary_import_guard_strict_guard.json"


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


def _safe_int(value, default: int = 0) -> int:
    try:
        return int(value)
    except Exception:
        return default


def main() -> int:
    baseline = _load_json(BASELINE_JSON)
    max_warning_count = _safe_int(os.getenv("SC_BOUNDARY_IMPORT_WARN_MAX"), _safe_int(baseline.get("max_warning_count"), 0))
    max_violation_count = _safe_int(
        os.getenv("SC_BOUNDARY_IMPORT_VIOLATION_MAX"),
        _safe_int(baseline.get("max_violation_count"), 0),
    )

    path = _resolve_artifact_path()
    payload = _load_json(path)
    if not payload:
        print("[boundary_import_guard_strict_guard] FAIL")
        print(f"missing or invalid artifact: {path}")
        return 1

    summary = payload.get("summary") if isinstance(payload.get("summary"), dict) else {}
    warning_count = _safe_int(summary.get("warning_count"), -1)
    violation_count = _safe_int(summary.get("violation_count"), -1)
    if warning_count < 0 or violation_count < 0:
        print("[boundary_import_guard_strict_guard] FAIL")
        print("summary.warning_count or summary.violation_count missing")
        return 1

    if warning_count > max_warning_count:
        print("[boundary_import_guard_strict_guard] FAIL")
        print(f"warning_count exceeded: {warning_count} > {max_warning_count}")
        return 1
    if violation_count > max_violation_count:
        print("[boundary_import_guard_strict_guard] FAIL")
        print(f"violation_count exceeded: {violation_count} > {max_violation_count}")
        return 1

    print("[boundary_import_guard_strict_guard] PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())

