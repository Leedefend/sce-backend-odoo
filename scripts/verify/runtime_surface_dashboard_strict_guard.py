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


def _safe_int(v, default: int = 0) -> int:
    try:
        return int(v)
    except Exception:
        return default


def main() -> int:
    path = _resolve_artifact_path()
    report = _load_json(path)
    if not report:
        print("[runtime_surface_dashboard_strict_guard] FAIL")
        print(f"missing or invalid artifact: {path}")
        return 1

    summary = report.get("summary") if isinstance(report.get("summary"), dict) else {}
    warning_count = _safe_int(summary.get("warning_count"), -1)
    max_warn_allowed = _safe_int(os.getenv("SC_RUNTIME_SURFACE_WARN_MAX"), 0)

    if warning_count < 0:
        print("[runtime_surface_dashboard_strict_guard] FAIL")
        print("summary.warning_count missing or invalid")
        return 1
    if warning_count > max_warn_allowed:
        print("[runtime_surface_dashboard_strict_guard] FAIL")
        print(f"warning_count exceeded: {warning_count} > {max_warn_allowed}")
        return 1

    print("[runtime_surface_dashboard_strict_guard] PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
