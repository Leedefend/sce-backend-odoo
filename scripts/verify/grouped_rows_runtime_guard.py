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
        "def _build_group_window_digest(self, window_id: str, group_summary: List[Dict[str, Any]]) -> str:",
        "def _build_group_window_identity_key(self, window_id: str, window_digest: str) -> str:",
        'GROUP_WINDOW_IDENTITY_VERSION = "v1"',
        'GROUP_WINDOW_IDENTITY_ALGO = "sha1"',
        "group_page_offsets: Optional[Dict[str, int]] = None,",
        '"group_key": group_key,',
        '"page_window": {',
        '"page_has_prev": page_offset > 0,',
        '"page_has_next": (page_offset + page_limit) < count,',
        '"window_digest": group_window_digest,',
        '"window_key": group_window_identity_key,',
        '"window_identity": group_window_identity,',
        '"version": self.GROUP_WINDOW_IDENTITY_VERSION,',
        '"algo": self.GROUP_WINDOW_IDENTITY_ALGO,',
        '"key": group_window_identity_key,',
        '"window_empty": len(group_summary) <= 0,',
        '"window_start": group_window_start,',
        '"window_end": group_window_end,',
        '"window_span": group_window_span,',
        '"prev_group_offset": prev_group_offset,',
        '"next_group_offset": next_group_offset,',
        '"has_more": group_has_more,',
        '"model": model,',
        '"group_by_field": primary_group_field or None,',
        '"group_offset": group_offset,',
        '"group_limit": group_limit,',
        '"group_count": len(group_summary),',
        '"page_size": effective_page_size,',
        '"has_group_page_offsets": bool(group_page_offsets),',
        'group_window_identity["group_total"] = int(group_total)',
        '"grouped_rows": grouped_rows,',
    ]
    for marker in api_markers:
        if marker not in api_data:
            errors.append(f"api_data missing marker: {marker}")

    action_markers = [
        ":grouped-rows=\"groupedRows\"",
        ":on-open-group=\"handleOpenGroupedRows\"",
        ":group-sample-limit=\"groupSampleLimit\"",
        ":on-group-sample-limit-change=\"handleGroupSampleLimitChange\"",
        ":group-sort=\"groupSort\"",
        ":on-group-sort-change=\"handleGroupSortChange\"",
        ":collapsed-group-keys=\"collapsedGroupKeys\"",
        ":on-group-collapsed-change=\"handleGroupCollapsedChange\"",
        ":on-group-page-change=\"handleGroupedRowsPageChange\"",
        "useActionViewGroupedRowsRuntime",
        "groupedRows,",
        "collapsedGroupKeys,",
        "handleGroupedRowsPageChange",
        "routeGroupFp: String(route.query.group_fp || '').trim()",
        "routeGroupWid: String(route.query.group_wid || '').trim()",
        "routeGroupWdg: String(route.query.group_wdg || '').trim()",
        "routeGroupWik: String(route.query.group_wik || '').trim()",
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
        "window_digest?: string;",
        "window_key?: string;",
        "version?: string;",
        "algo?: string;",
        "key?: string;",
        "window_start?: number;",
        "window_end?: number;",
        "window_span?: number;",
        "prev_group_offset?: number;",
        "next_group_offset?: number;",
        "has_more?: boolean;",
        "group_offset?: number;",
        "group_limit?: number;",
        "group_count?: number;",
        "group_total?: number;",
        "page_size?: number;",
        "has_group_page_offsets?: boolean;",
        "model?: string;",
        "group_by_field?: string | null;",
        "window_empty?: boolean;",
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
