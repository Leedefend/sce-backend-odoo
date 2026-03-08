#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Guard: handlers must not perform contract layout restructuring."""

from __future__ import annotations

import re
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
HANDLER_DIR = ROOT / "addons" / "smart_core" / "handlers"

FORBIDDEN_PATTERNS = [
    re.compile(r"def\s+_ensure_project_form_layout_structure\s*\("),
    re.compile(r"form\[\s*[\"']layout[\"']\s*\]\s*="),
    re.compile(r"views\[\s*[\"']form[\"']\s*\]\s*="),
    re.compile(r"data\[\s*[\"']views[\"']\s*\]\s*="),
    re.compile(r"[\"']project_form_sheet[\"']"),
    re.compile(r"[\"']core_group[\"']"),
    re.compile(r"[\"']advanced_group[\"']"),
]


def main() -> int:
    if not HANDLER_DIR.is_dir():
        print(f"[contract_handler_layout_boundary_guard] FAIL: missing {HANDLER_DIR}")
        return 1

    violations: list[str] = []
    for path in sorted(HANDLER_DIR.glob("*.py")):
        text = path.read_text(encoding="utf-8", errors="ignore")
        for pattern in FORBIDDEN_PATTERNS:
            if pattern.search(text):
                rel = path.relative_to(ROOT).as_posix()
                violations.append(f"{rel}: forbidden handler layout governance pattern `{pattern.pattern}`")

    if violations:
        print("[contract_handler_layout_boundary_guard] FAIL")
        for item in violations:
            print(item)
        return 1

    print("[contract_handler_layout_boundary_guard] PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())

