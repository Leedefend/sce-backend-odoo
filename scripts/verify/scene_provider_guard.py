#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

from pathlib import Path
import re
import sys


ROOT = Path(__file__).resolve().parents[2]
PROVIDER = ROOT / "addons/smart_core/core/scene_provider.py"

REQUIRED_SYMBOLS = (
    "resolve_scene_channel",
    "load_scene_contract",
    "merge_missing_scenes_from_registry",
    "load_scenes_from_db_or_fallback",
)

FORBIDDEN_IMPORT_RE = re.compile(r"(?:from\s+odoo\.addons\.smart_construction_core)")


def main() -> int:
    if not PROVIDER.is_file():
        print("[scene_provider_guard] FAIL")
        print(f"missing file: {PROVIDER.as_posix()}")
        return 1

    text = PROVIDER.read_text(encoding="utf-8", errors="ignore")
    violations: list[str] = []

    for symbol in REQUIRED_SYMBOLS:
        if f"def {symbol}(" not in text:
            violations.append(f"missing provider symbol: {symbol}")

    if FORBIDDEN_IMPORT_RE.search(text):
        violations.append("scene_provider must not import smart_construction_core")

    if violations:
        print("[scene_provider_guard] FAIL")
        for item in violations:
            print(item)
        return 1

    print("[scene_provider_guard] PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())

