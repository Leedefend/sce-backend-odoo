#!/usr/bin/env python3
from __future__ import annotations

import re
from datetime import date
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
ITERATION_STATUS = ROOT / "docs/releases/delivery_iteration_status_2026-03-20_mainline.md"
PHASE4_ZH = ROOT / "docs/releases/phase_4_frontend_stability_execution_report.md"
PHASE4_EN = ROOT / "docs/releases/phase_4_frontend_stability_execution_report.en.md"
OUT_MD = ROOT / "artifacts/release/current_status_wording_closeout.md"
ISO_DATE_RE = re.compile(r"\b20\d{2}-\d{2}-\d{2}\b")


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="ignore")


def _fail(errors: list[str]) -> int:
    print("[release_current_status_wording_closeout_guard] FAIL")
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


def _validate_iteration_status(errors: list[str]) -> None:
    text = _read(ITERATION_STATUS)
    forbidden = ["## 5. 当前未完成与后续计划", "结果：FAIL", "P0 剩余"]
    hits = [token for token in forbidden if token in text]
    if hits:
        errors.append(f"{ITERATION_STATUS.name} still has stale unfinished wording: {', '.join(hits)}")
    _contains_all(
        text,
        [
            "最终复验",
            "PASS",
            "verify.release.delivery_9_module.final_closeout.guard",
            "verify.scene.delivery.readiness.role_matrix",
        ],
        ITERATION_STATUS.name,
        errors,
    )
    _contains_iso_date(text, ITERATION_STATUS.name, errors)


def _validate_phase4(errors: list[str]) -> None:
    for path, forbidden in (
        (PHASE4_ZH, ["## 3. 当前阻塞项"]),
        (PHASE4_EN, ["## 3. Current Blockers"]),
    ):
        text = _read(path)
        hits = [token for token in forbidden if token in text]
        if hits:
            errors.append(f"{path.name} still has blocker heading: {', '.join(hits)}")
        _contains_all(text, ["PASS", "不阻塞" if path == PHASE4_ZH else "non-blocking"], path.name, errors)


def _write_report() -> None:
    OUT_MD.parent.mkdir(parents=True, exist_ok=True)
    OUT_MD.write_text(
        "\n".join(
            [
                "# Current Release Status Wording Closeout",
                "",
                "- status: PASS",
                f"- date: `{date.today().isoformat()}`",
                "- evidence: delivery iteration status and Phase 4 reports no longer expose stale blocker wording",
                "",
            ]
        ),
        encoding="utf-8",
    )


def main() -> int:
    paths = [ITERATION_STATUS, PHASE4_ZH, PHASE4_EN]
    errors = [f"missing file: {path.relative_to(ROOT).as_posix()}" for path in paths if not path.is_file()]
    if errors:
        return _fail(errors)
    try:
        _validate_iteration_status(errors)
        _validate_phase4(errors)
    except Exception as exc:
        return _fail([f"guard crashed: {exc}"])
    if errors:
        return _fail(errors)
    _write_report()
    print("[release_current_status_wording_closeout_guard] PASS")
    print(f"[release_current_status_wording_closeout_guard] report={OUT_MD.relative_to(ROOT).as_posix()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
