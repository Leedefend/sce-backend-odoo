#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
MAPPING_FILE = ROOT / "docs" / "product" / "capability_scene_mapping_v1.json"
MIN_PRODUCT_MAPPING_RATE = 0.85


def main() -> int:
    if not MAPPING_FILE.is_file():
        raise SystemExit(f"[FAIL] missing file: {MAPPING_FILE}")

    payload = json.loads(MAPPING_FILE.read_text(encoding="utf-8"))
    summary = payload.get("quality_summary") if isinstance(payload.get("quality_summary"), dict) else {}
    product_total = int(summary.get("product_scene_total") or 0)
    product_mapped = int(summary.get("product_scene_mapped") or 0)
    rate = float(summary.get("mapping_rate_product") or 0)

    if product_total <= 0:
        raise SystemExit("[FAIL] product_scene_total must be > 0")
    if rate < MIN_PRODUCT_MAPPING_RATE:
        raise SystemExit(
            f"[FAIL] product scene mapping rate too low: {rate:.4f} < {MIN_PRODUCT_MAPPING_RATE:.2f} "
            f"(mapped={product_mapped}, total={product_total})"
        )

    print(
        "[PASS] product scene mapping guard "
        f"rate={rate:.4f} mapped={product_mapped} total={product_total}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
