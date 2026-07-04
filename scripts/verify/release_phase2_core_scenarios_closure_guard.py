#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
POLICY = ROOT / "docs/product/delivery/v1/construction_pm_v1_scene_surface_policy.json"
SCOPE_ZH = ROOT / "docs/releases/release_scope_v1.md"
SCOPE_EN = ROOT / "docs/releases/release_scope_v1.en.md"
BOARD_ZH = ROOT / "docs/releases/construction_system_v1_execution_board.md"
BOARD_EN = ROOT / "docs/releases/construction_system_v1_execution_board.en.md"
SCENE_XML = ROOT / "addons/smart_construction_scene/data/sc_scene_orchestration.xml"
PROJECT_SCENE_XML = ROOT / "addons/smart_construction_scene/data/project_management_scene.xml"
PROJECT_DASHBOARD_MAPPING = ROOT / "docs/contract/project_management_capability_mapping_v2.json"
MY_WORK_REPORT_ZH = ROOT / "docs/releases/phase_2_w1_my_work_minimum_loop_report.md"
MY_WORK_REPORT_EN = ROOT / "docs/releases/phase_2_w1_my_work_minimum_loop_report.en.md"
LEDGER_REPORT_ZH = ROOT / "docs/releases/phase_2_w1_ledger_to_management_route_report.md"
LEDGER_REPORT_EN = ROOT / "docs/releases/phase_2_w1_ledger_to_management_route_report.en.md"
PROJECT_REPORT_ZH = ROOT / "docs/releases/phase_2_w1_project_management_7block_verify_report.md"
PROJECT_REPORT_EN = ROOT / "docs/releases/phase_2_w1_project_management_7block_verify_report.en.md"
PHASE4_REPORT_ZH = ROOT / "docs/releases/phase_4_frontend_stability_execution_report.md"
PHASE4_REPORT_EN = ROOT / "docs/releases/phase_4_frontend_stability_execution_report.en.md"
PHASE5_CHECKLIST_ZH = ROOT / "docs/releases/phase_5_verification_deployment_checklist.md"
PHASE5_CHECKLIST_EN = ROOT / "docs/releases/phase_5_verification_deployment_checklist.en.md"
OUT_MD = ROOT / "artifacts/release/phase2_core_scenarios_closure.md"

CORE_SCENES = [
    "my_work.workspace",
    "projects.ledger",
    "project.management",
    "contracts.workspace",
    "cost.analysis",
    "finance.workspace",
    "risk.center",
]
BUSINESS_WORKBENCH_SCENES = ["contracts.workspace", "cost.analysis", "finance.workspace"]
PROJECT_BLOCKS = ["Header", "Metrics", "Progress", "Contract", "Cost", "Finance", "Risk"]


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="ignore")


def _fail(errors: list[str]) -> int:
    print("[release_phase2_core_scenarios_closure_guard] FAIL")
    for error in errors:
        print(f"- {error}")
    return 1


def _contains_all(text: str, tokens: list[str], label: str, errors: list[str]) -> None:
    missing = [token for token in tokens if token not in text]
    if missing:
        errors.append(f"{label} missing tokens: {', '.join(missing)}")


def _line_done(text: str, token: str, phase: str) -> bool:
    return any(token in line and f"| {phase} | DONE |" in line for line in text.splitlines())


def _validate_docs(errors: list[str]) -> None:
    scope_zh = _read(SCOPE_ZH)
    scope_en = _read(SCOPE_EN)
    board_zh = _read(BOARD_ZH)
    board_en = _read(BOARD_EN)
    _contains_all(scope_zh, CORE_SCENES, "release_scope_v1.md", errors)
    _contains_all(scope_en, CORE_SCENES, "release_scope_v1.en.md", errors)
    if "| Phase 2 | 核心场景闭环 | DONE |" not in board_zh:
        errors.append("Chinese execution board must mark Phase 2 core scenario closure DONE")
    if "| Phase 2 | Core scenario closure | DONE |" not in board_en:
        errors.append("English execution board must mark Phase 2 core scenario closure DONE")
    for task in ("W1-03", "W1-04", "W1-05"):
        if not _line_done(board_zh, task, "P2"):
            errors.append(f"Chinese execution board missing DONE evidence for {task}")
        if not _line_done(board_en, task, "P2"):
            errors.append(f"English execution board missing DONE evidence for {task}")


