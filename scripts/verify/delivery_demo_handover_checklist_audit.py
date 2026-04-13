#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def main() -> int:
    checklist = ROOT / "docs" / "ops" / "delivery_demo_handover_checklist_v1.md"
    errors: list[str] = []
    if not checklist.exists():
        errors.append("missing_file:docs/ops/delivery_demo_handover_checklist_v1.md")
    else:
        text = checklist.read_text(encoding="utf-8")
        for token in [
            "## Demo Preflight",
            "## Demo Script",
            "### Segment A：基础链路",
            "### Segment B：核心业务链",
            "### Segment C：可观测性",
            "## Handover Package",
            "## Acceptance Sign-off",
            "## Post-Handover Guard",
        ]:
            if token not in text:
                errors.append(f"missing_token:checklist:{token}")

    if errors:
        for item in errors:
            print(f"[delivery_demo_handover_checklist_audit] FAIL: {item}")
        return 2

    print("[delivery_demo_handover_checklist_audit] PASS")
    print("- demo and handover checklist completeness: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
