#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def main() -> int:
    status_panel = ROOT / "frontend" / "apps" / "web" / "src" / "components" / "StatusPanel.vue"
    list_page = ROOT / "frontend" / "apps" / "web" / "src" / "pages" / "ListPage.vue"
    kanban_page = ROOT / "frontend" / "apps" / "web" / "src" / "pages" / "KanbanPage.vue"
    form_page = ROOT / "frontend" / "apps" / "web" / "src" / "pages" / "ContractFormPage.vue"

    checks = [
        (status_panel, "const retryButtonText = computed(() => String(props.retryLabel || '').trim() || '重试');"),
        (status_panel, "const compactTraceLine = computed(() => {"),
        (status_panel, "错误码："),
        (list_page, "retry-label=\"重新加载\""),
        (kanban_page, "retry-label=\"重新加载\""),
        (form_page, "retry-label=\"重新加载\""),
        (form_page, "页面加载失败，请稍后重试"),
    ]

    errors: list[str] = []
    for file_path, token in checks:
        if not file_path.exists():
            errors.append(f"missing_file:{file_path}")
            continue
        if token not in read(file_path):
            errors.append(f"missing_token:{file_path}:{token}")

    if errors:
        for item in errors:
            print(f"[formal_entry_feedback_refinement_audit] FAIL: {item}")
        return 2

    print("[formal_entry_feedback_refinement_audit] PASS")
    print("- formal entry feedback copy convergence: PASS")
    print("- retry/trace observability convergence: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
