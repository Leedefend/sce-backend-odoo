#!/usr/bin/env python3
"""Guard top-k suggested_action ranking API in trace service."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
TRACE_PATH = ROOT / "frontend/apps/web/src/services/trace.ts"

REQUIRED = [
    "export interface SuggestedActionKindStat",
    "export function rankSuggestedActionKinds(limit = 5)",
    "listSuggestedActionTraces({ limit: MAX_ENTRIES })",
    ".sort((a, b) => b.count - a.count || a.kind.localeCompare(b.kind))",
]


def main() -> int:
    if not TRACE_PATH.exists():
        print(f"[FAIL] missing file: {TRACE_PATH}")
        return 1
    text = TRACE_PATH.read_text(encoding="utf-8")
    missing = [item for item in REQUIRED if item not in text]
    if missing:
        print("[FAIL] suggested_action top-k guard")
        for item in missing:
            print(f"- missing snippet: {item}")
        return 1
    print("[OK] suggested_action top-k guard")
    return 0


if __name__ == "__main__":
    sys.exit(main())
