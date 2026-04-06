#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[2]
TARGET = ROOT / "addons/smart_construction_core/core_extension.py"
LOADER = ROOT / "addons/smart_core/core/extension_loader.py"


def main() -> int:
    text = TARGET.read_text(encoding="utf-8", errors="ignore") if TARGET.is_file() else ""
    loader_text = LOADER.read_text(encoding="utf-8", errors="ignore") if LOADER.is_file() else ""
    violations = []
    if "registry[" in text:
        violations.append("direct registry[...] assignment remains in smart_construction_core/core_extension.py")
    if "def get_intent_handler_contributions(" not in text:
        violations.append("get_intent_handler_contributions provider missing")
    if "smart_core_register" in loader_text:
        violations.append("extension_loader still contains legacy smart_core_register fallback")

    for path in ROOT.glob("addons/*/core_extension.py"):
        content = path.read_text(encoding="utf-8", errors="ignore")
        if "def smart_core_register(" in content:
            violations.append(f"legacy smart_core_register provider remains: {path.relative_to(ROOT).as_posix()}")

    if violations:
        print("[verify.architecture.intent_registry_single_owner_guard] FAIL")
        for item in violations:
            print(item)
        return 1
    print("[verify.architecture.intent_registry_single_owner_guard] PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
