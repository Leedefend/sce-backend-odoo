#!/usr/bin/env python3
from __future__ import annotations

import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
OUT_JSON = ROOT / "artifacts" / "backend" / "orchestration_platform_guard.json"

PLATFORM_ORCHESTRATORS = {
    "project.execution": ROOT / "addons" / "smart_core" / "orchestration" / "project_execution_scene_orchestrator.py",
    "project.dashboard": ROOT / "addons" / "smart_core" / "orchestration" / "project_dashboard_scene_orchestrator.py",
    "project.dashboard.contract": ROOT / "addons" / "smart_core" / "orchestration" / "project_dashboard_contract_orchestrator.py",
    "project.plan_bootstrap": ROOT / "addons" / "smart_core" / "orchestration" / "project_plan_bootstrap_scene_orchestrator.py",
}
LEGACY_DIR = ROOT / "addons" / "smart_construction_core" / "orchestration"
FORBIDDEN_INDUSTRY_ORCHESTRATORS = {
    "project.execution": LEGACY_DIR / "project_execution_scene_orchestrator.py",
    "project.dashboard": LEGACY_DIR / "project_dashboard_scene_orchestrator.py",
    "project.plan_bootstrap": LEGACY_DIR / "project_plan_bootstrap_scene_orchestrator.py",
}
HANDLER_IMPORT_RULES = {
    "addons/smart_construction_core/handlers/project_execution_enter.py": "from odoo.addons.smart_core.orchestration.project_execution_scene_orchestrator import (",
    "addons/smart_construction_core/handlers/project_execution_block_fetch.py": "from odoo.addons.smart_core.orchestration.project_execution_scene_orchestrator import (",
    "addons/smart_construction_core/handlers/project_dashboard.py": "from odoo.addons.smart_core.orchestration.project_dashboard_contract_orchestrator import (",
    "addons/smart_construction_core/handlers/project_dashboard_enter.py": "from odoo.addons.smart_core.orchestration.project_dashboard_scene_orchestrator import (",
    "addons/smart_construction_core/handlers/project_dashboard_block_fetch.py": "from odoo.addons.smart_core.orchestration.project_dashboard_scene_orchestrator import (",
    "addons/smart_construction_core/handlers/project_plan_bootstrap_enter.py": "from odoo.addons.smart_core.orchestration.project_plan_bootstrap_scene_orchestrator import (",
    "addons/smart_construction_core/handlers/project_plan_bootstrap_block_fetch.py": "from odoo.addons.smart_core.orchestration.project_plan_bootstrap_scene_orchestrator import (",
}
FRONTEND_FILES = [
    ROOT / "frontend" / "apps" / "web" / "src" / "layouts" / "AppShell.vue",
    ROOT / "frontend" / "apps" / "web" / "src" / "app" / "sceneMutationRuntime.ts",
]
FORBIDDEN_FRONTEND_PATTERNS = {
    "frontend/apps/web/src/layouts/AppShell.vue": [
        "sceneKey === 'projects.intake'",
    ],
    "frontend/apps/web/src/app/sceneMutationRuntime.ts": [
        "const LEGACY_MODEL_EXECUTE_INTENT",
        "if (model === 'finance.payment.request' || model === 'payment.request')",
        "if (model === 'project.risk.action')",
    ],
}
FORBIDDEN_SERVICE_PATTERNS = {
    "addons/smart_construction_core/services/project_dashboard_service.py": [
        "def build(self, project_id=None, context=None):",
        "build_scene_contract_from_specs",
        "dashboard_orchestration_kernel.py",
        "build_project_dashboard_scene_content",
    ],
}


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _read(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except Exception:
        return ""


def main() -> int:
    findings: list[dict] = []

    for scene_key, path in PLATFORM_ORCHESTRATORS.items():
        if path.exists():
            continue
        findings.append(
            {
                "rule": "platform_scene_carrier_required",
                "severity": "high",
                "path": str(path.relative_to(ROOT)),
                "message": f"smart_core orchestration carrier is missing for {scene_key}",
            }
        )

    for scene_key, path in FORBIDDEN_INDUSTRY_ORCHESTRATORS.items():
        if not path.exists():
            continue
        findings.append(
            {
                "rule": "industry_scene_carrier_forbidden",
                "severity": "high",
                "path": str(path.relative_to(ROOT)),
                "message": f"{scene_key} carrier must not remain under smart_construction_core orchestration",
            }
        )

    for rel, expected_import in HANDLER_IMPORT_RULES.items():
        path = ROOT / rel
        text = _read(path)
        if expected_import in text:
            continue
        findings.append(
            {
                "rule": "scene_handler_platform_import_required",
                "severity": "high",
                "path": rel,
                "message": "scene handler must import the smart_core orchestration carrier",
            }
        )

    for rel, patterns in FORBIDDEN_FRONTEND_PATTERNS.items():
        path = ROOT / rel
        text = _read(path)
        for pattern in patterns:
            if pattern not in text:
                continue
            findings.append(
                {
                    "rule": "frontend_business_semantics_forbidden",
                    "severity": "high",
                    "path": rel,
                    "message": f"found forbidden frontend business semantic branch `{pattern}`",
                }
            )

    for rel, patterns in FORBIDDEN_SERVICE_PATTERNS.items():
        path = ROOT / rel
        text = _read(path)
        for pattern in patterns:
            if pattern not in text:
                continue
            findings.append(
                {
                    "rule": "domain_service_dashboard_contract_assembly_forbidden",
                    "severity": "high",
                    "path": rel,
                    "message": f"found forbidden dashboard contract assembly token `{pattern}`",
                }
            )

    summary = {
        "finding_count": len(findings),
        "blocked": bool(findings),
        "platform_orchestrator_count": len(PLATFORM_ORCHESTRATORS),
    }
    report = {"status": "BLOCKED" if findings else "PASS", "summary": summary, "findings": findings}
    _write_json(OUT_JSON, report)
    if findings:
        print("[orchestration_platform_guard] BLOCKED")
        for item in findings[:12]:
            print(f" - {item['path']} {item['rule']}: {item['message']}")
        return 1

    print("[orchestration_platform_guard] PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
