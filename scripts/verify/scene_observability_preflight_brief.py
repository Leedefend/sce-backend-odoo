#!/usr/bin/env python3
"""Print concise readiness summary from latest preflight readiness output."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_INPUT = ROOT / "artifacts" / "scene_observability_preflight_readiness.latest.json"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", default=str(DEFAULT_INPUT))
    parser.add_argument("--strict", action="store_true")
    args = parser.parse_args()

    path = Path(args.input)
    if not path.exists():
        print(f"[FAIL] readiness file missing: {path}")
        return 2
    payload = json.loads(path.read_text(encoding="utf-8"))
    readiness = payload.get("readiness") if isinstance(payload, dict) else {}
    strict_ready = bool((readiness or {}).get("strict_ready"))
    reasons = [str(x) for x in ((readiness or {}).get("strict_failure_reasons") or [])]
    run_dir = str(payload.get("run_dir") or "-")

    print("[OK] scene observability preflight brief")
    print(f"- run_dir: {run_dir}")
    print(f"- strict_ready: {strict_ready}")
    print(f"- strict_failure_reasons: {', '.join(reasons) if reasons else '-'}")

    if args.strict and not strict_ready:
        print("[FAIL] strict readiness required but unmet")
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
