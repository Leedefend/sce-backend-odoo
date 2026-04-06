#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[2]
NATIVE_SERVICE = ROOT / "addons/smart_core/app_config_engine/capability/native/native_projection_service.py"
MODEL_ADAPTER = ROOT / "addons/smart_core/app_config_engine/capability/native/model_adapter.py"
LOADER = ROOT / "addons/smart_core/app_config_engine/capability/core/contribution_loader.py"
SCHEMA = ROOT / "addons/smart_core/app_config_engine/capability/schema/capability_schema.py"


def _read(path: Path) -> str:
    if not path.is_file():
        return ""
    return path.read_text(encoding="utf-8", errors="ignore")


def main() -> int:
    violations: list[str] = []

    service_text = _read(NATIVE_SERVICE)
    adapter_text = _read(MODEL_ADAPTER)
    loader_text = _read(LOADER)
    schema_text = _read(SCHEMA)

    if not service_text:
        violations.append("native projection service missing")
    if not adapter_text:
        violations.append("model adapter missing")
    if not loader_text:
        violations.append("capability contribution loader missing")
    if not schema_text:
        violations.append("capability schema missing")

    required_service_tokens = (
        "project_model_access_capabilities",
        "smart_core.native.model",
    )
    for token in required_service_tokens:
        if token not in service_text:
            violations.append(f"native projection service missing token: {token}")

    if "def project_model_access_capabilities(" not in adapter_text:
        violations.append("model adapter missing project_model_access_capabilities")
    if "ir.model.access" not in adapter_text:
        violations.append("model adapter missing ir.model.access projection source")

    if "load_native_capability_rows" not in loader_text:
        violations.append("contribution loader missing native ingestion call")
    if "source_module=\"smart_core.native\"" not in loader_text:
        violations.append("native row normalization source module binding missing")

    if "native_model_access" not in schema_text:
        violations.append("capability schema missing native_model_access type")

    if violations:
        print("[verify.architecture.native_capability_ingestion_guard] FAIL")
        for item in violations:
            print(item)
        return 1

    print("[verify.architecture.native_capability_ingestion_guard] PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())

