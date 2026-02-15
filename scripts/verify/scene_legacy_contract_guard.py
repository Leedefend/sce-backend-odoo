#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

from pathlib import Path
import re
import sys


ROOT = Path(__file__).resolve().parents[2]
SCENE_CONTROLLER = ROOT / "addons/smart_construction_core/controllers/scene_controller.py"

REQUIRED_PATTERNS = (
    (r'"status"\s*:\s*"deprecated"', "missing deprecation.status=deprecated payload"),
    (r'"sunset_date"\s*:\s*_LEGACY_SCENES_SUNSET_DATE', "missing payload sunset_date constant wiring"),
    (r'\("Deprecation",\s*"true"\)', "missing Deprecation header"),
    (r'\("Sunset",\s*_LEGACY_SCENES_SUNSET_HTTP\)', "missing Sunset header constant wiring"),
    (r'rel=\\"successor-version\\"', "missing successor-version Link header"),
    (r'_LEGACY_SCENES_SUCCESSOR\s*=\s*"/api/v1/intent"', "unexpected successor endpoint"),
    (r'_LEGACY_SCENES_SUNSET_DATE\s*=\s*"2026-04-30"', "unexpected sunset date constant"),
)


def main() -> int:
    if not SCENE_CONTROLLER.is_file():
        print("[scene_legacy_contract_guard] FAIL")
        print(f"missing file: {SCENE_CONTROLLER.as_posix()}")
        return 1

    text = SCENE_CONTROLLER.read_text(encoding="utf-8", errors="ignore")
    violations: list[str] = []

    for pattern, message in REQUIRED_PATTERNS:
        if not re.search(pattern, text):
            violations.append(message)

    if violations:
        print("[scene_legacy_contract_guard] FAIL")
        for item in violations:
            print(item)
        return 1

    print("[scene_legacy_contract_guard] PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
