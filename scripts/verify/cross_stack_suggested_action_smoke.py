#!/usr/bin/env python3
"""Cross-stack static smoke for suggested_action proof chain.

Purpose:
- Prove backend -> scene/access contract -> frontend action runtime -> trace export chain is wired.
- Keep this fast and deterministic (no DB/container dependency).
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

REQUIRED_PATTERNS = {
    "addons/smart_core/handlers/system_init.py": [
        'suggested_action = str(access.get("suggested_action") or "").strip()',
        'failure_meta_for_reason(reason_code).get("suggested_action")',
    ],
    "scripts/verify/scene_contract_shape_guard.py": [
        'access.get("suggested_action")',
        'access.suggested_action must be str',
    ],
    "frontend/apps/web/src/services/trace.ts": [
        "intent: 'suggested_action.run'",
        "export function exportSuggestedActionTraces",
        "export function rankSuggestedActionKinds",
        "export function summarizeSuggestedActionTraceFilter",
    ],
    "frontend/apps/web/src/layouts/AppShell.vue": [
        "exportSuggestedActionTraces(",
        "rankSuggestedActionKinds(",
        "const hudActions = computed(() => [",
    ],
    "frontend/apps/web/src/views/MyWorkView.vue": [
        "resolveSuggestedAction(",
        "runSuggestedAction(",
    ],
    "frontend/apps/web/src/views/ActionView.vue": [
        "resolveSuggestedAction(",
        "runSuggestedAction(",
    ],
}


def _read(rel_path: str) -> str:
    path = ROOT / rel_path
    if not path.exists():
        raise FileNotFoundError(rel_path)
    return path.read_text(encoding="utf-8")


def main() -> int:
    errors: list[str] = []
    checked = 0
    for rel_path, patterns in REQUIRED_PATTERNS.items():
        try:
            text = _read(rel_path)
        except FileNotFoundError:
            errors.append(f"missing file: {rel_path}")
            continue
        checked += 1
        for pattern in patterns:
            if pattern not in text:
                errors.append(f"{rel_path}: missing pattern -> {pattern}")

    if errors:
        print("[FAIL] cross-stack suggested_action smoke")
        for err in errors:
            print(f"- {err}")
        return 1

    print("[OK] cross-stack suggested_action smoke")
    print(f"- files_checked: {checked}")
    print(f"- chain: backend -> scene-shape -> frontend-runtime -> trace-export")
    return 0


if __name__ == "__main__":
    sys.exit(main())
