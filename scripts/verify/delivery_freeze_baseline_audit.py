#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def main() -> int:
    freeze_doc = ROOT / "docs" / "ops" / "delivery_freeze_baseline_v1.md"
    required_files = [
        ROOT / "artifacts" / "menu" / "delivery_user_navigation_v1.json",
        ROOT / "artifacts" / "menu" / "delivery_admin_navigation_v1.json",
        ROOT / "artifacts" / "menu" / "menu_convergence_diff_v1.json",
        ROOT / "docs" / "ops" / "delivery_formal_entry_page_review_v2.md",
        ROOT / "artifacts" / "codex" / "unified-system-menu-click-usability-smoke" / "20260411T181557Z" / "summary.json",
    ]

    errors: list[str] = []
    if not freeze_doc.exists():
        errors.append("missing_file:docs/ops/delivery_freeze_baseline_v1.md")
    else:
        text = freeze_doc.read_text(encoding="utf-8")
        for token in [
            "## Freeze Scope",
            "## Frozen Evidence",
            "## Frozen Decisions",
            "## Acceptance Snapshot",
            "delivery_decision: `GO`",
            "menu_299_return_path: `closed`",
            "watchpoint_count: `0`",
            "unified_menu_smoke: `PASS (leaf_count=28, fail_count=0)`",
        ]:
            if token not in text:
                errors.append(f"missing_token:{token}")

    for path in required_files:
        if not path.exists():
            errors.append(f"missing_evidence:{path.relative_to(ROOT)}")

    if errors:
        for item in errors:
            print(f"[delivery_freeze_baseline_audit] FAIL: {item}")
        return 2

    print("[delivery_freeze_baseline_audit] PASS")
    print("- delivery freeze baseline doc completeness: PASS")
    print("- referenced freeze evidence availability: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
