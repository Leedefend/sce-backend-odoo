#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
REPORT_FILE = ROOT / "docs" / "product" / "navigation_registry_quality_report_v1.json"
MIN_COVERAGE = 0.95


def main() -> int:
    if not REPORT_FILE.is_file():
        raise SystemExit(f"[FAIL] missing file: {REPORT_FILE}")
    payload = json.loads(REPORT_FILE.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise SystemExit("[FAIL] invalid report payload")
    summary = payload.get("summary") if isinstance(payload.get("summary"), dict) else {}
    issues = payload.get("issues") if isinstance(payload.get("issues"), dict) else {}

    scene_coverage = float(summary.get("scene_coverage") or 0.0)
    capability_coverage = float(summary.get("capability_coverage") or 0.0)
    if scene_coverage < MIN_COVERAGE:
        raise SystemExit(f"[FAIL] scene coverage too low: {scene_coverage:.4f} < {MIN_COVERAGE:.2f}")
    if capability_coverage < MIN_COVERAGE:
        raise SystemExit(f"[FAIL] capability coverage too low: {capability_coverage:.4f} < {MIN_COVERAGE:.2f}")

    for key in ("unknown_source_entries", "duplicate_registry_keys", "scene_ref_missing", "capability_ref_missing"):
        values = issues.get(key) or []
        if values:
            raise SystemExit(f"[FAIL] quality issue found in {key}: {', '.join(map(str, values[:12]))}")

    print(
        "[PASS] navigation registry quality guard "
        f"scene_coverage={scene_coverage:.4f} capability_coverage={capability_coverage:.4f}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
