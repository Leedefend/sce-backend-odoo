#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

from pathlib import Path
import re
import sys


ROOT = Path(__file__).resolve().parents[2]
TARGET = ROOT / "addons/smart_construction_core/core_extension.py"
PATTERN = re.compile(r"^def\s+smart_core_[a-zA-Z0-9_]*\s*\(", re.MULTILINE)


def main() -> int:
    text = TARGET.read_text(encoding="utf-8", errors="ignore") if TARGET.is_file() else ""
    matches = PATTERN.findall(text)
    if matches:
        print("[verify.architecture.industry_legacy_bridge_residue_guard] FAIL")
        print("legacy smart_core_* exports remain in smart_construction_core/core_extension.py")
        for item in matches:
            print(item.strip())
        return 1
    print("[verify.architecture.industry_legacy_bridge_residue_guard] PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())

