#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[2]
MERGER = ROOT / "addons/smart_core/core/system_init_extension_fact_merger.py"
HANDLER = ROOT / "addons/smart_core/handlers/system_init.py"
RUNTIME_FETCH = ROOT / "addons/smart_core/core/runtime_fetch_bootstrap_helper.py"
CORE_EXT = ROOT / "addons/smart_construction_core/core_extension.py"


def main() -> int:
    merger_text = MERGER.read_text(encoding="utf-8", errors="ignore") if MERGER.is_file() else ""
    handler_text = HANDLER.read_text(encoding="utf-8", errors="ignore") if HANDLER.is_file() else ""
    runtime_fetch_text = RUNTIME_FETCH.read_text(encoding="utf-8", errors="ignore") if RUNTIME_FETCH.is_file() else ""
    ext_text = CORE_EXT.read_text(encoding="utf-8", errors="ignore") if CORE_EXT.is_file() else ""

    violations = []
    if "def apply_extension_fact_contributions(" not in merger_text:
        violations.append("system_init extension fact collector missing")
    if "apply_extension_fact_contributions(data, env, user" not in handler_text:
        violations.append("system_init handler missing contribution collector wiring")
    if "def get_system_init_fact_contributions(" not in ext_text:
        violations.append("industry provider get_system_init_fact_contributions missing")
    if "smart_core_extend_system_init" in handler_text:
        violations.append("system_init handler still executes smart_core_extend_system_init legacy hook")
    if "smart_core_extend_system_init" in runtime_fetch_text:
        violations.append("runtime_fetch helper still executes smart_core_extend_system_init legacy hook")

    if violations:
        print("[verify.architecture.system_init_extension_protocol_guard] FAIL")
        for item in violations:
            print(item)
        return 1
    print("[verify.architecture.system_init_extension_protocol_guard] PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
