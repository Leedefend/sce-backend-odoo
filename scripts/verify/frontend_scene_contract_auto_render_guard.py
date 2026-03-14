#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SCENE_VIEW = ROOT / "frontend/apps/web/src/views/SceneView.vue"
ROUTER = ROOT / "frontend/apps/web/src/router/index.ts"

REPORT_JSON = ROOT / "artifacts/backend/frontend_scene_contract_auto_render_guard_report.json"
REPORT_MD = ROOT / "docs/ops/audit/frontend_scene_contract_auto_render_guard_report.md"


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="ignore") if path.is_file() else ""


def main() -> int:
    errors: list[str] = []

    scene_text = _read(SCENE_VIEW)
    router_text = _read(ROUTER)
    if not scene_text:
        errors.append("missing file: frontend/apps/web/src/views/SceneView.vue")
    if not router_text:
        errors.append("missing file: frontend/apps/web/src/router/index.ts")

    scene_required_tokens = [
        "const pageContract = usePageContract('scene');",
        "<ContractFormPage v-else-if=\"status === 'idle' && embeddedRecordActionId > 0\" />",
        "<ActionView v-else-if=\"status === 'idle' && embeddedActionId > 0\" />",
        "const embeddedActionId = ref(0);",
        "const embeddedRecordActionId = ref(0);",
    ]
    scene_forbidden_tokens = [
        "import MyWorkView",
        "import ProjectsIntakeView",
        "import ProjectManagementDashboardView",
        "embeddedMyWorkWorkspace",
        "embeddedProjectsIntake",
        "embeddedWorkspaceDashboard",
        "<MyWorkView",
        "<ProjectsIntakeView",
        "<ProjectManagementDashboardView",
    ]

    router_required_tokens = [
        "{ path: '/s/:sceneKey', name: 'scene', component: SceneView, meta: { layout: 'shell' } }",
        "{ path: '/my-work', name: 'my-work', redirect: '/s/my_work.workspace', meta: { layout: 'shell' } }",
        "{ path: '/pm/dashboard', name: 'project-management-dashboard', redirect: '/s/project.management', meta: { layout: 'shell' } }",
    ]

    for token in scene_required_tokens:
        if token not in scene_text:
            errors.append(f"SceneView.vue missing token: {token}")
    for token in scene_forbidden_tokens:
        if token in scene_text:
            errors.append(f"SceneView.vue forbidden token present: {token}")

    for token in router_required_tokens:
        if token not in router_text:
            errors.append(f"router/index.ts missing token: {token}")

    REPORT_JSON.parent.mkdir(parents=True, exist_ok=True)
    REPORT_MD.parent.mkdir(parents=True, exist_ok=True)

    payload = {
        "ok": not errors,
        "check": "verify.frontend.scene_contract_auto_render.guard",
        "errors": errors,
        "files": [
            "frontend/apps/web/src/views/SceneView.vue",
            "frontend/apps/web/src/router/index.ts",
        ],
    }
    REPORT_JSON.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    lines = [
        "# Frontend Scene Contract Auto Render Guard Report",
        "",
        f"- ok: {str(payload['ok']).lower()}",
        f"- check: {payload['check']}",
        "- files:",
        "  - frontend/apps/web/src/views/SceneView.vue",
        "  - frontend/apps/web/src/router/index.ts",
    ]
    if errors:
        lines.append("- errors:")
        for err in errors:
            lines.append(f"  - {err}")
    else:
        lines.append("- errors: []")
    REPORT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")

    if errors:
        print("[verify.frontend.scene_contract_auto_render.guard] FAIL")
        for err in errors:
            print(f" - {err}")
        return 2
    print("[verify.frontend.scene_contract_auto_render.guard] PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

