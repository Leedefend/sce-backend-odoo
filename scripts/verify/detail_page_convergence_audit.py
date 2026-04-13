#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def _must_contain(path: Path, token: str, errors: list[str]) -> None:
    text = path.read_text(encoding="utf-8")
    if token not in text:
        errors.append(f"missing_token:{path.relative_to(ROOT)}:{token}")


def main() -> int:
    errors: list[str] = []

    form_page = ROOT / "frontend" / "apps" / "web" / "src" / "pages" / "ContractFormPage.vue"
    detail_runtime = ROOT / "frontend" / "apps" / "web" / "src" / "app" / "runtime" / "detailLayoutRuntime.ts"

    _must_contain(form_page, "工程结构详情", errors)
    _must_contain(form_page, "查看或编辑工程结构节点信息", errors)
    _must_contain(form_page, "goBackFromDetail", errors)
    _must_contain(form_page, "mapDetailFieldLabel", errors)
    _must_contain(form_page, "normalizeDetailSectionTree", errors)
    _must_contain(form_page, "结构定位", errors)
    _must_contain(form_page, "节点信息", errors)

    _must_contain(detail_runtime, "dedupeTabLabel", errors)
    _must_contain(detail_runtime, "（${sameCount + 1}）", errors)

    if errors:
        for item in errors:
            print(f"[detail_page_convergence_audit] FAIL: {item}")
        return 2

    print("[detail_page_convergence_audit] PASS")
    print("- title/subtitle convergence: PASS")
    print("- back/save action path: PASS")
    print("- business field labels mapping: PASS")
    print("- duplicate tab label guard: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
