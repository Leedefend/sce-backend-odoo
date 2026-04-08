#!/usr/bin/env python3
"""Guard search.group_by and search.saved_filters runtime consumption stays wired."""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
ACTION_VIEW = ROOT / "frontend/apps/web/src/views/ActionView.vue"
ACTION_RUNTIME_FILTER_COMPUTED = (
    ROOT / "frontend/apps/web/src/app/action_runtime/useActionViewFilterComputedRuntime.ts"
)
ACTION_RUNTIME_REQUEST_CONTEXT = (
    ROOT / "frontend/apps/web/src/app/action_runtime/useActionViewRequestContextRuntime.ts"
)
ACTION_REQUEST_RUNTIME = ROOT / "frontend/apps/web/src/app/runtime/actionViewRequestRuntime.ts"
ACTION_RUNTIME_FILTER_GROUP = (
    ROOT / "frontend/apps/web/src/app/action_runtime/useActionViewFilterGroupRuntime.ts"
)
API_DATA = ROOT / "addons/smart_core/handlers/api_data.py"


def _read(path: Path) -> str:
    if not path.exists():
        raise FileNotFoundError(str(path))
    return path.read_text(encoding="utf-8")


def main() -> int:
    errors: list[str] = []
    try:
        action_view = _read(ACTION_VIEW)
        action_runtime_filter_computed = _read(ACTION_RUNTIME_FILTER_COMPUTED)
        action_runtime_request_context = _read(ACTION_RUNTIME_REQUEST_CONTEXT)
        action_request_runtime = _read(ACTION_REQUEST_RUNTIME)
        action_runtime_filter_group = _read(ACTION_RUNTIME_FILTER_GROUP)
        api_data = _read(API_DATA)
    except FileNotFoundError as exc:
        print("[FAIL] search_groupby_savedfilters_guard")
        print(f"- {exc}")
        return 1

    frontend_marker_specs = [
        (
            "action_view",
            ACTION_VIEW,
            action_view,
            [
                "useActionViewFilterComputedRuntime",
                "useActionViewRequestContextRuntime",
                "useActionViewFilterGroupRuntime",
            ],
        ),
        (
            "action_runtime_filter_computed",
            ACTION_RUNTIME_FILTER_COMPUTED,
            action_runtime_filter_computed,
            ["search?.saved_filters", "search?.group_by"],
        ),
        (
            "action_runtime_request_context",
            ACTION_RUNTIME_REQUEST_CONTEXT,
            action_runtime_request_context,
            [
                "function resolveEffectiveRequestContext()",
                "function resolveEffectiveRequestContextRaw()",
            ],
        ),
        (
            "action_request_runtime",
            ACTION_REQUEST_RUNTIME,
            action_request_runtime,
            ["group_by: field"],
        ),
        (
            "action_runtime_filter_group",
            ACTION_RUNTIME_FILTER_GROUP,
            action_runtime_filter_group,
            ["function applySavedFilter(key: string)", "function applyGroupBy(field: string)"],
        ),
    ]
    for label, _, content, markers in frontend_marker_specs:
        for marker in markers:
            if marker not in content:
                errors.append(f"{label} missing marker: {marker}")

    api_markers = [
        "def _normalize_group_by(self, val):",
        'group_by = self._normalize_group_by(self._dig(p, "group_by"))',
        '"group_by": group_by,',
    ]
    for marker in api_markers:
        if marker not in api_data:
            errors.append(f"api_data missing marker: {marker}")

    if errors:
        print("[FAIL] search_groupby_savedfilters_guard")
        for line in errors:
            print(f"- {line}")
        return 1

    print("[OK] search_groupby_savedfilters_guard")
    print(f"- action_view: {ACTION_VIEW}")
    print(f"- action_runtime_filter_computed: {ACTION_RUNTIME_FILTER_COMPUTED}")
    print(f"- action_runtime_request_context: {ACTION_RUNTIME_REQUEST_CONTEXT}")
    print(f"- action_request_runtime: {ACTION_REQUEST_RUNTIME}")
    print(f"- action_runtime_filter_group: {ACTION_RUNTIME_FILTER_GROUP}")
    print(f"- api_data: {API_DATA}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
