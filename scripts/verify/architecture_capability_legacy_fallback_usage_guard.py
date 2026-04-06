#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[2]
PROVIDER = ROOT / "addons/smart_core/core/capability_provider.py"


def _contains_after(text: str, anchor: str, needle: str) -> bool:
    anchor_index = text.find(anchor)
    if anchor_index < 0:
        return False
    return text.find(needle, anchor_index) >= 0


def main() -> int:
    provider_text = PROVIDER.read_text(encoding="utf-8", errors="ignore") if PROVIDER.is_file() else ""
    violations = []

    if "def _capability_legacy_fallback_enabled(" not in provider_text:
        violations.append("capability_provider missing explicit legacy fallback toggle helper")
    if "smart_core.capability_legacy_fallback_enabled" not in provider_text:
        violations.append("capability_provider missing legacy fallback config key")
    if "smart_core.capability_registry_query_v2_enabled" in provider_text:
        violations.append("obsolete capability_registry_query_v2 toggle still present")

    if "CapabilityQueryService(platform_owner=\"smart_core\")" not in provider_text:
        violations.append("capability_provider missing platform CapabilityQueryService path")

    if not _contains_after(provider_text, "def load_capabilities_for_user", "legacy_fallback_enabled = _capability_legacy_fallback_enabled(env)"):
        violations.append("load_capabilities_for_user missing legacy_fallback_enabled guard variable")

    if not _contains_after(provider_text, "def load_capabilities_for_user", "if runtime_caps or not legacy_fallback_enabled:"):
        violations.append("query path does not enforce no-fallback behavior when legacy toggle disabled")

    if not _contains_after(provider_text, "def load_capabilities_for_user", "if not legacy_fallback_enabled:"):
        violations.append("exception path does not short-circuit to empty when legacy toggle disabled")

    if violations:
        print("[verify.architecture.capability_legacy_fallback_usage_guard] FAIL")
        for item in violations:
            print(item)
        return 1

    print("[verify.architecture.capability_legacy_fallback_usage_guard] PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
