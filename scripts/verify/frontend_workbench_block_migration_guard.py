#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
WORKBENCH_VIEW = ROOT / "frontend/apps/web/src/views/WorkbenchView.vue"

REQUIRED_TOKENS = [
    "<PageRenderer",
    "v-if=\"useUnifiedWorkbenchRenderer\"",
    ":contract=\"workbenchOrchestrationContract\"",
    ":datasets=\"workbenchOrchestrationDatasets\"",
    "@action=\"handleWorkbenchBlockAction\"",
    "const workbenchOrchestrationContract = computed<PageOrchestrationContract>(() => {",
    "const useUnifiedWorkbenchRenderer = computed(() => {",
    "const workbenchOrchestrationDatasets = computed<Record<string, unknown>>(() => {",
    "async function handleWorkbenchBlockAction(event: PageBlockActionEvent)",
    "ds_section_header",
    "ds_section_status_panel",
    "ds_section_tiles",
]


def _fail(errors: list[str]) -> int:
    print("[frontend_workbench_block_migration_guard] FAIL")
    for err in errors:
        print(f"- {err}")
    return 1


def main() -> int:
    if not WORKBENCH_VIEW.is_file():
        return _fail([f"missing file: {WORKBENCH_VIEW.relative_to(ROOT).as_posix()}"])

    text = WORKBENCH_VIEW.read_text(encoding="utf-8", errors="ignore")
    errors: list[str] = []
    for token in REQUIRED_TOKENS:
        if token not in text:
            errors.append(f"WorkbenchView missing token: {token}")

    if "<section v-else class=\"workbench\"" not in text:
        errors.append("WorkbenchView must keep legacy fallback section with v-else")

    if errors:
        return _fail(errors)

    print("[frontend_workbench_block_migration_guard] PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
