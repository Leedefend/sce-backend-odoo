#!/usr/bin/env python3
from __future__ import annotations

import re
from datetime import date
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
UAT_ZH = ROOT / "docs/releases/user_acceptance_checklist.md"
UAT_EN = ROOT / "docs/releases/user_acceptance_checklist.en.md"
PHASE1_GUARD = ROOT / "scripts/verify/release_phase1_navigation_convergence_guard.py"
PHASE2_GUARD = ROOT / "scripts/verify/release_phase2_core_scenarios_closure_guard.py"
PHASE6_GUARD = ROOT / "scripts/verify/release_phase6_launch_closeout_guard.py"
PHASE2_CHECKLIST_ZH = ROOT / "docs/releases/phase_2_core_scenarios_closure_checklist.md"
PHASE2_CHECKLIST_EN = ROOT / "docs/releases/phase_2_core_scenarios_closure_checklist.en.md"
PHASE3_REPORT_ZH = ROOT / "docs/releases/phase_3_role_permission_execution_report.md"
PHASE3_REPORT_EN = ROOT / "docs/releases/phase_3_role_permission_execution_report.en.md"
PHASE4_REPORT_ZH = ROOT / "docs/releases/phase_4_frontend_stability_execution_report.md"
PHASE4_REPORT_EN = ROOT / "docs/releases/phase_4_frontend_stability_execution_report.en.md"
PHASE5_REPORT_ZH = ROOT / "docs/releases/phase_5_verification_deployment_execution_report.md"
PHASE5_REPORT_EN = ROOT / "docs/releases/phase_5_verification_deployment_execution_report.en.md"
PHASE6_REVIEW_ZH = ROOT / "docs/releases/scems_v1_0_post_launch_review.md"
PHASE6_REVIEW_EN = ROOT / "docs/releases/scems_v1_0_post_launch_review.en.md"
OUT_MD = ROOT / "artifacts/release/user_acceptance_closeout.md"
ISO_DATE_RE = re.compile(r"\b20\d{2}-\d{2}-\d{2}\b")


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="ignore")


def _fail(errors: list[str]) -> int:
    print("[release_user_acceptance_closeout_guard] FAIL")
    for error in errors:
        print(f"- {error}")
    return 1


def _contains_all(text: str, tokens: list[str], label: str, errors: list[str]) -> None:
    missing = [token for token in tokens if token not in text]
    if missing:
        errors.append(f"{label} missing tokens: {', '.join(missing)}")


def _contains_iso_date(text: str, label: str, errors: list[str]) -> None:
    if not ISO_DATE_RE.search(text):
        errors.append(f"{label} missing ISO closeout date")


def _validate_uat_checklists(errors: list[str]) -> None:
    for path in (UAT_ZH, UAT_EN):
        text = _read(path)
        unchecked = [line for line in text.splitlines() if line.strip().startswith("- [ ]")]
        if unchecked:
            errors.append(f"{path.name} still has unchecked items: {len(unchecked)}")
        _contains_all(text, ["PASS", "Codex"], path.name, errors)
        _contains_iso_date(text, path.name, errors)


def _validate_evidence(errors: list[str]) -> None:
    for path in (PHASE1_GUARD, PHASE2_GUARD, PHASE6_GUARD):
        if not path.is_file():
            errors.append(f"missing guard: {path.relative_to(ROOT).as_posix()}")
    phase2_zh = _read(PHASE2_CHECKLIST_ZH)
    phase2_en = _read(PHASE2_CHECKLIST_EN)
    _contains_all(phase2_zh, ["my_work.workspace", "projects.ledger", "project.management", "合同", "成本", "资金", "风险"], PHASE2_CHECKLIST_ZH.name, errors)
    _contains_all(phase2_en, ["my_work.workspace", "projects.ledger", "project.management", "contract", "cost", "fund", "Risk"], PHASE2_CHECKLIST_EN.name, errors)
    for text, label in ((_read(PHASE3_REPORT_ZH), PHASE3_REPORT_ZH.name), (_read(PHASE3_REPORT_EN), PHASE3_REPORT_EN.name)):
        _contains_all(
            text,
            [
                "verify.role.management_viewer.readonly.guard",
                "verify.project.dashboard.role_runtime.guard",
                "verify.scene.permission_reasoncode_deeplink.guard",
                "PASS",
            ],
            label,
            errors,
        )
    for text, label in ((_read(PHASE4_REPORT_ZH), PHASE4_REPORT_ZH.name), (_read(PHASE4_REPORT_EN), PHASE4_REPORT_EN.name)):
        _contains_all(text, ["verify.frontend.runtime_navigation_hud.guard", "PASS"], label, errors)
    for text, label in ((_read(PHASE5_REPORT_ZH), PHASE5_REPORT_ZH.name), (_read(PHASE5_REPORT_EN), PHASE5_REPORT_EN.name)):
        _contains_all(text, ["verify.phase_next.evidence.bundle", "verify.runtime.surface.dashboard.strict.guard", "PASS"], label, errors)
    for text, label in ((_read(PHASE6_REVIEW_ZH), PHASE6_REVIEW_ZH.name), (_read(PHASE6_REVIEW_EN), PHASE6_REVIEW_EN.name)):
        _contains_all(text, ["PASS", "P0", "0"], label, errors)


def _write_report() -> None:
    OUT_MD.parent.mkdir(parents=True, exist_ok=True)
    OUT_MD.write_text(
        "\n".join(
            [
                "# SCEMS v1.0 User Acceptance Closeout",
                "",
                "- status: PASS",
                f"- date: `{date.today().isoformat()}`",
                "- functional acceptance: PASS",
                "- permission acceptance: PASS",
                "- stability acceptance: PASS",
                "- evidence: Phase 1/2/3/4/5/6 guard and report chain",
                "",
            ]
        ),
        encoding="utf-8",
    )


def main() -> int:
    paths = [
        UAT_ZH,
        UAT_EN,
        PHASE2_CHECKLIST_ZH,
        PHASE2_CHECKLIST_EN,
        PHASE3_REPORT_ZH,
        PHASE3_REPORT_EN,
        PHASE4_REPORT_ZH,
        PHASE4_REPORT_EN,
        PHASE5_REPORT_ZH,
        PHASE5_REPORT_EN,
        PHASE6_REVIEW_ZH,
        PHASE6_REVIEW_EN,
    ]
    errors = [f"missing file: {path.relative_to(ROOT).as_posix()}" for path in paths if not path.is_file()]
    if errors:
        return _fail(errors)
    try:
        _validate_uat_checklists(errors)
        _validate_evidence(errors)
    except Exception as exc:
        return _fail([f"guard crashed: {exc}"])
    if errors:
        return _fail(errors)
    _write_report()
    print("[release_user_acceptance_closeout_guard] PASS")
    print(f"[release_user_acceptance_closeout_guard] report={OUT_MD.relative_to(ROOT).as_posix()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
