#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[2]
LIST_PROJECTION = ROOT / "addons/smart_core/app_config_engine/capability/projection/capability_list_projection.py"
RUNTIME_EXPOSURE = ROOT / "addons/smart_core/app_config_engine/capability/projection/capability_runtime_exposure.py"


def _read(path: Path) -> str:
    if not path.is_file():
        return ""
    return path.read_text(encoding="utf-8", errors="ignore")


def main() -> int:
    violations: list[str] = []

    list_text = _read(LIST_PROJECTION)
    exposure_text = _read(RUNTIME_EXPOSURE)

    if not list_text:
        violations.append("capability list projection missing")
    if not exposure_text:
        violations.append("runtime exposure resolver missing")

    required_projection_fields = (
        '"access_mode":',
        '"release_tier":',
        '"lifecycle_status":',
        '"primary_intent":',
        '"runtime_target":',
    )
    for token in required_projection_fields:
        if token not in list_text:
            violations.append(f"capability list projection missing field token: {token}")

    if "resolve_primary_intent(row)" not in list_text:
        violations.append("capability list projection missing resolve_primary_intent usage")
    if "resolve_runtime_target(row)" not in list_text:
        violations.append("capability list projection missing resolve_runtime_target usage")

    if "if explicit:" not in exposure_text or "return explicit" not in exposure_text:
        violations.append("runtime exposure resolver must preserve explicit primary_intent for non-native capabilities")

    # non-native guard: projection layer should not hardcode non-native type branches
    disallowed_non_native_tokens = (
        "platform_entry",
        "platform_operation",
    )
    for token in disallowed_non_native_tokens:
        if token in exposure_text:
            violations.append(f"runtime exposure resolver must not hardcode non-native token: {token}")

    if violations:
        print("[verify.architecture.non_native_capability_binding_policy_parity_guard] FAIL")
        for item in violations:
            print(item)
        return 1

    print("[verify.architecture.non_native_capability_binding_policy_parity_guard] PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())

