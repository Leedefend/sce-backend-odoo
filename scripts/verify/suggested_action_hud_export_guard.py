#!/usr/bin/env python3
"""Guard HUD export wiring for suggested_action traces."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
APP_SHELL = ROOT / "frontend/apps/web/src/layouts/AppShell.vue"
DEV_CONTEXT_PANEL = ROOT / "frontend/apps/web/src/components/DevContextPanel.vue"

REQUIRED_SHELL_SNIPPETS = [
    "exportSuggestedActionTraces",
    ":actions=\"hudActions\"",
    "exportSuggestedActionJson({ success: true }, 'ok')",
    "exportSuggestedActionJson({ success: false }, 'fail')",
    "exportSuggestedActionJson({ kind: 'open_record' }, 'kind-open_record')",
    "exportSuggestedActionJson({ kind: 'copy_trace' }, 'kind-copy_trace')",
    "exportSuggestedActionJson({ kind: 'refresh' }, 'kind-refresh')",
]

REQUIRED_PANEL_SNIPPETS = [
    "actions?: Array<{ key: string; label: string; onClick: () => void }>",
    "v-if=\"actions?.length\"",
    "class=\"action-btn\"",
]


def _check(path: Path, snippets: list[str], label: str) -> list[str]:
    if not path.exists():
        return [f"missing file: {path}"]
    text = path.read_text(encoding="utf-8")
    return [f"{label} missing snippet: {snippet}" for snippet in snippets if snippet not in text]


def main() -> int:
    errors = []
    errors.extend(_check(APP_SHELL, REQUIRED_SHELL_SNIPPETS, "AppShell"))
    errors.extend(_check(DEV_CONTEXT_PANEL, REQUIRED_PANEL_SNIPPETS, "DevContextPanel"))
    if errors:
        print("[FAIL] suggested_action HUD export guard")
        for err in errors:
            print(f"- {err}")
        return 1

    print("[OK] suggested_action HUD export guard")
    return 0


if __name__ == "__main__":
    sys.exit(main())
