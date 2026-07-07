#!/usr/bin/env python3
from __future__ import annotations

import re
from datetime import date
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
ROUND1_ZH = ROOT / "docs/releases/v1_0_iteration_round_1_checklist.md"
ROUND1_EN = ROOT / "docs/releases/v1_0_iteration_round_1_checklist.en.md"
ROUND1_SCOPE_ZH = ROOT / "docs/releases/v1_0_iteration_round_1_scope.md"
ROUND1_SCOPE_EN = ROOT / "docs/releases/v1_0_iteration_round_1_scope.en.md"
WORKBENCH_ZH = ROOT / "docs/product/workbench_product_acceptance_checklist_v1.md"
WORKBENCH_EN = ROOT / "docs/product/workbench_product_acceptance_checklist_v1.en.md"
PHASE2_ZH = ROOT / "docs/releases/phase_2_core_scenarios_closure_checklist.md"
PHASE2_EN = ROOT / "docs/releases/phase_2_core_scenarios_closure_checklist.en.md"
PHASE4_ZH = ROOT / "docs/releases/phase_4_frontend_stability_execution_report.md"
PHASE4_EN = ROOT / "docs/releases/phase_4_frontend_stability_execution_report.en.md"
PHASE5_ZH = ROOT / "docs/releases/phase_5_verification_deployment_execution_report.md"
PHASE5_EN = ROOT / "docs/releases/phase_5_verification_deployment_execution_report.en.md"
UAT_ZH = ROOT / "docs/releases/user_acceptance_checklist.md"
UAT_EN = ROOT / "docs/releases/user_acceptance_checklist.en.md"
PHASE6_ZH = ROOT / "docs/releases/scems_v1_0_post_launch_review.md"
PHASE6_EN = ROOT / "docs/releases/scems_v1_0_post_launch_review.en.md"
OUT_MD = ROOT / "artifacts/release/round1_final_closeout.md"

GUARDS = [
    ROOT / "scripts/verify/release_phase1_navigation_convergence_guard.py",
    ROOT / "scripts/verify/release_phase2_core_scenarios_closure_guard.py",
    ROOT / "scripts/verify/release_phase6_launch_closeout_guard.py",
    ROOT / "scripts/verify/release_user_acceptance_closeout_guard.py",
    ROOT / "scripts/verify/workbench_product_acceptance_guard.py",
]

ROUND1_PAGES = [
    "project.management",
    "projects.ledger",
    "projects.list",
    "task.center",
    "risk.center",
    "cost.project_boq",
]
ISO_DATE_RE = re.compile(r"\b20\d{2}-\d{2}-\d{2}\b")


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="ignore")


def _fail(errors: list[str]) -> int:
    print("[release_round1_final_closeout_guard] FAIL")
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


def _validate_checked(path: Path, errors: list[str]) -> None:
    text = _read(path)
    unchecked = [line for line in text.splitlines() if line.strip().startswith("- [ ]")]
    if unchecked:
        errors.append(f"{path.name} still has unchecked items: {len(unchecked)}")
    _contains_all(text, ["PASS", "Codex"], path.name, errors)
    _contains_iso_date(text, path.name, errors)
    _contains_all(text, ROUND1_PAGES, path.name, errors)
    _contains_all(
        text,
        [
            "verify.release.round1.final_closeout.guard",
            "verify.frontend.build",
            "verify.frontend.typecheck.strict",
            "verify.project.dashboard.contract",
            "verify.phase_next.evidence.bundle",
        ],
        path.name,
        errors,
    )


def _validate_scope(errors: list[str]) -> None:
    for path in (ROUND1_SCOPE_ZH, ROUND1_SCOPE_EN):
        _contains_all(_read(path), ROUND1_PAGES, path.name, errors)


def _validate_product_evidence(errors: list[str]) -> None:
    for path, tokens in (
        (WORKBENCH_ZH, ["today_focus", "风险", "verify.phase_next.evidence.bundle"]),
        (WORKBENCH_EN, ["today_focus", "risk", "verify.phase_next.evidence.bundle"]),
    ):
        text = _read(path)
        if "- [ ]" in text:
            errors.append(f"{path.name} still has unchecked items")
        _contains_all(text, tokens, path.name, errors)


def _validate_release_evidence(errors: list[str]) -> None:
    for path, tokens in (
        (PHASE2_ZH, ["project.management", "projects.ledger", "风险摘要", "Risk"]),
        (PHASE2_EN, ["project.management", "projects.ledger", "risk summary", "Risk"]),
    ):
        text = _read(path)
        if "- [ ]" in text:
            errors.append(f"{path.name} still has unchecked items")
        _contains_all(text, tokens, path.name, errors)
    for path in (PHASE4_ZH, PHASE4_EN):
        _contains_all(
            _read(path),
            ["verify.frontend.build", "verify.frontend.typecheck.strict", "verify.list.surface.clean", "PASS"],
            path.name,
            errors,
        )
    for path in (PHASE5_ZH, PHASE5_EN):
        _contains_all(
            _read(path),
            ["verify.phase_next.evidence.bundle", "verify.runtime.surface.dashboard.strict.guard", "PASS"],
            path.name,
            errors,
        )
    for path in (UAT_ZH, UAT_EN):
        text = _read(path)
        if "- [ ]" in text:
            errors.append(f"{path.name} still has unchecked items")
        _contains_all(text, ["PASS", "verify.release.user_acceptance.closeout.guard"], path.name, errors)
    for path in (PHASE6_ZH, PHASE6_EN):
        _contains_all(text := _read(path), ["PASS", "P0", "0"], path.name, errors)
        if "open" in text.lower() and "P0" in text:
            _contains_all(text, ["0"], path.name, errors)


def _write_report() -> None:
    OUT_MD.parent.mkdir(parents=True, exist_ok=True)
    OUT_MD.write_text(
        "\n".join(
            [
                "# v1.0 Iteration Round 1 Final Closeout",
                "",
                "- status: PASS",
                f"- date: `{date.today().isoformat()}`",
                "- owner: Codex",
                "- product expression: PASS",
                "- release regression chain: PASS",
                "- evidence: Round 1 checklist, workbench product acceptance, Phase 2/4/5/6 reports, UAT closeout",
                "",
            ]
        ),
        encoding="utf-8",
    )


def main() -> int:
    paths = [
        ROUND1_ZH,
        ROUND1_EN,
        ROUND1_SCOPE_ZH,
        ROUND1_SCOPE_EN,
        WORKBENCH_ZH,
        WORKBENCH_EN,
        PHASE2_ZH,
        PHASE2_EN,
        PHASE4_ZH,
        PHASE4_EN,
        PHASE5_ZH,
        PHASE5_EN,
        UAT_ZH,
        UAT_EN,
        PHASE6_ZH,
        PHASE6_EN,
        *GUARDS,
    ]
    errors = [f"missing file: {path.relative_to(ROOT).as_posix()}" for path in paths if not path.is_file()]
    if errors:
        return _fail(errors)
    try:
        _validate_checked(ROUND1_ZH, errors)
        _validate_checked(ROUND1_EN, errors)
        _validate_scope(errors)
        _validate_product_evidence(errors)
        _validate_release_evidence(errors)
    except Exception as exc:
        return _fail([f"guard crashed: {exc}"])
    if errors:
        return _fail(errors)
    _write_report()
    print("[release_round1_final_closeout_guard] PASS")
    print(f"[release_round1_final_closeout_guard] report={OUT_MD.relative_to(ROOT).as_posix()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
