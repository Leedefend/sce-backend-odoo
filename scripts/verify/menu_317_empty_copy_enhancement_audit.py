#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def main() -> int:
    list_page = ROOT / "frontend" / "apps" / "web" / "src" / "pages" / "ListPage.vue"
    summary = ROOT / "artifacts" / "delivery" / "remediation_1710_summary.json"

    errors: list[str] = []
    if not list_page.exists():
        errors.append("missing_file:frontend/apps/web/src/pages/ListPage.vue")
    else:
        text = list_page.read_text(encoding="utf-8")
        for token in [
            "const emptyMessageText = computed(() => {",
            "if (pageTitle.includes('投标'))",
            "当前暂无投标数据。建议先点击",
            ":message=\"emptyMessageText\"",
        ]:
            if token not in text:
                errors.append(f"missing_token:ListPage:{token}")

    if not summary.exists():
        errors.append("missing_file:artifacts/delivery/remediation_1710_summary.json")

    if errors:
        for item in errors:
            print(f"[menu_317_empty_copy_enhancement_audit] FAIL: {item}")
        return 2

    print("[menu_317_empty_copy_enhancement_audit] PASS")
    print("- menu 317 empty-state copy enhancement token check: PASS")
    print("- remediation summary artifact presence: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
