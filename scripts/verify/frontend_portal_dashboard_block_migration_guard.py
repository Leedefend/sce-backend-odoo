#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
HOME_VIEW = ROOT / "frontend/apps/web/src/views/HomeView.vue"

REQUIRED_TOKENS = [
    "<PageRenderer",
    "v-if=\"useUnifiedHomeRenderer\"",
    ":contract=\"homeOrchestrationContract\"",
    ":datasets=\"homeOrchestrationDatasets\"",
    "@action=\"handleHomeBlockAction\"",
    "const homeOrchestrationDatasets = computed<Record<string, unknown>>(() => {",
    "ds_metrics",
    "ds_today_todos",
    "ds_risk_alerts",
    "ds_scene_groups",
    "ds_capability_groups",
]


def _fail(errors: list[str]) -> int:
    print("[frontend_portal_dashboard_block_migration_guard] FAIL")
    for err in errors:
        print(f"- {err}")
    return 1


def main() -> int:
    if not HOME_VIEW.is_file():
        return _fail([f"missing file: {HOME_VIEW.relative_to(ROOT).as_posix()}"])

    text = HOME_VIEW.read_text(encoding="utf-8", errors="ignore")
    errors: list[str] = []
    for token in REQUIRED_TOKENS:
        if token not in text:
            errors.append(f"HomeView missing token: {token}")

    if "<section v-else class=\"capability-home\"" not in text:
        errors.append("HomeView must keep legacy fallback section with v-else")

    if errors:
        return _fail(errors)

    print("[frontend_portal_dashboard_block_migration_guard] PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
