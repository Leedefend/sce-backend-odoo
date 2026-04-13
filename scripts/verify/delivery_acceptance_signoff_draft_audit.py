#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def main() -> int:
    path = ROOT / "docs" / "ops" / "delivery_acceptance_signoff_record_draft_v1.md"
    errors: list[str] = []

    if not path.exists():
        errors.append("missing_file:docs/ops/delivery_acceptance_signoff_record_draft_v1.md")
    else:
        text = path.read_text(encoding="utf-8")
        for token in [
            "## Basic Info",
            "## Verified Baseline (Pre-filled)",
            "governance_gate: `PASS (27/27)`",
            "menu_smoke: `PASS (leaf_count=28, fail_count=0)`",
            "## Technical Sign-off (On-site)",
            "## Business Sign-off (On-site)",
            "## Final Release Decision",
        ]:
            if token not in text:
                errors.append(f"missing_token:draft:{token}")

    if errors:
        for item in errors:
            print(f"[delivery_acceptance_signoff_draft_audit] FAIL: {item}")
        return 2

    print("[delivery_acceptance_signoff_draft_audit] PASS")
    print("- on-site signoff draft completeness: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
