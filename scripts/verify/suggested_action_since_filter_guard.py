#!/usr/bin/env python3
"""Guard since_ts filter support for suggested_action trace APIs."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
TRACE_PATH = ROOT / "frontend/apps/web/src/services/trace.ts"

REQUIRED_SNIPPETS = [
    "since_ts?: number;",
    "const sinceTs = Number(filter.since_ts || 0);",
    "if (sinceTs > 0 && row.ts < sinceTs) continue;",
    "since_ts: Number(filter.since_ts || 0) > 0 ? Number(filter.since_ts) : undefined",
]


def main() -> int:
    if not TRACE_PATH.exists():
        print(f"[FAIL] missing file: {TRACE_PATH}")
        return 1
    text = TRACE_PATH.read_text(encoding="utf-8")
    missing = [item for item in REQUIRED_SNIPPETS if item not in text]
    if missing:
        print("[FAIL] suggested_action since filter guard")
        for item in missing:
            print(f"- missing snippet: {item}")
        return 1
    print("[OK] suggested_action since filter guard")
    return 0


if __name__ == "__main__":
    sys.exit(main())
