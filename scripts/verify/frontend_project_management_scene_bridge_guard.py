#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
ROUTER = ROOT / "frontend/apps/web/src/router/index.ts"
PM_VIEW = ROOT / "frontend/apps/web/src/views/ProjectManagementDashboardView.vue"
MY_WORK_VIEW = ROOT / "frontend/apps/web/src/views/MyWorkView.vue"
RELEASE_ENTRY_VIEW = ROOT / "frontend/apps/web/src/views/ReleaseProductEntryView.vue"


def _must(text: str, token: str, label: str, errors: list[str]) -> None:
    if token not in text:
        errors.append(f"{label}: missing `{token}`")


def main() -> int:
    errors: list[str] = []
    router_text = ROUTER.read_text(encoding="utf-8", errors="ignore")
    pm_text = PM_VIEW.read_text(encoding="utf-8", errors="ignore") if PM_VIEW.exists() else ""
    my_work_text = MY_WORK_VIEW.read_text(encoding="utf-8", errors="ignore") if MY_WORK_VIEW.exists() else ""
    release_entry_text = RELEASE_ENTRY_VIEW.read_text(encoding="utf-8", errors="ignore") if RELEASE_ENTRY_VIEW.exists() else ""

    _must(router_text, "ProjectManagementDashboardView", "router", errors)
    _must(router_text, "path: '/pm/dashboard'", "router", errors)
    _must(router_text, "path: '/s/project.management'", "router", errors)

    if not PM_VIEW.exists():
        errors.append("missing frontend/apps/web/src/views/ProjectManagementDashboardView.vue")
    else:
        _must(pm_text, "const currentProjectContext = computed", "ProjectManagementDashboardView", errors)
        _must(pm_text, "entry.value?.project_context", "ProjectManagementDashboardView", errors)
        _must(pm_text, "loadEntry(currentEntryIntent(), { project_context: currentProjectContext.value })", "ProjectManagementDashboardView", errors)
        _must(pm_text, "const currentSceneKey = ref('project.dashboard')", "ProjectManagementDashboardView", errors)

    if not MY_WORK_VIEW.exists():
        errors.append("missing frontend/apps/web/src/views/MyWorkView.vue")
    else:
        _must(my_work_text, "router.push({ path: '/s/project.management' })", "MyWorkView", errors)

    if not RELEASE_ENTRY_VIEW.exists():
        errors.append("missing frontend/apps/web/src/views/ReleaseProductEntryView.vue")
    else:
        _must(release_entry_text, "path: '/s/project.management'", "ReleaseProductEntryView", errors)

    if errors:
        print("[frontend_project_management_scene_bridge_guard] FAIL")
        for line in errors:
            print(line)
        return 1

    print("[frontend_project_management_scene_bridge_guard] PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
