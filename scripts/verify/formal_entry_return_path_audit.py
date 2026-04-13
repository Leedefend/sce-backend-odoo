#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def main() -> int:
    path = ROOT / "docs" / "ops" / "delivery_formal_entry_page_review_v2.md"
    if not path.exists():
        print("[formal_entry_return_path_audit] FAIL: missing_file:docs/ops/delivery_formal_entry_page_review_v2.md")
        return 2

    text = path.read_text(encoding="utf-8")
    checks = [
        "## Delivery Decision",
        "- 当前建议：`GO`",
        "## Scope Note",
        "menu_id=299 项目指标",
        "in_first_delivery_scope = false",
        "de-scope reason: `return_path_gap`",
        "| 299 | 项目指标 | ✅ | ✅ | ✅ | ❌ | ✅ | ⚠️ |",
    ]

    errors: list[str] = []
    for token in checks:
        if token not in text:
            errors.append(f"missing_token:{token}")

    if errors:
        for item in errors:
            print(f"[formal_entry_return_path_audit] FAIL: {item}")
        return 2

    print("[formal_entry_return_path_audit] PASS")
    print("- menu_id 299 return-path risk disposition documented: PASS")
    print("- first-delivery scope closure is explicit: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
