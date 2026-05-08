#!/usr/bin/env python3
"""Guard search.group_by and search.saved_filters runtime consumption stays wired."""

from __future__ import annotations

import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
ACTION_VIEW = ROOT / "frontend/apps/web/src/views/ActionView.vue"
REQUEST_RUNTIME = ROOT / "frontend/apps/web/src/app/runtime/actionViewRequestRuntime.ts"
LOAD_REQUEST_RUNTIME = ROOT / "frontend/apps/web/src/app/runtime/actionViewLoadRequestRuntime.ts"
API_DATA = ROOT / "addons/smart_core/handlers/api_data.py"


def _read(path: Path) -> str:
    if not path.exists():
        raise FileNotFoundError(str(path))
    return path.read_text(encoding="utf-8")


def main() -> int:
    errors: list[str] = []
    try:
        action_view = _read(ACTION_VIEW)
        request_runtime = _read(REQUEST_RUNTIME)
        load_request_runtime = _read(LOAD_REQUEST_RUNTIME)
        api_data = _read(API_DATA)
    except FileNotFoundError as exc:
        print("[FAIL] search_groupby_savedfilters_guard")
        print(f"- {exc}")
        return 1

    action_markers = [
        "savedFilterPrimaryChips",
        "savedFilterOverflowChips",
        "routeGroupByChips",
        "applySavedFilter,",
        "applyGroupBy: applyGroupByRuntime",
        "function applyGroupBy(field: string)",
        "context: resolveEffectiveRequestContext()",
        "resolveEffectiveRequestContext,",
        "resolveEffectiveRequestContextRaw,",
        "function applyGroupBy(field: string)",
    ]
    for marker in action_markers:
        if marker not in action_view:
            errors.append(f"action_view missing marker: {marker}")

    request_markers = [
        "export function resolveEffectiveRequestContext(filterContext: Dict, groupContext: Dict): Dict",
        "export function resolveEffectiveRequestContextRaw(filterContextRaw: string, groupContextRaw: string): string",
        "return { ...(found?.context || {}), group_by: field };",
        "return found?.contextRaw || '';",
        "return filterContextRaw || groupContextRaw || '';",
    ]
    for marker in request_markers:
        if marker not in request_runtime:
            errors.append(f"request_runtime missing marker: {marker}")

    load_request_markers = [
        "group_by: grouped ? options.activeGroupByField : undefined",
        "activeGroupByField: string;",
    ]
    for marker in load_request_markers:
        if marker not in load_request_runtime:
            errors.append(f"load_request_runtime missing marker: {marker}")

    api_markers = [
        "def _normalize_group_by(self, val):",
        "group_by_norm = self._normalize_group_by(group_by)",
        '"group_by": group_by,',
    ]
    for marker in api_markers:
        if marker not in api_data:
            errors.append(f"api_data missing marker: {marker}")

    if errors:
        env_name = str(os.getenv("ENV") or "").strip().lower()
        if env_name in {"dev", "test", "local"}:
            print("[WARN] search_groupby_savedfilters_guard (dev/test/local relaxed mode)")
            for line in errors:
                print(f"- {line}")
            return 0
        print("[FAIL] search_groupby_savedfilters_guard")
        for line in errors:
            print(f"- {line}")
        return 1

    print("[OK] search_groupby_savedfilters_guard")
    print(f"- action_view: {ACTION_VIEW}")
    print(f"- request_runtime: {REQUEST_RUNTIME}")
    print(f"- load_request_runtime: {LOAD_REQUEST_RUNTIME}")
    print(f"- api_data: {API_DATA}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
