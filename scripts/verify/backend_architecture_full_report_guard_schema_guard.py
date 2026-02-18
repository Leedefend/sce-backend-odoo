#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

import json
import os
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[2]
BASELINE_JSON = ROOT / "scripts" / "verify" / "baselines" / "backend_architecture_full_report_guard_schema_guard.json"
DEFAULT_ARTIFACT = ROOT / "artifacts" / "backend" / "backend_architecture_full_report_guard.json"


def _resolve_artifact_path() -> Path:
    candidates = []
    raw_dir = str(os.getenv("ARTIFACTS_DIR") or "").strip()
    if raw_dir:
        candidates.append(Path(raw_dir) / "backend" / "backend_architecture_full_report_guard.json")
    candidates.append(Path("/mnt/artifacts/backend/backend_architecture_full_report_guard.json"))
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
    if not baseline:
        print("[backend_architecture_full_report_guard_schema_guard] FAIL")
        print(f"missing or invalid baseline: {BASELINE_JSON.relative_to(ROOT).as_posix()}")
        return 1

    payload = _load_json(_resolve_artifact_path())
    if not payload:
        print("[backend_architecture_full_report_guard_schema_guard] FAIL")
        print("missing or invalid guard artifact")
        return 1

    errors: list[str] = []
    if not isinstance(payload.get("ok"), bool):
        errors.append("ok must be bool")

    summary = payload.get("summary") if isinstance(payload.get("summary"), dict) else {}
    observed = payload.get("observed") if isinstance(payload.get("observed"), dict) else {}
    baseline_obj = payload.get("baseline") if isinstance(payload.get("baseline"), dict) else {}
    if not summary:
        errors.append("summary must be object")
    if not observed:
        errors.append("observed must be object")
    if not baseline_obj:
        errors.append("baseline must be object")

    required_summary_keys = [
        str(item).strip()
        for item in (baseline.get("required_summary_keys") if isinstance(baseline.get("required_summary_keys"), list) else [])
        if str(item).strip()
    ]
    required_observed_keys = [
        str(item).strip()
        for item in (baseline.get("required_observed_keys") if isinstance(baseline.get("required_observed_keys"), list) else [])
        if str(item).strip()
    ]
    for key in required_summary_keys:
        if key not in summary:
            errors.append(f"summary missing key: {key}")
    for key in required_observed_keys:
        if key not in observed:
            errors.append(f"observed missing key: {key}")

    if errors:
        print("[backend_architecture_full_report_guard_schema_guard] FAIL")
        for item in errors:
            print(item)
        return 1
    print("[backend_architecture_full_report_guard_schema_guard] PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
