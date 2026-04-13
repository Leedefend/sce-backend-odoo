#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def file_contains(path: Path, token: str) -> bool:
    return token in path.read_text(encoding="utf-8")


def main() -> int:
    errors: list[str] = []

    page_layout = ROOT / "frontend" / "apps" / "web" / "src" / "components" / "page" / "PageLayout.vue"
    page_feedback = ROOT / "frontend" / "apps" / "web" / "src" / "components" / "page" / "PageFeedback.vue"
    list_page = ROOT / "frontend" / "apps" / "web" / "src" / "pages" / "ListPage.vue"
    kanban_page = ROOT / "frontend" / "apps" / "web" / "src" / "pages" / "KanbanPage.vue"

    checks = [
        (page_layout, "<slot name=\"header\""),
        (page_layout, "<slot name=\"filter\""),
        (page_layout, "<slot name=\"content\""),
        (page_layout, "<slot name=\"feedback\""),
        (page_feedback, "<section class=\"page-feedback\""),
        (list_page, "<PageLayout class=\"page\">"),
        (list_page, "<template #header>"),
        (list_page, "<template #filter>"),
        (kanban_page, "<PageLayout class=\"page\">"),
        (kanban_page, "<PageFeedback>"),
        (kanban_page, "<template #feedback>"),
    ]

    for file_path, token in checks:
        if not file_path.exists():
            errors.append(f"missing_file:{file_path}")
            continue
        if not file_contains(file_path, token):
            errors.append(f"missing_token:{file_path}:{token}")

    if errors:
        for item in errors:
            print(f"[page_layout_convergence_audit] FAIL: {item}")
        return 2

    print("[page_layout_convergence_audit] PASS")
    print("- unified page skeleton components: PASS")
    print("- list/kanban page layout convergence: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
