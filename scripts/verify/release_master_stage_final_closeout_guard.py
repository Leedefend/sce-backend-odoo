#!/usr/bin/env python3
from __future__ import annotations

import re
from datetime import date
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
AUDIT_ZH = ROOT / "docs/releases/v1_0_iteration_master_stage_audit.md"
AUDIT_EN = ROOT / "docs/releases/v1_0_iteration_master_stage_audit.en.md"
PLAN_ZH = ROOT / "docs/releases/v1_0_iteration_master_stage_plan.md"
REGRESSION_ZH = ROOT / "docs/releases/v1_0_iteration_round_1_regression_report.md"
REGRESSION_EN = ROOT / "docs/releases/v1_0_iteration_round_1_regression_report.en.md"
ROUND1_ZH = ROOT / "docs/releases/v1_0_iteration_round_1_checklist.md"
ROUND1_EN = ROOT / "docs/releases/v1_0_iteration_round_1_checklist.en.md"
ROUND1_GUARD = ROOT / "scripts/verify/release_round1_final_closeout_guard.py"
OUT_MD = ROOT / "artifacts/release/master_stage_final_closeout.md"

VERIFY_TOKENS = [
    "verify.release.round1.final_closeout.guard",
    "verify.frontend.build",
    "verify.frontend.typecheck.strict",
    "verify.project.dashboard.contract",
    "verify.phase_next.evidence.bundle",
]
ISO_DATE_RE = re.compile(r"\b20\d{2}-\d{2}-\d{2}\b")


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="ignore")


def _fail(errors: list[str]) -> int:
    print("[release_master_stage_final_closeout_guard] FAIL")
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


def _validate_audit(errors: list[str]) -> None:
    for path, completed_token in (
        (AUDIT_ZH, "最终状态：`已完成`"),
        (AUDIT_EN, "Final status: `Completed`"),
    ):
        text = _read(path)
        _contains_all(text, ["PASS", completed_token], path.name, errors)
        _contains_iso_date(text, path.name, errors)
        _contains_all(text, VERIFY_TOKENS, path.name, errors)
        forbidden = ["Pending closure", "待收口", "等待“本次大阶段登录验证”", "waiting for stage-level login validation"]
        hits = [token for token in forbidden if token in text]
        if hits:
            errors.append(f"{path.name} still contains pending closeout wording: {', '.join(hits)}")


def _validate_plan(errors: list[str]) -> None:
    text = _read(PLAN_ZH)
    _contains_all(text, ["第 4 批：已完成", "反馈收口阶段", "verify.release.round1.final_closeout.guard"], PLAN_ZH.name, errors)


def _validate_regression(errors: list[str]) -> None:
    for path, closeout_token in (
        (REGRESSION_ZH, "最终复验"),
        (REGRESSION_EN, "Final re-check"),
    ):
        text = _read(path)
        _contains_all(text, [closeout_token, "PASS"], path.name, errors)
        _contains_iso_date(text, path.name, errors)
        _contains_all(text, VERIFY_TOKENS, path.name, errors)
        if "当前分支先保留" in text or "do not release yet" in text:
            errors.append(f"{path.name} still contains stale non-release recommendation")


def _validate_round1(errors: list[str]) -> None:
    if not ROUND1_GUARD.is_file():
        errors.append(f"missing guard: {ROUND1_GUARD.relative_to(ROOT).as_posix()}")
    for path in (ROUND1_ZH, ROUND1_EN):
        text = _read(path)
        if "- [ ]" in text:
            errors.append(f"{path.name} still has unchecked items")
        _contains_all(text, ["PASS", "verify.release.round1.final_closeout.guard"], path.name, errors)


def _write_report() -> None:
    OUT_MD.parent.mkdir(parents=True, exist_ok=True)
    OUT_MD.write_text(
        "\n".join(
            [
                "# v1.0 Product Expression Master Stage Final Closeout",
                "",
                "- status: PASS",
                f"- date: `{date.today().isoformat()}`",
                "- owner: Codex",
                "- scope: Task Pack 01-11, Round 1 checklist, minimum regression, final closeout guard",
                "- evidence: master stage audit, Round 1 regression report, Round 1 final closeout guard",
                "",
            ]
        ),
        encoding="utf-8",
    )


def main() -> int:
    paths = [
        AUDIT_ZH,
        AUDIT_EN,
        PLAN_ZH,
        REGRESSION_ZH,
        REGRESSION_EN,
        ROUND1_ZH,
        ROUND1_EN,
    ]
    errors = [f"missing file: {path.relative_to(ROOT).as_posix()}" for path in paths if not path.is_file()]
    if errors:
        return _fail(errors)
    try:
        _validate_audit(errors)
        _validate_plan(errors)
        _validate_regression(errors)
        _validate_round1(errors)
    except Exception as exc:
        return _fail([f"guard crashed: {exc}"])
    if errors:
        return _fail(errors)
    _write_report()
    print("[release_master_stage_final_closeout_guard] PASS")
    print(f"[release_master_stage_final_closeout_guard] report={OUT_MD.relative_to(ROOT).as_posix()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
