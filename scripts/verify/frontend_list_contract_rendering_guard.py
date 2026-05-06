#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
LIST_PAGE = ROOT / "frontend" / "apps" / "web" / "src" / "pages" / "ListPage.vue"
SHAPE_RUNTIME = (
    ROOT
    / "frontend"
    / "apps"
    / "web"
    / "src"
    / "app"
    / "action_runtime"
    / "useActionViewContractShapeRuntime.ts"
)


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _extract_function(source: str, name: str) -> str:
    marker = f"function {name}("
    start = source.find(marker)
    if start < 0:
        raise AssertionError(f"missing function {name}")
    next_function = source.find("\nfunction ", start + len(marker))
    if next_function < 0:
        return source[start:]
    return source[start:next_function]


def main() -> int:
    list_page = _read(LIST_PAGE)
    shape_runtime = _read(SHAPE_RUNTIME)
    errors: list[str] = []

    footer_cell = _extract_function(list_page, "footerCellText")
    group_footer_cell = _extract_function(list_page, "groupFooterCellText")
    for name, block in (
        ("footerCellText", footer_cell),
        ("groupFooterCellText", group_footer_cell),
    ):
        if "columnLabel(" in block or "`${label}" in block or "}：" in block:
            errors.append(f"{name} must render numeric-only footer cells; row header owns the label")

    if "sortable?: boolean" not in shape_runtime:
        errors.append("contract column options must expose sortable?: boolean")
    if "sortableRaw === false ? false : undefined" not in shape_runtime:
        errors.append("columns_schema.sortable=false must be preserved from contract to column options")
    if "function isColumnSortable" not in list_page:
        errors.append("ListPage must centralize column sortable resolution")
    if "if (!isColumnSortable(col)) return;" not in list_page:
        errors.append("ListPage must not emit sort requests for non-sortable columns")
    if "sort_column_disabled" not in list_page:
        errors.append("ListPage must expose disabled sort affordance text")
    column_width_style = _extract_function(list_page, "columnWidthStyle")
    if "Math.min(width" in column_width_style or "maxTextWidth" in column_width_style:
        errors.append("explicit column widths must render as saved; do not clamp name/text columns after resize")

    if errors:
        print("[frontend_list_contract_rendering_guard] FAIL")
        for item in errors:
            print(f" - {item}")
        return 1
    print("[frontend_list_contract_rendering_guard] PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
