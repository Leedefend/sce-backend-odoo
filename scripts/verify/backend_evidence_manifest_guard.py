#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

import json
import os
from pathlib import Path
import re
import sys


ROOT = Path(__file__).resolve().parents[2]
BASELINE_JSON = ROOT / "scripts" / "verify" / "baselines" / "backend_evidence_manifest_guard.json"
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
    baseline = _load_json(BASELINE_JSON)
    if not baseline:
        print("[backend_evidence_manifest_guard] FAIL")
        print(f"missing or invalid baseline: {BASELINE_JSON.relative_to(ROOT).as_posix()}")
        return 1

    manifest_path = _resolve_manifest_path()
    manifest = _load_json(manifest_path)
    if not manifest:
        print("[backend_evidence_manifest_guard] FAIL")
        print(f"missing or invalid manifest: {manifest_path}")
        return 1

    errors: list[str] = []
    summary = manifest.get("summary") if isinstance(manifest.get("summary"), dict) else {}
    artifacts = manifest.get("artifacts") if isinstance(manifest.get("artifacts"), list) else []
    required = {
        str(item).strip()
        for item in (baseline.get("required_artifacts") if isinstance(baseline.get("required_artifacts"), list) else [])
        if str(item).strip()
    }
    if not required:
        errors.append("baseline.required_artifacts is empty")

    seen = set()
    sha_pat = re.compile(r"^[0-9a-f]{64}$")
    for idx, row in enumerate(artifacts):
        if not isinstance(row, dict):
            errors.append(f"artifacts[{idx}] must be object")
            continue
        path = str(row.get("path") or "").strip()
        seen.add(path)
        exists = bool(row.get("exists"))
        size_bytes = _safe_int(row.get("size_bytes"), -1)
        sha = str(row.get("sha256") or "").strip()
        if exists:
            if size_bytes < 1:
                errors.append(f"artifacts[{idx}] size_bytes must be > 0 when exists=true")
            if not sha_pat.match(sha):
                errors.append(f"artifacts[{idx}] sha256 invalid")
        else:
            if sha:
                errors.append(f"artifacts[{idx}] sha256 must be empty when exists=false")

    missing_required = sorted(required - seen)
    if missing_required:
        errors.append(f"required artifacts missing from manifest rows: {', '.join(missing_required)}")

    max_missing = _safe_int(baseline.get("max_missing_count"), 0)
    min_total_size = _safe_int(baseline.get("min_total_size_bytes"), 0)
    missing_count = _safe_int(summary.get("missing_count"), 0)
    total_size_bytes = _safe_int(summary.get("total_size_bytes"), 0)
    if missing_count > max_missing:
        errors.append(f"summary.missing_count exceeded: {missing_count} > {max_missing}")
    if total_size_bytes < min_total_size:
        errors.append(f"summary.total_size_bytes too small: {total_size_bytes} < {min_total_size}")

    if errors:
        print("[backend_evidence_manifest_guard] FAIL")
        for item in errors:
            print(item)
        return 1
    print("[backend_evidence_manifest_guard] PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
