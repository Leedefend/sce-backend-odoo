#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Guard: scene orchestration must consume governed contracts, not parser/XML internals."""

from __future__ import annotations

import re
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
TARGET_PATHS = [
    ROOT / "addons" / "smart_core" / "core",
    ROOT / "addons" / "smart_core" / "handlers",
    ROOT / "addons" / "smart_construction_core" / "controllers",
]

FILE_INCLUDE_RE = re.compile(r"(scene|system_init|catalog|orchestr|provider)", re.IGNORECASE)
FORBIDDEN_PATTERNS = [
    re.compile(r"app\.view\.parser"),
    re.compile(r"\bfields_view_get\s*\("),
    re.compile(r"\bget_view\s*\("),
    re.compile(r"xml\.etree"),
    re.compile(r"ET\.fromstring\s*\("),
]

ALLOWLIST = {
    # View parser/contract generation layer is expected to access get_view/fields_view_get.
    "addons/smart_core/handlers/ui_contract.py",
}


def _iter_py(path: Path):
    if path.is_file() and path.suffix == ".py":
        yield path
        return
    if path.is_dir():
        yield from path.rglob("*.py")


def main() -> int:
    violations: list[str] = []
    for root in TARGET_PATHS:
        for py in _iter_py(root):
            rel = py.relative_to(ROOT).as_posix()
            if rel in ALLOWLIST:
                continue
            if not FILE_INCLUDE_RE.search(py.name):
                continue
            text = py.read_text(encoding="utf-8", errors="ignore")
            for pattern in FORBIDDEN_PATTERNS:
                if pattern.search(text):
                    violations.append(f"{rel}: forbidden scene-input boundary pattern `{pattern.pattern}`")

    if violations:
        print("[scene_input_boundary_guard] FAIL")
        for item in violations:
            print(item)
        return 1

    print("[scene_input_boundary_guard] PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

