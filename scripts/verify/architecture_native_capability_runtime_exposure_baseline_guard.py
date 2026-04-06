#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[2]
CENTRAL = ROOT / "addons/smart_core/app_config_engine/capability/projection/capability_runtime_exposure.py"
LIST_PROJECTION = ROOT / "addons/smart_core/app_config_engine/capability/projection/capability_list_projection.py"
WORKSPACE_PROJECTION = ROOT / "addons/smart_core/app_config_engine/capability/projection/workspace_projection.py"
QUERY_SERVICE = ROOT / "addons/smart_core/app_config_engine/capability/services/capability_query_service.py"
RUNTIME_SERVICE = ROOT / "addons/smart_core/app_config_engine/capability/services/capability_runtime_service.py"


NATIVE_TYPE_TOKENS = (
    "native_menu_entry",
    "native_window_action",
    "native_model_access",
    "native_server_action",
    "native_report_action",
    "native_view_binding",
)


def _read(path: Path) -> str:
    if not path.is_file():
        return ""
    return path.read_text(encoding="utf-8", errors="ignore")


def main() -> int:
    violations: list[str] = []

    central_text = _read(CENTRAL)
    list_text = _read(LIST_PROJECTION)
    workspace_text = _read(WORKSPACE_PROJECTION)
    query_text = _read(QUERY_SERVICE)
    runtime_text = _read(RUNTIME_SERVICE)

    if not central_text:
        violations.append("missing central runtime exposure resolver")
    if "NATIVE_PRIMARY_INTENT_BASELINE" not in central_text:
        violations.append("central resolver missing NATIVE_PRIMARY_INTENT_BASELINE")
    if "def resolve_primary_intent(" not in central_text:
        violations.append("central resolver missing resolve_primary_intent")
    if "def resolve_runtime_target(" not in central_text:
        violations.append("central resolver missing resolve_runtime_target")

    for token in NATIVE_TYPE_TOKENS:
        if token not in central_text:
            violations.append(f"central baseline missing native type token: {token}")

    if "from .capability_runtime_exposure import resolve_primary_intent, resolve_runtime_target" not in list_text:
        violations.append("capability_list_projection missing centralized runtime exposure import")
    if "resolve_primary_intent(row)" not in list_text:
        violations.append("capability_list_projection missing resolve_primary_intent usage")
    if "resolve_runtime_target(row)" not in list_text:
        violations.append("capability_list_projection missing resolve_runtime_target usage")

    if "from .capability_runtime_exposure import resolve_primary_intent, resolve_runtime_target" not in workspace_text:
        violations.append("workspace_projection missing centralized runtime exposure import")
    if "resolve_primary_intent(row)" not in workspace_text:
        violations.append("workspace_projection missing resolve_primary_intent usage")
    if "resolve_runtime_target(row)" not in workspace_text:
        violations.append("workspace_projection missing resolve_runtime_target usage")

    for token in NATIVE_TYPE_TOKENS:
        if token in list_text:
            violations.append(f"capability_list_projection must not hardcode native type token: {token}")
        if token in workspace_text:
            violations.append(f"workspace_projection must not hardcode native type token: {token}")
        if token in query_text:
            violations.append(f"capability_query_service must not hardcode native type token: {token}")
        if token in runtime_text:
            violations.append(f"capability_runtime_service must not hardcode native type token: {token}")

    if violations:
        print("[verify.architecture.native_capability_runtime_exposure_baseline_guard] FAIL")
        for item in violations:
            print(item)
        return 1

    print("[verify.architecture.native_capability_runtime_exposure_baseline_guard] PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())

