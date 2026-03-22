#!/usr/bin/env python3
from __future__ import annotations

import json
import re
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
OUT_JSON = ROOT / "artifacts" / "backend" / "orchestration_platform_guard.json"

PLATFORM_EXECUTION = ROOT / "addons" / "smart_core" / "orchestration" / "project_execution_scene_orchestrator.py"
LEGACY_DIR = ROOT / "addons" / "smart_construction_core" / "orchestration"
FORBIDDEN_EXECUTION = LEGACY_DIR / "project_execution_scene_orchestrator.py"
HANDLER_FILES = [
    ROOT / "addons" / "smart_construction_core" / "handlers" / "project_execution_enter.py",
    ROOT / "addons" / "smart_construction_core" / "handlers" / "project_execution_block_fetch.py",
]
FRONTEND_FILES = [
    ROOT / "frontend" / "apps" / "web" / "src" / "layouts" / "AppShell.vue",
    ROOT / "frontend" / "apps" / "web" / "src" / "app" / "sceneMutationRuntime.ts",
]
LEGACY_MARKER = 'LEGACY_ORCHESTRATION_MODE = "industry_local"'
FORBIDDEN_FRONTEND_PATTERNS = {
    "frontend/apps/web/src/layouts/AppShell.vue": [
        "sceneKey === 'projects.intake'",
    ],
    "frontend/apps/web/src/app/sceneMutationRuntime.ts": [
        "if (model === 'finance.payment.request' || model === 'payment.request')",
        "if (model === 'project.risk.action')",
    ],
}
EXPECTED_HANDLER_IMPORT = "from odoo.addons.smart_core.orchestration.project_execution_scene_orchestrator import ("


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

    if not PLATFORM_EXECUTION.exists():
        findings.append(
            {
                "rule": "platform_execution_carrier_required",
                "severity": "high",
                "path": str(PLATFORM_EXECUTION.relative_to(ROOT)),
                "message": "smart_core execution orchestration carrier is missing",
            }
        )

    if FORBIDDEN_EXECUTION.exists():
        findings.append(
            {
                "rule": "industry_execution_carrier_forbidden",
                "severity": "high",
                "path": str(FORBIDDEN_EXECUTION.relative_to(ROOT)),
                "message": "execution carrier must not remain under smart_construction_core orchestration",
            }
        )

    for path in HANDLER_FILES:
        text = _read(path)
        if EXPECTED_HANDLER_IMPORT not in text:
            findings.append(
                {
                    "rule": "execution_handler_platform_import_required",
                    "severity": "high",
                    "path": str(path.relative_to(ROOT)),
                    "message": "execution handler must import the smart_core orchestration carrier",
                }
            )

    for path in sorted(LEGACY_DIR.glob("*_scene_orchestrator.py")):
        text = _read(path)
        if path.name == "project_execution_scene_orchestrator.py":
            continue
        if LEGACY_MARKER not in text:
            findings.append(
                {
                    "rule": "legacy_orchestration_marker_required",
                    "severity": "medium",
                    "path": str(path.relative_to(ROOT)),
                    "message": "remaining industry-local orchestrator must be explicitly marked as legacy mode",
                }
            )

    for rel, patterns in FORBIDDEN_FRONTEND_PATTERNS.items():
        path = ROOT / rel
        text = _read(path)
        for pattern in patterns:
            if pattern in text:
                findings.append(
                    {
                        "rule": "frontend_business_semantics_forbidden",
                        "severity": "high",
                        "path": rel,
                        "message": f"found forbidden frontend business semantic branch `{pattern}`",
                    }
                )

    summary = {
        "finding_count": len(findings),
        "blocked": bool(findings),
        "legacy_dir": str(LEGACY_DIR.relative_to(ROOT)),
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
