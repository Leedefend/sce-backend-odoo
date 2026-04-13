#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def main() -> int:
    path = ROOT / "docs" / "ops" / "delivery_acceptance_signoff_record_v1.md"
    errors: list[str] = []

    if not path.exists():
        errors.append("missing_file:docs/ops/delivery_acceptance_signoff_record_v1.md")
    else:
        text = path.read_text(encoding="utf-8")
        for token in [
            "## Basic Info",
            "## Technical Acceptance",
            "## Business Acceptance",
            "## Final Conclusion",
            "business_decision: `GO / NO_GO`",
            "release_decision: `GO / NO_GO`",
        ]:
            if token not in text:
                errors.append(f"missing_token:signoff:{token}")

    if errors:
        for item in errors:
            print(f"[delivery_acceptance_signoff_record_audit] FAIL: {item}")
        return 2

    print("[delivery_acceptance_signoff_record_audit] PASS")
    print("- sign-off record template completeness: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
