#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
MY_WORK_VIEW = ROOT / "frontend/apps/web/src/views/MyWorkView.vue"

REQUIRED_TOKENS = [
    "<PageRenderer",
    "v-if=\"useUnifiedMyWorkRenderer\"",
    ":contract=\"myWorkOrchestrationContract\"",
    ":datasets=\"myWorkOrchestrationDatasets\"",
    "@action=\"handleMyWorkBlockAction\"",
    "const myWorkOrchestrationContract = computed<PageOrchestrationContract>(() => {",
    "const useUnifiedMyWorkRenderer = computed(() => {",
    "const myWorkOrchestrationDatasets = computed<Record<string, unknown>>(() => {",
    "async function handleMyWorkBlockAction(event: PageBlockActionEvent)",
]


def _fail(errors: list[str]) -> int:
    print("[frontend_my_work_block_migration_guard] FAIL")
    for err in errors:
        print(f"- {err}")
    return 1


def main() -> int:
    if not MY_WORK_VIEW.is_file():
        return _fail([f"missing file: {MY_WORK_VIEW.relative_to(ROOT).as_posix()}"])

    text = MY_WORK_VIEW.read_text(encoding="utf-8", errors="ignore")
    errors: list[str] = []
    for token in REQUIRED_TOKENS:
        if token not in text:
            errors.append(f"MyWorkView missing token: {token}")

    if "<section v-else class=\"my-work\"" not in text:
        errors.append("MyWorkView must keep legacy fallback section with v-else")

    if errors:
        return _fail(errors)

    print("[frontend_my_work_block_migration_guard] PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
