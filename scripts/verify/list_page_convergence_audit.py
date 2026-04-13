#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def main() -> int:
    path = ROOT / "frontend" / "apps" / "web" / "src" / "pages" / "ListPage.vue"
    text = path.read_text(encoding="utf-8")
    checks = [
        ":quick-filters=\"convergedQuickFilters\"",
        ":saved-filters=\"convergedSavedFilters\"",
        "const convergedQuickFilters = computed(() => quickFilters.value);",
        "if (quickFilters.value.length > 0) return [];",
        "StatusPanel",
        "PageHeader",
        "PageToolbar",
    ]
    errors: list[str] = []
    for token in checks:
        if token not in text:
            errors.append(f"missing_token:{token}")

    if errors:
        for item in errors:
            print(f"[list_page_convergence_audit] FAIL: {item}")
        return 2

    print("[list_page_convergence_audit] PASS")
    print("- single filter system convergence: PASS")
    print("- header/toolbar/feedback presence: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
