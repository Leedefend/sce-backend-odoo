#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
OUT_JSON = ROOT / "artifacts" / "backend" / "product_project_creation_mainline_guard.json"
FRONTEND_BASELINE = ROOT / "frontend" / "apps" / "web" / "src" / "app" / "projectCreationBaseline.ts"
INTAKE_VIEW = ROOT / "frontend" / "apps" / "web" / "src" / "views" / "ProjectsIntakeView.vue"
FORM_PAGE = ROOT / "frontend" / "apps" / "web" / "src" / "pages" / "ContractFormPage.vue"
INITIATION_HANDLER = ROOT / "addons" / "smart_construction_core" / "handlers" / "project_initiation_enter.py"
BASELINE_DOC = ROOT / "docs" / "ops" / "product_project_creation_mainline_baseline_v1.md"


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def main() -> int:
    findings: list[str] = []

    baseline_text = _read(FRONTEND_BASELINE)
    for token in (
        "PROJECT_INTAKE_SCENE_KEY = 'projects.intake'",
        "PROJECT_INITIATION_PRODUCT_INTENT = 'project.initiation.enter'",
        "PROJECT_DASHBOARD_ENTRY_INTENT = 'project.dashboard.enter'",
        "PROJECT_INITIATION_MENU_XMLID = 'smart_construction_core.menu_sc_project_initiation'",
    ):
        if token not in baseline_text:
            findings.append(f"frontend baseline constant missing: {token}")

    intake_view_text = _read(INTAKE_VIEW)
    for token in (
        "PROJECT_INTAKE_SCENE_KEY",
        "PROJECT_INITIATION_MENU_XMLID",
        "getSceneByKey(PROJECT_INTAKE_SCENE_KEY)",
        "scene_key: PROJECT_INTAKE_SCENE_KEY",
    ):
        if token not in intake_view_text:
            findings.append(f"ProjectsIntakeView missing token: {token}")

    form_page_text = _read(FORM_PAGE)
    if "PROJECT_INTAKE_SCENE_KEY" not in form_page_text:
        findings.append("ContractFormPage missing PROJECT_INTAKE_SCENE_KEY import/use")

    initiation_text = _read(INITIATION_HANDLER)
    for token in (
        'INTENT_TYPE = "project.initiation.enter"',
        '"intent": "project.dashboard.enter"',
        '"intent": "ui.contract"',
        '"scene_key": "project.dashboard"',
        '"menu_xmlid": menu_xmlid',
    ):
        if token not in initiation_text:
            findings.append(f"project initiation handler missing token: {token}")

    doc_text = _read(BASELINE_DOC)
    for token in (
        "`projects.intake`",
        "`project.initiation.enter`",
        "`project.dashboard.enter`",
        "navigation/native-form scene",
        "business creation truth",
    ):
        if token not in doc_text:
            findings.append(f"baseline doc missing token: {token}")

    report = {
        "status": "PASS" if not findings else "FAIL",
        "finding_count": len(findings),
        "findings": findings,
    }
    _write_json(OUT_JSON, report)
    if findings:
        print("[product_project_creation_mainline_guard] FAIL")
        for item in findings:
            print(f" - {item}")
        return 1
    print("[product_project_creation_mainline_guard] PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
