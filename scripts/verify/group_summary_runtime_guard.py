#!/usr/bin/env python3
"""Guard group_summary backend/frontend runtime wiring remains active."""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
API_DATA = ROOT / "addons/smart_core/handlers/api_data.py"
ACTION_VIEW = ROOT / "frontend/apps/web/src/views/ActionView.vue"
SUMMARY_BAR = ROOT / "frontend/apps/web/src/components/GroupSummaryBar.vue"


def _read(path: Path) -> str:
    if not path.exists():
        raise FileNotFoundError(str(path))
    return path.read_text(encoding="utf-8")


def main() -> int:
    errors: list[str] = []
    try:
        api_data = _read(API_DATA)
        action_view = _read(ACTION_VIEW)
        summary_bar = _read(SUMMARY_BAR)
    except FileNotFoundError as exc:
        print("[FAIL] group_summary_runtime_guard")
        print(f"- {exc}")
        return 1

    api_markers = [
        "def _build_group_summary(self, env_model, domain, group_by, limit: int = 20):",
        '"group_summary": group_summary,',
    ]
    for marker in api_markers:
        if marker not in api_data:
            errors.append(f"api_data missing marker: {marker}")

    action_markers = [
        "GroupSummaryBar",
        "groupSummaryItems.value = (Array.isArray(result.data?.group_summary)",
        "function handleGroupSummaryPick(item: GroupSummaryItem)",
        "function clearGroupSummaryDrilldown()",
    ]
    for marker in action_markers:
        if marker not in action_view:
            errors.append(f"action_view missing marker: {marker}")

    summary_bar_markers = [
        "class=\"group-summary\"",
        "clear-btn",
        ":class=\"{ active: activeKey === item.key }\"",
    ]
    for marker in summary_bar_markers:
        if marker not in summary_bar:
            errors.append(f"group_summary_bar missing marker: {marker}")

    if errors:
        print("[FAIL] group_summary_runtime_guard")
        for line in errors:
            print(f"- {line}")
        return 1

    print("[OK] group_summary_runtime_guard")
    print(f"- api_data: {API_DATA}")
    print(f"- action_view: {ACTION_VIEW}")
    print(f"- group_summary_bar: {SUMMARY_BAR}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
