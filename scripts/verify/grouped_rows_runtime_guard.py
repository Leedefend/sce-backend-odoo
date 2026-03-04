#!/usr/bin/env python3
"""Guard grouped_rows backend/frontend runtime wiring remains active."""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
API_DATA = ROOT / "addons/smart_core/handlers/api_data.py"
ACTION_VIEW = ROOT / "frontend/apps/web/src/views/ActionView.vue"
LIST_PAGE = ROOT / "frontend/apps/web/src/pages/ListPage.vue"


def _read(path: Path) -> str:
    if not path.exists():
        raise FileNotFoundError(str(path))
    return path.read_text(encoding="utf-8")


def main() -> int:
    errors: list[str] = []
    try:
        api_data = _read(API_DATA)
        action_view = _read(ACTION_VIEW)
        list_page = _read(LIST_PAGE)
    except FileNotFoundError as exc:
        print("[FAIL] grouped_rows_runtime_guard")
        print(f"- {exc}")
        return 1

    api_markers = [
        "def _build_grouped_rows(self, env_model, domain, group_by, fields_safe: List[str], limit: int = 20, sample_limit: int = 3):",
        '"grouped_rows": grouped_rows,',
    ]
    for marker in api_markers:
        if marker not in api_data:
            errors.append(f"api_data missing marker: {marker}")

    action_markers = [
        "const groupedRows = ref<Array<{ key: string; label: string; count: number; sampleRows: Array<Record<string, unknown>>; domain?: unknown[] }>>([]);",
        "groupedRows.value = (Array.isArray(result.data?.grouped_rows) ? result.data?.grouped_rows : [])",
        ":grouped-rows=\"groupedRows\"",
        ":on-open-group=\"handleOpenGroupedRows\"",
    ]
    for marker in action_markers:
        if marker not in action_view:
            errors.append(f"action_view missing marker: {marker}")

    list_markers = [
        "v-if=\"groupedRows.length\" class=\"grouped-table\"",
        "v-for=\"group in sortedGroupedRows\"",
        "sampleRows",
        "toggleGroupCollapsed(",
        "grouped-sort-btn",
    ]
    for marker in list_markers:
        if marker not in list_page:
            errors.append(f"list_page missing marker: {marker}")

    if errors:
        print("[FAIL] grouped_rows_runtime_guard")
        for line in errors:
            print(f"- {line}")
        return 1

    print("[OK] grouped_rows_runtime_guard")
    print(f"- api_data: {API_DATA}")
    print(f"- action_view: {ACTION_VIEW}")
    print(f"- list_page: {LIST_PAGE}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
