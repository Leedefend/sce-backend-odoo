#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
HOME_VIEW = ROOT / "frontend/apps/web/src/views/HomeView.vue"


def _fail(errors: list[str]) -> int:
    print("[frontend_page_legacy_renderer_residue_guard] FAIL")
    for err in errors:
        print(f"- {err}")
    return 1


def main() -> int:
    if not HOME_VIEW.is_file():
        return _fail([f"missing file: {HOME_VIEW.relative_to(ROOT).as_posix()}"])

    text = HOME_VIEW.read_text(encoding="utf-8", errors="ignore")
    errors: list[str] = []

    if "const useUnifiedHomeRenderer = computed(() => {" not in text:
        errors.append("HomeView missing unified renderer switch")
    if "<PageRenderer" not in text:
        errors.append("HomeView missing PageRenderer usage")
    if "<section v-else class=\"capability-home\"" not in text:
        errors.append("HomeView must keep legacy renderer fallback boundary")
    if "handleHomeBlockAction" not in text:
        errors.append("HomeView missing unified block action handler")

    if errors:
        return _fail(errors)

    print("[frontend_page_legacy_renderer_residue_guard] PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
