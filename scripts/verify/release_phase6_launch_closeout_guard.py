#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
BOARD_ZH = ROOT / "docs/releases/construction_system_v1_execution_board.md"
BOARD_EN = ROOT / "docs/releases/construction_system_v1_execution_board.en.md"
CHECKLIST_ZH = ROOT / "docs/releases/phase_6_pilot_launch_checklist.md"
CHECKLIST_EN = ROOT / "docs/releases/phase_6_pilot_launch_checklist.en.md"
LAUNCH_ZH = ROOT / "docs/ops/releases/current/scems_v1_0_launch.md"
LAUNCH_EN = ROOT / "docs/ops/releases/current/scems_v1_0_launch.en.md"
REVIEW_ZH = ROOT / "docs/releases/scems_v1_0_post_launch_review.md"
REVIEW_EN = ROOT / "docs/releases/scems_v1_0_post_launch_review.en.md"
ISSUES_ZH = ROOT / "docs/releases/phase_6_issue_ledger.md"
ISSUES_EN = ROOT / "docs/releases/phase_6_issue_ledger.en.md"
REPORT_ZH = ROOT / "docs/releases/phase_6_pilot_launch_execution_report.md"
REPORT_EN = ROOT / "docs/releases/phase_6_pilot_launch_execution_report.en.md"
OUT_MD = ROOT / "artifacts/release/phase6_launch_closeout.md"


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="ignore")


def _fail(errors: list[str]) -> int:
    print("[release_phase6_launch_closeout_guard] FAIL")
    for error in errors:
        print(f"- {error}")
    return 1


def _contains_all(text: str, tokens: list[str], label: str, errors: list[str]) -> None:
    missing = [token for token in tokens if token not in text]
    if missing:
        errors.append(f"{label} missing tokens: {', '.join(missing)}")


def _reject_any(text: str, tokens: list[str], label: str, errors: list[str]) -> None:
    hits = [token for token in tokens if token in text]
    if hits:
        errors.append(f"{label} contains open-ended tokens: {', '.join(hits)}")


def _validate_board(errors: list[str]) -> None:
    board_zh = _read(BOARD_ZH)
    board_en = _read(BOARD_EN)
    if "| Phase 6 | 试运行首发 | DONE |" not in board_zh:
        errors.append("Chinese execution board must mark Phase 6 DONE")
    if "| Phase 6 | Pilot and launch | DONE |" not in board_en:
        errors.append("English execution board must mark Phase 6 DONE")
    for text, label in ((board_zh, BOARD_ZH.name), (board_en, BOARD_EN.name)):
        if not any("W6-03" in line and "| P6 | DONE |" in line for line in text.splitlines()):
            errors.append(f"{label} must mark W6-03 DONE")


def _validate_checklists(errors: list[str]) -> None:
    for path in (CHECKLIST_ZH, CHECKLIST_EN):
        text = _read(path)
        unchecked = [line for line in text.splitlines() if line.strip().startswith("- [ ]")]
        if unchecked:
            errors.append(f"{path.name} still has unchecked items: {len(unchecked)}")
        _contains_all(text, ["24h" if path == CHECKLIST_ZH else "24 hours", "反馈" if path == CHECKLIST_ZH else "feedback"], path.name, errors)


def _validate_launch_and_review(errors: list[str]) -> None:
    for path in (LAUNCH_ZH, LAUNCH_EN, REVIEW_ZH, REVIEW_EN, REPORT_ZH, REPORT_EN):
        text = _read(path)
        _reject_any(text, ["待填写", "TBD", "pending", "进行中", "in progress", "条件通过", "conditional pass"], path.name, errors)
        _contains_all(text, ["PASS", "P0", "0"], path.name, errors)
    _contains_all(_read(REVIEW_ZH), ["稳定发布", "核心链路可用性", "100%", "反馈收集通道已启动"], REVIEW_ZH.name, errors)
    _contains_all(_read(REVIEW_EN), ["stable launch", "Core-path availability", "100%", "feedback intake channel is active"], REVIEW_EN.name, errors)


def _validate_issue_ledger(errors: list[str]) -> None:
    for path in (ISSUES_ZH, ISSUES_EN):
        text = _read(path)
        _contains_all(text, ["P6-001", "P6-002", "CLOSED", "P0", "0"], path.name, errors)
        _reject_any(text, ["OPEN", "BLOCKED"], path.name, errors)


def _write_report() -> None:
    OUT_MD.parent.mkdir(parents=True, exist_ok=True)
    OUT_MD.write_text(
        "\n".join(
            [
                "# Phase 6 Launch Closeout Evidence",
                "",
                "- status: PASS",
                "- phase: `DONE`",
                "- W6-03: `DONE`",
                "- 24h indicators: healthy",
                "- open P0: `0`",
                "- open P1: `0`",
                "- launch conclusion: stable launch",
                "",
            ]
        ),
        encoding="utf-8",
    )


def main() -> int:
    paths = [
        BOARD_ZH,
        BOARD_EN,
        CHECKLIST_ZH,
        CHECKLIST_EN,
        LAUNCH_ZH,
        LAUNCH_EN,
        REVIEW_ZH,
        REVIEW_EN,
        ISSUES_ZH,
        ISSUES_EN,
        REPORT_ZH,
        REPORT_EN,
    ]
    errors = [f"missing file: {path.relative_to(ROOT).as_posix()}" for path in paths if not path.is_file()]
    if errors:
        return _fail(errors)
    try:
        _validate_board(errors)
        _validate_checklists(errors)
        _validate_launch_and_review(errors)
        _validate_issue_ledger(errors)
    except Exception as exc:
        return _fail([f"guard crashed: {exc}"])
    if errors:
        return _fail(errors)
    _write_report()
    print("[release_phase6_launch_closeout_guard] PASS")
    print(f"[release_phase6_launch_closeout_guard] report={OUT_MD.relative_to(ROOT).as_posix()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
