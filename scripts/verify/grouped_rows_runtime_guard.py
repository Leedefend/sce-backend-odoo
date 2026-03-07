#!/usr/bin/env python3
"""Guard grouped_rows backend/frontend runtime wiring remains active."""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
API_DATA = ROOT / "addons/smart_core/handlers/api_data.py"
ACTION_VIEW = ROOT / "frontend/apps/web/src/views/ActionView.vue"
LIST_PAGE = ROOT / "frontend/apps/web/src/pages/ListPage.vue"
SCHEMA = ROOT / "frontend/packages/schema/src/index.ts"


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
        schema = _read(SCHEMA)
    except FileNotFoundError as exc:
        print("[FAIL] grouped_rows_runtime_guard")
        print(f"- {exc}")
        return 1

    api_markers = [
        "def _build_grouped_rows(",
        "group_page_offsets: Optional[Dict[str, int]] = None,",
        '"group_key": group_key,',
        '"page_window": {',
        '"page_has_prev": page_offset > 0,',
        '"page_has_next": (page_offset + page_limit) < count,',
        '"grouped_rows": grouped_rows,',
    ]
    for marker in api_markers:
        if marker not in api_data:
            errors.append(f"api_data missing marker: {marker}")

    action_markers = [
        "type GroupedRow = {",
        "const groupedRows = ref<GroupedRow[]>([]);",
        "const groupSampleLimit = ref(3);",
        "groupedRows.value = (Array.isArray(result.data?.grouped_rows) ? result.data?.grouped_rows : [])",
        "key: String(item.group_key || fallbackKey),",
        "pageWindow?: { start?: number; end?: number };",
        "pageWindow: typeof item.page_window === 'object' && item.page_window !== null",
        "pageHasPrev: typeof item.page_has_prev === 'boolean' ? Boolean(item.page_has_prev) : undefined,",
        "pageHasNext: typeof item.page_has_next === 'boolean' ? Boolean(item.page_has_next) : undefined,",
        "group_sample_limit: groupSampleLimit.value,",
        ":grouped-rows=\"groupedRows\"",
        ":on-open-group=\"handleOpenGroupedRows\"",
        ":group-sample-limit=\"groupSampleLimit\"",
        ":on-group-sample-limit-change=\"handleGroupSampleLimitChange\"",
        ":group-sort=\"groupSort\"",
        ":on-group-sort-change=\"handleGroupSortChange\"",
        ":collapsed-group-keys=\"collapsedGroupKeys\"",
        ":on-group-collapsed-change=\"handleGroupCollapsedChange\"",
        ":on-group-page-change=\"handleGroupedRowsPageChange\"",
        "const groupPageOffsets = ref<Record<string, number>>({});",
        "const groupPageRaw = String(route.query.group_page || '').trim();",
        "const groupFingerprintRaw = String(route.query.group_fp || '').trim();",
        "group_page: groupPage || undefined,",
        "group_fp: activeGroupByField.value && groupQueryFingerprint.value ? groupQueryFingerprint.value : undefined,",
        "function handleGroupedRowsPageChange(group: {",
        "async function hydrateGroupedRowsByOffset() {",
        "void hydrateGroupedRowsByOffset();",
        "function normalizeGroupedRouteState() {",
        "normalizeGroupedRouteState();",
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
        "onGroupSampleLimitSelectChange",
        "props.groupSort",
        "props.collapsedGroupKeys",
        "props.onGroupPageChange",
        "pageWindow?: { start?: number; end?: number };",
        "pageHasPrev?: boolean;",
        "pageHasNext?: boolean;",
        "const backendWindow = (group as { pageWindow?: { start?: unknown; end?: unknown } }).pageWindow;",
        "typeof (group as { pageHasPrev?: unknown }).pageHasPrev === 'boolean'",
        "typeof (group as { pageHasNext?: unknown }).pageHasNext === 'boolean'",
        "group-page-btn",
        "group-page-input",
        "onGroupJumpInputChange(",
        "groupPageInfoText(",
        "jumpGroupPage(",
        "跳转",
        "上一页",
        "下一页",
        "expandAllGroups()",
        "collapseAllGroups()",
        "全部展开",
        "全部收起",
    ]
    for marker in list_markers:
        if marker not in list_page:
            errors.append(f"list_page missing marker: {marker}")

    schema_markers = [
        "export interface ApiDataListResult {",
        "grouped_rows?: Array<{",
        "group_key?: string;",
        "page_offset?: number;",
        "page_limit?: number;",
        "page_window?: {",
        "page_has_prev?: boolean;",
        "page_has_next?: boolean;",
        "export interface ApiDataListRequest {",
        "group_page_offsets?: Record<string, number>;",
    ]
    for marker in schema_markers:
        if marker not in schema:
            errors.append(f"schema missing marker: {marker}")

    if errors:
        print("[FAIL] grouped_rows_runtime_guard")
        for line in errors:
            print(f"- {line}")
        return 1

    print("[OK] grouped_rows_runtime_guard")
    print(f"- api_data: {API_DATA}")
    print(f"- action_view: {ACTION_VIEW}")
    print(f"- list_page: {LIST_PAGE}")
    print(f"- schema: {SCHEMA}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
