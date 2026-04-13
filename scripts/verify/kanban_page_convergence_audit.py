#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def main() -> int:
    path = ROOT / "frontend" / "apps" / "web" / "src" / "pages" / "KanbanPage.vue"
    text = path.read_text(encoding="utf-8")

    checks = [
        "title=\"正在加载看板...\"",
        "props.errorMessage || '看板加载失败'",
        "const groupedFilterTabs = computed(() => {",
        "class=\"kanban-filter-tabs\"",
        "class=\"kanban-filter-tab\"",
        "const filteredGroupColumns = computed(() => {",
        "const filteredRecords = computed(() => {",
        "function selectGroupedTab(key: string) {",
    ]
    errors: list[str] = []
    for token in checks:
        if token not in text:
            errors.append(f"missing_token:{token}")

    if errors:
        for item in errors:
            print(f"[kanban_page_convergence_audit] FAIL: {item}")
        return 2

    print("[kanban_page_convergence_audit] PASS")
    print("- grouped filter tabs convergence: PASS")
    print("- kanban feedback copy convergence: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
