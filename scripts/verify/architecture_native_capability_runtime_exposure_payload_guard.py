#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[2]
RUNTIME_EXPOSURE = ROOT / "addons/smart_core/app_config_engine/capability/projection/capability_runtime_exposure.py"
LIST_PROJECTION = ROOT / "addons/smart_core/app_config_engine/capability/projection/capability_list_projection.py"
WORKSPACE_PROJECTION = ROOT / "addons/smart_core/app_config_engine/capability/projection/workspace_projection.py"


def _read(path: Path) -> str:
    if not path.is_file():
        return ""
    return path.read_text(encoding="utf-8", errors="ignore")


def main() -> int:
    violations: list[str] = []

    runtime_text = _read(RUNTIME_EXPOSURE)
    list_text = _read(LIST_PROJECTION)
    workspace_text = _read(WORKSPACE_PROJECTION)

    if not runtime_text:
        violations.append("missing capability_runtime_exposure.py")
    if not list_text:
        violations.append("missing capability_list_projection.py")
    if not workspace_text:
        violations.append("missing workspace_projection.py")

    if "def resolve_runtime_target(" not in runtime_text:
        violations.append("runtime exposure resolver missing resolve_runtime_target")
    if "\"mode\"" not in runtime_text:
        violations.append("runtime exposure resolver missing runtime_target mode field")

    if "\"primary_intent\": primary_intent" not in list_text:
        violations.append("capability list projection missing primary_intent output")
    if "\"runtime_target\": runtime_target" not in list_text:
        violations.append("capability list projection missing runtime_target output")

    if "\"primary_intent\": primary_intent" not in workspace_text:
        violations.append("workspace projection missing primary_intent output")
    if "\"runtime_target\": runtime_target" not in workspace_text:
        violations.append("workspace projection missing runtime_target output")

    if violations:
        print("[verify.architecture.native_capability_runtime_exposure_payload_guard] FAIL")
        for item in violations:
            print(item)
        return 1

    print("[verify.architecture.native_capability_runtime_exposure_payload_guard] PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())

