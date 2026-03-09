#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]

REQUIRED_FILES = {
    "frontend/apps/web/src/components/page/PageRenderer.vue": [
        "<ZoneRenderer",
        "orderedZones",
    ],
    "frontend/apps/web/src/components/page/ZoneRenderer.vue": [
        "<BlockRenderer",
        "orderedBlocks",
    ],
    "frontend/apps/web/src/components/page/BlockRenderer.vue": [
        "resolveBlockComponent",
        "未支持的区块类型",
    ],
    "frontend/apps/web/src/app/pageBlockRegistry.ts": [
        "metric_row",
        "todo_list",
        "alert_panel",
        "entry_grid",
        "record_summary",
        "progress_summary",
        "activity_feed",
        "accordion_group",
    ],
    "frontend/apps/web/src/components/page/blocks/BlockRecordSummary.vue": ["block-record-summary"],
    "frontend/apps/web/src/components/page/blocks/BlockProgressSummary.vue": ["block-progress-summary"],
    "frontend/apps/web/src/components/page/blocks/BlockActivityFeed.vue": ["block-activity-feed"],
    "frontend/apps/web/src/components/page/blocks/BlockAccordionGroup.vue": ["block-accordion-group"],
}


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="ignore") if path.is_file() else ""


def _fail(errors: list[str]) -> int:
    print("[frontend_page_block_renderer_smoke_guard] FAIL")
    for err in errors:
        print(f"- {err}")
    return 1


def main() -> int:
    errors: list[str] = []
    for rel, tokens in REQUIRED_FILES.items():
        path = ROOT / rel
        text = _read(path)
        if not text:
            errors.append(f"missing file: {rel}")
            continue
        for token in tokens:
            if token not in text:
                errors.append(f"{rel} missing token: {token}")

    if errors:
        return _fail(errors)

    print("[frontend_page_block_renderer_smoke_guard] PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
