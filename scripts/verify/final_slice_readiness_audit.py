#!/usr/bin/env python3
from __future__ import annotations

import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
OUT_JSON = ROOT / "artifacts" / "backend" / "final_slice_readiness_audit.json"

CHECKS = {
    "platform_execution_carrier": ROOT / "addons" / "smart_core" / "orchestration" / "project_execution_scene_orchestrator.py",
    "platform_dashboard_carrier": ROOT / "addons" / "smart_core" / "orchestration" / "project_dashboard_scene_orchestrator.py",
    "platform_dashboard_contract": ROOT / "addons" / "smart_core" / "orchestration" / "project_dashboard_contract_orchestrator.py",
    "platform_plan_carrier": ROOT / "addons" / "smart_core" / "orchestration" / "project_plan_bootstrap_scene_orchestrator.py",
}
FRONTEND_FILES = [
    ROOT / "frontend" / "apps" / "web" / "src" / "views" / "SceneView.vue",
    ROOT / "frontend" / "apps" / "web" / "src" / "views" / "ProjectManagementDashboardView.vue",
]
FORBIDDEN_TEXT = {
    "frontend/apps/web/src/views/SceneView.vue": [
        "fallbackSceneFromSceneReady",
    ],
    "frontend/apps/web/src/views/ProjectManagementDashboardView.vue": [
        "project.dashboard.enter",
    ],
    "addons/smart_construction_core/services/project_dashboard_service.py": [
        "def build(self, project_id=None, context=None):",
    ],
}


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def main() -> int:
    findings: list[dict] = []
    for key, path in CHECKS.items():
        if path.exists():
            continue
        findings.append({"rule": key, "path": str(path.relative_to(ROOT)), "message": "required platform artifact missing"})

    for rel, patterns in FORBIDDEN_TEXT.items():
        text = (ROOT / rel).read_text(encoding="utf-8")
        for pattern in patterns:
            if pattern in text:
                findings.append({"rule": "forbidden_text", "path": rel, "message": f"forbidden token remains: {pattern}"})

    report = {
        "status": "READY_FOR_SLICE" if not findings else "BLOCKED",
        "finding_count": len(findings),
        "findings": findings,
    }
    _write_json(OUT_JSON, report)
    if findings:
        print("[final_slice_readiness_audit] BLOCKED")
        for item in findings[:20]:
            print(f" - {item['path']} {item['message']}")
        return 1
    print("[final_slice_readiness_audit] READY_FOR_SLICE")
    return 0


if __name__ == "__main__":
    sys.exit(main())