def _validate_phase2_reports(errors: list[str]) -> None:
    for path in (MY_WORK_REPORT_ZH, MY_WORK_REPORT_EN):
        text = _read(path)
        _contains_all(text, ["DONE", "my_work.workspace"], path.name, errors)
        is_en = path.name.endswith(".en.md")
        _contains_all(text, ["todo", "Quick", "risk"] if is_en else ["待办", "快捷", "风险"], path.name, errors)
        if "PASS" not in text:
            errors.append(f"{path.name} must record PASS runtime verification")
    for path in (LEDGER_REPORT_ZH, LEDGER_REPORT_EN):
        text = _read(path)
        _contains_all(text, ["projects.ledger", "project.management", "/s/project.management"], path.name, errors)
    for path in (PROJECT_REPORT_ZH, PROJECT_REPORT_EN):
        text = _read(path)
        _contains_all(text, ["DONE", "verify.project.dashboard.contract"], path.name, errors)
        _contains_all(text, ["7-block"], path.name, errors)


def _validate_scene_sources(errors: list[str]) -> None:
    scene_text = _read(SCENE_XML)
    project_text = _read(PROJECT_SCENE_XML)
    policy_text = _read(POLICY)
    mapping_text = _read(PROJECT_DASHBOARD_MAPPING)
    _contains_all(scene_text, CORE_SCENES, "sc_scene_orchestration.xml", errors)
    _contains_all(policy_text, CORE_SCENES, "construction_pm_v1_scene_surface_policy.json", errors)
    _contains_all(project_text, ["project.management", "/s/project.management"], "project_management_scene.xml", errors)
    _contains_all(mapping_text, [block.lower() for block in PROJECT_BLOCKS], "project_management_capability_mapping_v2.json", errors)
    _contains_all(policy_text, BUSINESS_WORKBENCH_SCENES, "business workbench policy", errors)


def _validate_runtime_evidence(errors: list[str]) -> None:
    phase4_zh = _read(PHASE4_REPORT_ZH)
    phase4_en = _read(PHASE4_REPORT_EN)
    phase5_zh = _read(PHASE5_CHECKLIST_ZH)
    phase5_en = _read(PHASE5_CHECKLIST_EN)
    for text, label in ((phase4_zh, PHASE4_REPORT_ZH.name), (phase4_en, PHASE4_REPORT_EN.name)):
        _contains_all(
            text,
            ["verify.frontend.runtime_navigation_hud.guard", "verify.scene.hud.trace.smoke", "PASS"],
            label,
            errors,
        )
    for text, label in ((phase5_zh, PHASE5_CHECKLIST_ZH.name), (phase5_en, PHASE5_CHECKLIST_EN.name)):
        _contains_all(text, ["[x]", "system.init", "ui.contract"], label, errors)
        _contains_all(text, ["verify.phase_next.evidence.bundle", "verify.scene.catalog.governance.guard"], label, errors)


def _write_report() -> None:
    OUT_MD.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# Phase 2 Core Scenarios Closure Evidence",
        "",
        "- status: PASS",
        "- core_scenes:",
        *[f"  - `{scene}`" for scene in CORE_SCENES],
        "- evidence:",
        "  - W1-03 `project.management` 7-block contract verification",
        "  - W1-04 `my_work.workspace` minimum loop verification",
        "  - W1-05 `projects.ledger -> project.management` route chain verification",
        "  - Phase 4 user/hud runtime navigation evidence",
        "  - Phase 5 `system.init` / `ui.contract` stability checklist",
        "",
    ]
    OUT_MD.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    paths = [
        POLICY,
        SCOPE_ZH,
        SCOPE_EN,
        BOARD_ZH,
        BOARD_EN,
        SCENE_XML,
        PROJECT_SCENE_XML,
        PROJECT_DASHBOARD_MAPPING,
        MY_WORK_REPORT_ZH,
        MY_WORK_REPORT_EN,
        LEDGER_REPORT_ZH,
        LEDGER_REPORT_EN,
        PROJECT_REPORT_ZH,
        PROJECT_REPORT_EN,
        PHASE4_REPORT_ZH,
        PHASE4_REPORT_EN,
        PHASE5_CHECKLIST_ZH,
        PHASE5_CHECKLIST_EN,
    ]
    errors = [f"missing file: {path.relative_to(ROOT).as_posix()}" for path in paths if not path.is_file()]
    if errors:
        return _fail(errors)
    try:
        _validate_docs(errors)
        _validate_phase2_reports(errors)
        _validate_scene_sources(errors)
        _validate_runtime_evidence(errors)
    except Exception as exc:
        return _fail([f"guard crashed: {exc}"])
    if errors:
        return _fail(errors)
    _write_report()
    print("[release_phase2_core_scenarios_closure_guard] PASS")
    print(f"[release_phase2_core_scenarios_closure_guard] report={OUT_MD.relative_to(ROOT).as_posix()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
