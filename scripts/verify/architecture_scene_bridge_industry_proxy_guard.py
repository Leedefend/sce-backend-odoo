#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[2]
SCENE_PROVIDER = ROOT / "addons/smart_core/core/scene_registry_provider.py"
SCENE_PACKAGE = ROOT / "addons/smart_core/handlers/scene_package.py"
SCENE_GOV = ROOT / "addons/smart_core/handlers/scene_governance.py"


def main() -> int:
    provider_text = SCENE_PROVIDER.read_text(encoding="utf-8", errors="ignore") if SCENE_PROVIDER.is_file() else ""
    package_text = SCENE_PACKAGE.read_text(encoding="utf-8", errors="ignore") if SCENE_PACKAGE.is_file() else ""
    gov_text = SCENE_GOV.read_text(encoding="utf-8", errors="ignore") if SCENE_GOV.is_file() else ""

    violations = []
    if "smart_construction_scene.scene_registry" not in provider_text:
        violations.append("scene_registry_provider missing direct scene_registry import path")
    if any(
        token in provider_text
        for token in (
            "smart_core_load_scene_configs",
            "smart_core_has_db_scenes",
            "smart_core_get_scene_version",
            "smart_core_get_schema_version",
            "call_extension_hook_first",
        )
    ):
        violations.append("scene_registry_provider still contains legacy smart_core_scene_* fallback hooks")
    if "smart_construction_scene.services.scene_package_service" not in package_text:
        violations.append("scene_package handler missing direct scene package service path")
    if "smart_construction_scene.services.scene_governance_service" not in gov_text:
        violations.append("scene_governance handler missing direct scene governance service path")

    if violations:
        print("[verify.architecture.scene_bridge_industry_proxy_guard] FAIL")
        for item in violations:
            print(item)
        return 1
    print("[verify.architecture.scene_bridge_industry_proxy_guard] PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
