#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[2]
NATIVE_DIR = ROOT / "addons/smart_core/app_config_engine/capability/native"
SERVICE = NATIVE_DIR / "native_projection_service.py"
SCHEMA = ROOT / "addons/smart_core/app_config_engine/capability/schema/capability_schema.py"


def _read(path: Path) -> str:
    if not path.is_file():
        return ""
    return path.read_text(encoding="utf-8", errors="ignore")


def main() -> int:
    violations: list[str] = []

    required_files = [
        NATIVE_DIR / "menu_adapter.py",
        NATIVE_DIR / "action_adapter.py",
        NATIVE_DIR / "model_adapter.py",
        NATIVE_DIR / "server_action_adapter.py",
        NATIVE_DIR / "report_adapter.py",
        NATIVE_DIR / "view_binding_adapter.py",
        SERVICE,
    ]
    for path in required_files:
        if not path.is_file():
            violations.append(f"missing native adapter file: {path.relative_to(ROOT).as_posix()}")

    service_text = _read(SERVICE)
    schema_text = _read(SCHEMA)

    required_projection_calls = (
        "project_menu_capabilities",
        "project_window_action_capabilities",
        "project_model_access_capabilities",
        "project_server_action_capabilities",
        "project_report_action_capabilities",
        "project_view_binding_capabilities",
    )
    for token in required_projection_calls:
        if token not in service_text:
            violations.append(f"native projection service missing projection call: {token}")

    required_types = (
        "native_menu_entry",
        "native_window_action",
        "native_model_access",
        "native_server_action",
        "native_report_action",
        "native_view_binding",
    )
    for token in required_types:
        if token not in schema_text:
            violations.append(f"capability schema missing native type: {token}")

    if violations:
        print("[verify.architecture.native_capability_ingestion_lint_bundle] FAIL")
        for item in violations:
            print(item)
        return 1

    print("[verify.architecture.native_capability_ingestion_lint_bundle] PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())

