#!/usr/bin/env python3
from __future__ import annotations

import re
from datetime import date
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
MATRIX_ZH = ROOT / "docs/releases/delivery_9_module_acceptance_matrix_v1.md"
MATRIX_EN = ROOT / "docs/releases/delivery_9_module_acceptance_matrix_v1.en.md"
JOURNEY_ZH = ROOT / "docs/releases/delivery_9_module_role_journey_smoke_checklist_v1.md"
JOURNEY_EN = ROOT / "docs/releases/delivery_9_module_role_journey_smoke_checklist_v1.en.md"
BLOCKERS_ZH = ROOT / "docs/releases/delivery_sprint_blockers_v1.md"
BLOCKERS_EN = ROOT / "docs/releases/delivery_sprint_blockers_v1.en.md"
SCOREBOARD_ZH = ROOT / "docs/releases/delivery_readiness_scoreboard_v1.md"
SCOREBOARD_EN = ROOT / "docs/releases/delivery_readiness_scoreboard_v1.en.md"
OUT_MD = ROOT / "artifacts/release/delivery_9_module_final_closeout.md"

GUARD_TOKENS = [
    "verify.scene.delivery.readiness.role_matrix",
    "verify.portal.payment_request_approval_all_smoke.container",
    "verify.portal.payment_request_approval_field_consumer_audit",
    "verify.release.delivery_9_module.final_closeout.guard",
]
ISO_DATE_RE = re.compile(r"\b20\d{2}-\d{2}-\d{2}\b")


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="ignore")


def _fail(errors: list[str]) -> int:
    print("[delivery_9_module_final_closeout_guard] FAIL")
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


def _validate_no_stale_status(text: str, label: str, errors: list[str]) -> None:
    deprecated_payment_summary_key = "live_no_" + "allowed_actions"
    stale_tokens = [
        "| PENDING |",
        "| FAIL |",
        "| IN_PROGRESS |",
        "| BLOCKED |",
        "not yet in a delivery-ready state",
        "未达到“正式交付就绪”状态",
        "handoff flow is blocked",
        "交接阻塞",
        deprecated_payment_summary_key,
    ]
    hits = [token for token in stale_tokens if token in text]
    if hits:
        errors.append(f"{label} still contains stale delivery status: {', '.join(hits)}")


def _validate_docs(errors: list[str]) -> None:
    for path in (MATRIX_ZH, MATRIX_EN, JOURNEY_ZH, JOURNEY_EN, BLOCKERS_ZH, BLOCKERS_EN, SCOREBOARD_ZH, SCOREBOARD_EN):
        text = _read(path)
        _validate_no_stale_status(text, path.name, errors)
        _contains_all(text, ["PASS"], path.name, errors)
        _contains_iso_date(text, path.name, errors)
        _contains_all(text, GUARD_TOKENS, path.name, errors)
    for path in (MATRIX_ZH, MATRIX_EN):
        text = _read(path)
        pass_rows = [line for line in text.splitlines() if line.startswith("|") and "| PASS |" in line]
        if len(pass_rows) < 9:
            errors.append(f"{path.name} must include at least 9 PASS module rows, got {len(pass_rows)}")
    for path in (BLOCKERS_ZH, BLOCKERS_EN):
        text = _read(path)
        closed_rows = [line for line in text.splitlines() if line.startswith("| B") and "| CLOSED |" in line]
        if len(closed_rows) < 5:
            errors.append(f"{path.name} must close all 5 P0 blockers, got {len(closed_rows)}")


def _write_report() -> None:
    OUT_MD.parent.mkdir(parents=True, exist_ok=True)
    OUT_MD.write_text(
        "\n".join(
            [
                "# 9-Module Delivery Final Closeout",
                "",
                "- status: PASS",
                f"- date: `{date.today().isoformat()}`",
                "- evidence: role matrix, finance approval all smoke, field consumer audit, delivery closeout docs",
                "",
            ]
        ),
        encoding="utf-8",
    )


def main() -> int:
    paths = [MATRIX_ZH, MATRIX_EN, JOURNEY_ZH, JOURNEY_EN, BLOCKERS_ZH, BLOCKERS_EN, SCOREBOARD_ZH, SCOREBOARD_EN]
    errors = [f"missing file: {path.relative_to(ROOT).as_posix()}" for path in paths if not path.is_file()]
    if errors:
        return _fail(errors)
    try:
        _validate_docs(errors)
    except Exception as exc:
        return _fail([f"guard crashed: {exc}"])
    if errors:
        return _fail(errors)
    _write_report()
    print("[delivery_9_module_final_closeout_guard] PASS")
    print(f"[delivery_9_module_final_closeout_guard] report={OUT_MD.relative_to(ROOT).as_posix()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
