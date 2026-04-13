#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def main() -> int:
    path = ROOT / "docs" / "ops" / "delivery_formal_entry_page_review_v2.md"
    if not path.exists():
        print("[formal_entry_page_review_refinement_audit] FAIL: missing_file:docs/ops/delivery_formal_entry_page_review_v2.md")
        return 2

    text = path.read_text(encoding="utf-8")
    checks = [
        "## Delivery Gate",
        "## Formal Entry Checklist",
        "## Delivery Decision",
        "## Evidence",
        "错误可观测",
        "GO_WITH_WATCH",
        "| menu_id | menu_name |",
        "| 299 | 项目指标 |",
    ]

    errors: list[str] = []
    for token in checks:
        if token not in text:
            errors.append(f"missing_token:{token}")

    if errors:
        for item in errors:
            print(f"[formal_entry_page_review_refinement_audit] FAIL: {item}")
        return 2

    print("[formal_entry_page_review_refinement_audit] PASS")
    print("- formal entry review checklist completeness: PASS")
    print("- delivery decision and risk watchpoint documented: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
