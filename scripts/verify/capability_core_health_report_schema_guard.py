#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

import json
import os
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_ARTIFACT = ROOT / "artifacts" / "backend" / "capability_core_health_report.json"


def _resolve_artifact_path() -> Path:
    candidates = []
    raw_dir = str(os.getenv("ARTIFACTS_DIR") or "").strip()
    if raw_dir:
        candidates.append(Path(raw_dir) / "backend" / "capability_core_health_report.json")
    candidates.append(Path("/mnt/artifacts/backend/capability_core_health_report.json"))
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
        print("[capability_core_health_report_schema_guard] FAIL")
        print("missing or invalid artifact")
        return 1

    errors: list[str] = []
    if not isinstance(payload.get("ok"), bool):
        errors.append("ok must be bool")
    summary = payload.get("summary")
    if not isinstance(summary, dict):
        errors.append("summary must be object")
        summary = {}
    baseline = payload.get("baseline")
    if not isinstance(baseline, dict):
        errors.append("baseline must be object")
    roles = payload.get("roles")
    if not isinstance(roles, list):
        errors.append("roles must be list")
        roles = []
    login_failures = payload.get("login_failures")
    if not isinstance(login_failures, list):
        errors.append("login_failures must be list")
    if not isinstance(payload.get("errors"), list):
        errors.append("errors must be list")
    if not isinstance(payload.get("warnings"), list):
        errors.append("warnings must be list")

    for key in ("role_sample_count", "login_failure_count", "error_count", "warning_count"):
        if key not in summary:
            errors.append(f"summary missing key: {key}")

    for idx, role in enumerate(roles):
        if not isinstance(role, dict):
            errors.append(f"roles[{idx}] must be object")
            continue
        if not str(role.get("login") or "").strip():
            errors.append(f"roles[{idx}] missing login")
        for mode in ("user_mode", "hud_mode"):
            row = role.get(mode)
            if not isinstance(row, dict):
                errors.append(f"roles[{idx}].{mode} must be object")
                continue
            for key in ("capability_count", "group_count", "scene_count", "error_count", "warning_count"):
                if key not in row:
                    errors.append(f"roles[{idx}].{mode} missing key: {key}")

    if errors:
        print("[capability_core_health_report_schema_guard] FAIL")
        for item in errors:
            print(item)
        return 1
    print("[capability_core_health_report_schema_guard] PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
