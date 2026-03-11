#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
ROUTER = ROOT / "frontend/apps/web/src/router/index.ts"
SCENE_VIEW = ROOT / "frontend/apps/web/src/views/SceneView.vue"
WORKSPACE_CTX = ROOT / "frontend/apps/web/src/app/workspaceContext.ts"
PM_VIEW = ROOT / "frontend/apps/web/src/views/ProjectManagementDashboardView.vue"


def _must(text: str, token: str, label: str, errors: list[str]) -> None:
    if token not in text:
        errors.append(f"{label}: missing `{token}`")


def main() -> int:
    errors: list[str] = []
    router_text = ROUTER.read_text(encoding="utf-8", errors="ignore")
    scene_text = SCENE_VIEW.read_text(encoding="utf-8", errors="ignore")
    ctx_text = WORKSPACE_CTX.read_text(encoding="utf-8", errors="ignore")

    _must(router_text, "ProjectManagementDashboardView", "router", errors)
    _must(router_text, "path: '/pm/dashboard'", "router", errors)

    _must(scene_text, "sceneKey === 'project.management'", "SceneView", errors)
    _must(scene_text, "path: '/pm/dashboard'", "SceneView", errors)
    _must(scene_text, "query: workspaceContextQuery", "SceneView", errors)

    _must(ctx_text, "project_id", "workspaceContext", errors)
    _must(ctx_text, "context.project_id", "workspaceContext", errors)

    if not PM_VIEW.exists():
      errors.append("missing frontend/apps/web/src/views/ProjectManagementDashboardView.vue")

    if errors:
        print("[frontend_project_management_scene_bridge_guard] FAIL")
        for line in errors:
            print(line)
        return 1

    print("[frontend_project_management_scene_bridge_guard] PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
