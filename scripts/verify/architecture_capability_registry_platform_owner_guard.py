#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[2]
PROVIDER = ROOT / "addons/smart_core/core/capability_provider.py"
LOADER = ROOT / "addons/smart_core/core/capability_contribution_loader.py"


def main() -> int:
    provider_text = PROVIDER.read_text(encoding="utf-8", errors="ignore") if PROVIDER.is_file() else ""
    loader_text = LOADER.read_text(encoding="utf-8", errors="ignore") if LOADER.is_file() else ""
    violations = []

    if "collect_capability_contributions" not in provider_text:
        violations.append("capability_provider missing collect_capability_contributions path")
    if "def collect_capability_contributions(" not in loader_text:
        violations.append("capability contribution loader missing")
    if "smart_core_list_capabilities_for_user" in provider_text or "smart_core_capability_groups" in provider_text:
        violations.append("legacy capability runtime hooks remain in capability_provider")
    if "smart_core_list_capabilities_for_user" in loader_text or "smart_core_capability_groups" in loader_text:
        violations.append("legacy capability runtime hooks remain in capability_contribution_loader")

    if violations:
        print("[verify.architecture.capability_registry_platform_owner_guard] FAIL")
        for item in violations:
            print(item)
        return 1
    print("[verify.architecture.capability_registry_platform_owner_guard] PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
