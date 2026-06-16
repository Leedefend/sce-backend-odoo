#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

import json
import os
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[2]
DB_NAME = os.getenv("DB_NAME") or os.getenv("DB") or "sc_demo"
PROBE_JSON = ROOT / "artifacts" / f"p1_locked_fact_mapping_candidate_probe.{DB_NAME}.json"

AUTO_REQUIRED = {
    ("sc.receipt.income", "partner_id"): 0.95,
    ("sc.invoice.registration", "partner_id"): 0.80,
    ("sc.tax.deduction.registration", "partner_id"): 0.80,
}
HYBRID_REQUIRED = {
    ("sc.business.entity", "partner_id"): 0.50,
}


def _load_json(path: Path) -> dict:
    if not path.is_file():
        return {}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}
    return payload if isinstance(payload, dict) else {}


def _safe_float(value, default: float = 0.0) -> float:
    try:
        return float(value)
    except Exception:
        return default


def main() -> int:
    payload = _load_json(PROBE_JSON)
    if not payload:
        print("[p1_locked_fact_mapping_candidate_guard] FAIL")
        print(f"missing or invalid probe artifact: {PROBE_JSON.relative_to(ROOT).as_posix()}")
        return 1

    probes = payload.get("probes") if isinstance(payload.get("probes"), list) else []
    by_key = {
        (item.get("model"), item.get("target")): item
        for item in probes
        if isinstance(item, dict)
    }
    errors = []
    warnings = []
    for key, min_coverage in AUTO_REQUIRED.items():
        item = by_key.get(key)
        if not item:
            errors.append(f"missing auto candidate probe: {key[0]}.{key[1]}")
            continue
        coverage = _safe_float(item.get("match_coverage"))
        if coverage < min_coverage:
            errors.append(
                f"{key[0]}.{key[1]} match_coverage {coverage:.6f} < required {min_coverage:.2f}"
            )
        if item.get("recommendation") not in ("auto_candidate", "hybrid_candidate"):
            errors.append(
                f"{key[0]}.{key[1]} recommendation is {item.get('recommendation')}, expected auto/hybrid"
            )

    for key, min_coverage in HYBRID_REQUIRED.items():
        item = by_key.get(key)
        if not item:
            warnings.append(f"missing hybrid candidate probe: {key[0]}.{key[1]}")
            continue
        coverage = _safe_float(item.get("match_coverage"))
        if coverage < min_coverage:
            warnings.append(
                f"{key[0]}.{key[1]} match_coverage {coverage:.6f} < expected {min_coverage:.2f}"
            )

    if errors:
        print("[p1_locked_fact_mapping_candidate_guard] FAIL")
        for item in errors:
            print(item)
        for item in warnings:
            print("WARN:", item)
        return 1

    print("[p1_locked_fact_mapping_candidate_guard] PASS")
    for item in warnings:
        print("WARN:", item)
    return 0


if __name__ == "__main__":
    sys.exit(main())
