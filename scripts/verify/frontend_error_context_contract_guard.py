#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]

REQUIRED = {
    "frontend/apps/web/src/api/client.ts": [
        "details?: Record<string, unknown>;",
        "details = payload?.error?.details || payload?.details;",
    ],
    "frontend/apps/web/src/composables/useStatus.ts": [
        "details?: Record<string, unknown>;",
        "errorContextHint(",
        "err?.details?.model",
        "Context:",
    ],
    "frontend/apps/web/src/components/StatusPanel.vue": [
        "errorDetails?: Record<string, unknown>;",
        "Context:",
        "errorDetails?.model",
        "errorDetails?.op",
    ],
    "frontend/apps/web/src/app/errorContext.ts": [
        "collectErrorContextIssue(",
        "summarizeErrorContextIssues(",
        "issueScopeLabel(",
    ],
}


def fail(msg: str) -> int:
    print("[frontend_error_context_contract_guard] FAIL")
    print(msg)
    return 1


def main() -> int:
    missing: list[str] = []
    scanned = 0
    for rel, tokens in REQUIRED.items():
        path = ROOT / rel
        if not path.is_file():
            missing.append(f"{rel}: file missing")
            continue
        scanned += 1
        text = path.read_text(encoding="utf-8", errors="ignore")
        for token in tokens:
            if token not in text:
                missing.append(f"{rel}: missing token -> {token}")
    if missing:
        return fail("\n".join(missing))
    print("[frontend_error_context_contract_guard] PASS")
    print(f"scanned_files={scanned}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
