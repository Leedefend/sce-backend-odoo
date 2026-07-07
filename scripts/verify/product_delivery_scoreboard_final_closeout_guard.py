#!/usr/bin/env python3
from __future__ import annotations
import re
from datetime import date
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SCOREBOARD = ROOT / "docs/product/delivery/v1/delivery_readiness_scoreboard_v1.md"
OUT_MD = ROOT / "artifacts/release/product_delivery_scoreboard_final_closeout.md"
ISO_DATE_RE = re.compile(r"\b20\d{2}-\d{2}-\d{2}\b")


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="ignore")


def _fail(errors: list[str]) -> int:
    print("[product_delivery_scoreboard_final_closeout_guard] FAIL")
    for error in errors:
        print(f"- {error}")
    return 1


def _contains_all(text: str, tokens: list[str], errors: list[str]) -> None:
    missing = [token for token in tokens if token not in text]
    if missing:
        errors.append(f"{SCOREBOARD.name} missing tokens: {', '.join(missing)}")


def _contains_iso_date(text: str, errors: list[str]) -> None:
    if not ISO_DATE_RE.search(text):
        errors.append(f"{SCOREBOARD.name} missing ISO closeout date")


def _write_report() -> None:
    OUT_MD.parent.mkdir(parents=True, exist_ok=True)
    OUT_MD.write_text(
        "\n".join(
            [
                "# Product Delivery Scoreboard Final Closeout",
                "",
                "- status: PASS",
                f"- date: `{date.today().isoformat()}`",
                "- evidence: product delivery scoreboard aligns to current main closeout gates",
                "",
            ]
        ),
        encoding="utf-8",
    )


def main() -> int:
    if not SCOREBOARD.is_file():
        return _fail([f"missing file: {SCOREBOARD.relative_to(ROOT).as_posix()}"])
    text = _read(SCOREBOARD)
    errors: list[str] = []
    forbidden = [
        "topic/ledger-reconciliation-trend",
        "098d897f8",
        "deprecated refs remain",
        "Remaining blocking posture",
        "strict live-fetch dependency",
        "network-restricted runners",
    ]
    hits = [token for token in forbidden if token in text]
    if hits:
        errors.append(f"{SCOREBOARD.name} still has stale scoreboard wording: {', '.join(hits)}")
    if text.count("CI profile posture:") > 1:
        errors.append(f"{SCOREBOARD.name} has duplicated CI profile posture lines")
    _contains_all(
        text,
        [
            "commit_ref:",
            "verify.release.delivery_9_module.final_closeout.guard",
            "verify.release.current_status.wording_closeout.guard",
            "verify.portal.payment_request_approval_field_consumer_audit",
            "unexpected_deprecated_refs=0",
            "Release Blocking Gaps (Current)",
            "No release-blocking gaps remain",
        ],
        errors,
    )
    _contains_iso_date(text, errors)
    if errors:
        return _fail(errors)
    _write_report()
    print("[product_delivery_scoreboard_final_closeout_guard] PASS")
    print(f"[product_delivery_scoreboard_final_closeout_guard] report={OUT_MD.relative_to(ROOT).as_posix()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
