#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

import json
import os
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_ARTIFACT = ROOT / "artifacts" / "backend" / "role_capability_floor_prod_like.json"


def _resolve_artifact_path() -> Path:
    candidates = []
    raw_dir = str(os.getenv("ARTIFACTS_DIR") or "").strip()
    if raw_dir:
        candidates.append(Path(raw_dir) / "backend" / "role_capability_floor_prod_like.json")
    candidates.append(Path("/mnt/artifacts/backend/role_capability_floor_prod_like.json"))
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
        print("[role_capability_floor_prod_like_schema_guard] FAIL")
        print(f"missing or invalid artifact: {path}")
        return 1

    errors: list[str] = []
    summary = report.get("summary") if isinstance(report.get("summary"), dict) else {}
    roles = report.get("roles") if isinstance(report.get("roles"), list) else []
    if not isinstance(report.get("ok"), bool):
        errors.append("ok must be bool")
    if not summary:
        errors.append("summary must be object")
    if not roles:
        errors.append("roles must be non-empty list")
    for key in ("fixture_count", "passed_fixture_count", "failed_fixture_count", "error_count"):
        if key not in summary:
            errors.append(f"summary missing key: {key}")
    for idx, row in enumerate(roles):
        if not isinstance(row, dict):
            errors.append(f"roles[{idx}] must be object")
            continue
        for key in ("role", "login", "ok", "capability_count", "journey", "failure_reason"):
            if key not in row:
                errors.append(f"roles[{idx}] missing key: {key}")
        if not isinstance(row.get("ok"), bool):
            errors.append(f"roles[{idx}].ok must be bool")
        if not isinstance(row.get("journey"), list):
            errors.append(f"roles[{idx}].journey must be list")
        for j, journey in enumerate(row.get("journey") if isinstance(row.get("journey"), list) else []):
            if not isinstance(journey, dict):
                errors.append(f"roles[{idx}].journey[{j}] must be object")
                continue
            for key in ("intent", "ok", "reason"):
                if key not in journey:
                    errors.append(f"roles[{idx}].journey[{j}] missing key: {key}")

    if errors:
        print("[role_capability_floor_prod_like_schema_guard] FAIL")
        for item in errors:
            print(item)
        return 1
    print("[role_capability_floor_prod_like_schema_guard] PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
