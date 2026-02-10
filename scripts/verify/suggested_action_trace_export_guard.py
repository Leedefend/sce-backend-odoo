#!/usr/bin/env python3
"""Guard suggested_action trace export API surface."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
TRACE_PATH = ROOT / "frontend/apps/web/src/services/trace.ts"

REQUIRED_SNIPPETS = [
    "export interface SuggestedActionTraceFilter",
    "export interface SuggestedActionTraceRow",
    "export function listSuggestedActionTraces(filter: SuggestedActionTraceFilter = {})",
    "export function exportSuggestedActionTraces(filter: SuggestedActionTraceFilter = {})",
    "filter:",
    "summary:",
    "success_count:",
    "failure_count:",
    "top_k:",
    "items:",
]


def main() -> int:
    if not TRACE_PATH.exists():
        print(f"[FAIL] missing trace service: {TRACE_PATH}")
        return 1

    text = TRACE_PATH.read_text(encoding="utf-8")
    missing = [snippet for snippet in REQUIRED_SNIPPETS if snippet not in text]

    if missing:
        print("[FAIL] suggested_action trace export guard")
        for snippet in missing:
            print(f"- missing snippet: {snippet}")
        return 1

    print("[OK] suggested_action trace export guard")
    return 0


if __name__ == "__main__":
    sys.exit(main())
