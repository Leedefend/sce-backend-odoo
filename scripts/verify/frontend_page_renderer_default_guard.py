#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]

REQUIRED = {
    "frontend/apps/web/src/views/HomeView.vue": [
        "<PageRenderer",
        'v-if="useUnifiedHomeRenderer"',
        "const useUnifiedHomeRenderer = computed(() => {",
        "route.query.legacy_home",
        "const hasV1 =",
        "const isDashboard =",
        "return hasV1 && isDashboard && zones.length > 0;",
        "<section v-else",
    ],
    "frontend/apps/web/src/views/WorkbenchView.vue": [
        "<PageRenderer",
        'v-if="useUnifiedWorkbenchRenderer"',
        "const useUnifiedWorkbenchRenderer = computed(() => {",
        "route.query.legacy_workbench",
        "const hasV1 =",
        "return hasV1 && zones.length > 0;",
        "<section v-else",
    ],
    "frontend/apps/web/src/views/MyWorkView.vue": [
        "<PageRenderer",
        'v-if="useUnifiedMyWorkRenderer"',
        "const useUnifiedMyWorkRenderer = computed(() => {",
        "route.query.legacy_my_work",
        "const hasV1 =",
        "return hasV1 && zones.length > 0;",
        "<section v-else",
    ],
}


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="ignore") if path.is_file() else ""


def _fail(errors: list[str]) -> int:
    print("[frontend_page_renderer_default_guard] FAIL")
    for err in errors:
        print(f"- {err}")
    return 1


def main() -> int:
    errors: list[str] = []
    for rel, tokens in REQUIRED.items():
        text = _read(ROOT / rel)
        if not text:
            errors.append(f"missing file: {rel}")
            continue
        for token in tokens:
            if token not in text:
                errors.append(f"{rel} missing token: {token}")
    if errors:
        return _fail(errors)
    print("[frontend_page_renderer_default_guard] PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
