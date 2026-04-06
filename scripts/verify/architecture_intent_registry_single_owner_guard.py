#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[2]
TARGET = ROOT / "addons/smart_construction_core/core_extension.py"


def main() -> int:
    text = TARGET.read_text(encoding="utf-8", errors="ignore") if TARGET.is_file() else ""
    violations = []
    if "registry[" in text:
        violations.append("direct registry[...] assignment remains in smart_construction_core/core_extension.py")
    if "def get_intent_handler_contributions(" not in text:
        violations.append("get_intent_handler_contributions provider missing")

    if violations:
        print("[verify.architecture.intent_registry_single_owner_guard] FAIL")
        for item in violations:
            print(item)
        return 1
    print("[verify.architecture.intent_registry_single_owner_guard] PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())

