#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
REPORT_FILE = ROOT / "docs" / "product" / "entry_registry_quality_report_v1.json"
MIN_COVERAGE = 0.95


def main() -> int:
    if not REPORT_FILE.is_file():
        raise SystemExit(f"[FAIL] missing file: {REPORT_FILE}")
    payload = json.loads(REPORT_FILE.read_text(encoding="utf-8"))
    summary = payload.get("summary") if isinstance(payload.get("summary"), dict) else {}
    status = str(payload.get("status") or "").strip().lower()

    scene_cov = float(summary.get("scene_entry_coverage") or 0.0)
    cap_cov = float(summary.get("capability_entry_coverage") or 0.0)

    if scene_cov < MIN_COVERAGE:
        raise SystemExit(f"[FAIL] scene entry coverage too low: {scene_cov:.4f} < {MIN_COVERAGE:.2f}")
    if cap_cov < MIN_COVERAGE:
        raise SystemExit(f"[FAIL] capability entry coverage too low: {cap_cov:.4f} < {MIN_COVERAGE:.2f}")
    if status == "fail":
        raise SystemExit("[FAIL] entry registry quality report status=fail")

    print(f"[PASS] entry registry quality guard scene_cov={scene_cov:.4f} cap_cov={cap_cov:.4f} status={status or 'n/a'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
