#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
CHECKLIST = ROOT / "docs" / "frontend" / "sidebar_navigation_consumer_acceptance_v1.md"

REQUIRED_VERIFY_FILES = [
    "scripts/verify/sidebar_navigation_consumer_verify.py",
    "scripts/verify/sidebar_active_chain_verify.py",
    "scripts/verify/sidebar_directory_rule_verify.py",
    "scripts/verify/sidebar_unavailable_guard_verify.py",
    "scripts/verify/sidebar_route_consumer_ux_verify.py",
    "scripts/verify/sidebar_interaction_smoke_verify.py",
    "scripts/verify/sidebar_acceptance_checklist_verify.py",
]


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def main() -> int:
    if not CHECKLIST.exists():
      raise AssertionError(f"missing checklist doc: {CHECKLIST}")

    text = _read(CHECKLIST)
    for rel in REQUIRED_VERIFY_FILES:
        if rel not in text:
            raise AssertionError(f"checklist missing verify mapping: {rel}")
        target = ROOT / rel
        if not target.exists():
            raise AssertionError(f"missing verify script file: {rel}")

    print("[verify.frontend.sidebar.acceptance_checklist] PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

