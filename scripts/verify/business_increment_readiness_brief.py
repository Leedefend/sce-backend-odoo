#!/usr/bin/env python3
"""Print concise business increment readiness summary."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_INPUT = ROOT / "artifacts" / "business_increment_readiness.latest.json"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", default=str(DEFAULT_INPUT))
    parser.add_argument("--profile", default="")
    parser.add_argument("--strict", action="store_true")
    args = parser.parse_args()

    path = Path(args.input)
    if not path.exists():
        print(f"[FAIL] business increment readiness file missing: {path}")
        return 2

    payload = json.loads(path.read_text(encoding="utf-8"))
    summary = payload.get("summary") if isinstance(payload, dict) else {}
    profile = str((summary or {}).get("profile") or "")
    expected_profile = str(args.profile or "").strip()
    if expected_profile and expected_profile != profile:
        print("[FAIL] business increment readiness brief")
        print(f"- profile mismatch: expected={expected_profile} actual={profile or '-'}")
        return 2

    ready = bool((summary or {}).get("ready"))
    intent_count = int((summary or {}).get("intent_count", 0))
    scene_count = int((summary or {}).get("scene_count", 0))
    renderable = bool((summary or {}).get("renderability_fully_renderable"))
    blockers = [str(x) for x in ((summary or {}).get("blockers") or [])]
    warnings = [str(x) for x in ((summary or {}).get("warnings") or [])]

    print("[OK] business increment readiness brief")
    print(f"- profile: {profile or '-'}")
    print(f"- ready: {ready}")
    print(f"- intent_count: {intent_count}")
    print(f"- scene_count: {scene_count}")
    print(f"- renderability_fully_renderable: {renderable}")
    print(f"- blockers: {', '.join(blockers) if blockers else '-'}")
    print(f"- warnings: {', '.join(warnings) if warnings else '-'}")

    if args.strict and not ready:
        print("[FAIL] readiness required but unmet")
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
