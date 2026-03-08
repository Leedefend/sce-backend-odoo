#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Guard: parse layer must not perform runtime governance."""

from __future__ import annotations

import re
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
TARGET_PATHS = [
    ROOT / "addons" / "smart_core" / "view",
    ROOT / "addons" / "smart_core" / "app_config_engine" / "services" / "view_Parser",
    ROOT / "addons" / "smart_core" / "app_config_engine" / "services" / "native_parse_service.py",
    ROOT / "addons" / "smart_core" / "app_config_engine" / "services" / "parse_fallback_service.py",
]
EXCLUDED_RELATIVE_PATHS = {
    # Legacy semantic parser keeps permission projection and is outside v1 parse pipeline.
    "addons/smart_core/view/universal_parser.py",
}

FORBIDDEN_PATTERNS = [
    re.compile(r"\bapply_contract_governance\s*\("),
    re.compile(r"\bcontract_mode\b"),
    re.compile(r"\bcontract_surface\b"),
    re.compile(r"\bgoverned_from_native\b"),
    re.compile(r"\bsurface_mapping\b"),
    re.compile(r"\bcheck_access_rights\s*\("),
    re.compile(r"\b_runtime_filter\b"),
]


def _iter_py_files(path: Path):
    if path.is_file() and path.suffix == ".py":
        yield path
        return
    if path.is_dir():
        yield from path.rglob("*.py")


def main() -> int:
    violations: list[str] = []
    for path in TARGET_PATHS:
        for py in _iter_py_files(path):
            rel = py.relative_to(ROOT).as_posix()
            if rel in EXCLUDED_RELATIVE_PATHS:
                continue
            text = py.read_text(encoding="utf-8", errors="ignore")
            for pattern in FORBIDDEN_PATTERNS:
                if pattern.search(text):
                    violations.append(f"{rel}: forbidden parse-layer runtime governance pattern `{pattern.pattern}`")

    if violations:
        print("[contract_parse_boundary_guard] FAIL")
        for item in violations:
            print(item)
        return 1

    print("[contract_parse_boundary_guard] PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
