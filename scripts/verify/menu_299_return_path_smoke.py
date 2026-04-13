#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def main() -> int:
    action_view = ROOT / "frontend" / "apps" / "web" / "src" / "views" / "ActionView.vue"
    header_runtime = ROOT / "frontend" / "apps" / "web" / "src" / "app" / "action_runtime" / "useActionViewHeaderRuntime.ts"
    review_doc = ROOT / "docs" / "ops" / "delivery_formal_entry_page_review_v2.md"

    checks = [
        (action_view, "key: 'open_workbench'"),
        (action_view, "label: '返回工作台'"),
        (header_runtime, "if (key === 'open_workbench' || key === 'open_landing')"),
        (header_runtime, "openFocusAction('/workbench');"),
        (review_doc, "| 299 | 项目指标 | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |"),
        (review_doc, "- 当前建议：`GO`"),
    ]

    errors: list[str] = []
    for path, token in checks:
        if not path.exists():
            errors.append(f"missing_file:{path}")
            continue
        text = path.read_text(encoding="utf-8")
        if token not in text:
            errors.append(f"missing_token:{path}:{token}")

    if errors:
        for item in errors:
            print(f"[menu_299_return_path_smoke] FAIL: {item}")
        return 2

    print("[menu_299_return_path_smoke] PASS")
    print("- menu 299 return-path fallback wiring: PASS")
    print("- delivery review closure updated: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
