#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def assert_contains(path: str, token: str, errors: list[str]) -> None:
    if token not in read(path):
        errors.append(f"missing_token:{path}:{token}")


def assert_not_contains(path: str, token: str, errors: list[str]) -> None:
    if token in read(path):
        errors.append(f"forbidden_token:{path}:{token}")


def main() -> int:
    errors: list[str] = []

    list_page = "frontend/apps/web/src/pages/ListPage.vue"
    form_page = "frontend/apps/web/src/pages/ContractFormPage.vue"
    kanban_page = "frontend/apps/web/src/pages/KanbanPage.vue"
    detail_runtime = "frontend/apps/web/src/app/runtime/detailLayoutRuntime.ts"
    checklist = "docs/ops/ui_page_class_convergence_checklist_v1.md"

    assert_contains(checklist, "Unified Regions (Mandatory)", errors)
    assert_contains(checklist, "ListPage", errors)
    assert_contains(checklist, "ContractFormPage", errors)
    assert_contains(checklist, "KanbanPage", errors)

    assert_contains(list_page, "<PageHeader", errors)
    assert_contains(list_page, "StatusPanel", errors)
    assert_contains(list_page, ":on-filter=\"onFilter\"", errors)

    assert_contains(form_page, "goBackFromDetail", errors)
    assert_contains(form_page, "工程结构详情", errors)
    assert_contains(form_page, "查看或编辑工程结构节点信息", errors)
    assert_contains(form_page, "mapDetailFieldLabel", errors)
    assert_contains(form_page, "normalizeDetailSectionTree", errors)

    assert_contains(kanban_page, "<PageHeader", errors)
    assert_contains(kanban_page, "StatusPanel", errors)

    assert_contains(detail_runtime, "dedupeTabLabel", errors)
    assert_not_contains(form_page, "construction.work.breakdown 详情", errors)

    if errors:
        for err in errors:
            print(f"[page_class_convergence_audit] FAIL: {err}")
        return 2

    print("[page_class_convergence_audit] PASS")
    print("- checklist baseline: PASS")
    print("- list/form/kanban region presence: PASS")
    print("- detail-page convergence hooks: PASS")
    print("- duplicate tab guard: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
