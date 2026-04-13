#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def main() -> int:
    list_page = ROOT / "frontend" / "apps" / "web" / "src" / "pages" / "ListPage.vue"
    summary = ROOT / "artifacts" / "delivery" / "remediation_1709_summary.json"

    errors: list[str] = []
    if not list_page.exists():
        errors.append("missing_file:frontend/apps/web/src/pages/ListPage.vue")
    else:
        text = list_page.read_text(encoding="utf-8")
        for token in [
            "if (pageTitle.includes('预算') || pageTitle.includes('成本'))",
            "先选择一条记录查看详情；新增请点击右上角",
            "先选择一条记录查看详情，再继续预算/成本处理",
        ]:
            if token not in text:
                errors.append(f"missing_token:ListPage:{token}")

    if not summary.exists():
        errors.append("missing_file:artifacts/delivery/remediation_1709_summary.json")

    if errors:
        for item in errors:
            print(f"[menu_315_copy_convergence_audit] FAIL: {item}")
        return 2

    print("[menu_315_copy_convergence_audit] PASS")
    print("- menu 315 copy convergence token check: PASS")
    print("- remediation summary artifact presence: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
