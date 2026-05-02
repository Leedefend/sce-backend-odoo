#!/usr/bin/env python3
"""Guard api.onchange Lite opt-in preview remains narrow and non-default."""

from __future__ import annotations

import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
HANDLER = ROOT / "addons" / "smart_core" / "handlers" / "api_onchange.py"
PREVIEW_CORE = ROOT / "addons" / "smart_core" / "core" / "unified_page_contract_lite_preview.py"


REQUIRED_HANDLER_TOKENS = (
    "from ..core.unified_page_contract_lite_preview import with_lite_preview_if_requested",
    'return with_lite_preview_if_requested(response, params, "api_onchange")',
)
REQUIRED_CORE_TOKENS = (
    "from .unified_page_contract_lite_adapter import build_lite_contract, build_lite_patch",
    "from .unified_page_contract_lite_patch_normalizer import normalize_lite_patch_source",
    "from .unified_page_contract_lite_source_normalizer import normalize_lite_contract_source",
    'LITE_PREVIEW_CONTRACT_MODE = "lite_preview"',
    'LITE_PREVIEW_CONTRACT_VERSION = "2.0.0"',
    'LITE_PREVIEW_FALLBACK_MODE = "legacy_default"',
    "def is_lite_preview_request(params: Dict[str, Any], entry_point: str) -> bool:",
    "def with_lite_preview_if_requested(",
    'params.get("contractMode") == LITE_PREVIEW_CONTRACT_MODE',
    'params.get("contractVersion") == LITE_PREVIEW_CONTRACT_VERSION',
    'params.get("entryPoint") == entry_point',
    'params.get("fallbackMode", LITE_PREVIEW_FALLBACK_MODE) == LITE_PREVIEW_FALLBACK_MODE',
    "payload_type: str = \"lite_patch\"",
    "out[\"lite_preview\"] = build_lite_preview_envelope(",
)
FORBIDDEN_TOKENS = (
    'params.get("contractMode") == "lite"',
    'params.get("contractMode") in',
    'params.get("contractVersion")',
    'entryPoint") == "ui_contract"',
    'entryPoint") == "load_contract"',
)


def main() -> int:
    handler_text = HANDLER.read_text(encoding="utf-8")
    core_text = PREVIEW_CORE.read_text(encoding="utf-8")
    errors: list[str] = []
    for token in REQUIRED_HANDLER_TOKENS:
        if token not in handler_text:
            errors.append(f"handler missing required token: {token}")
    for token in REQUIRED_CORE_TOKENS:
        if token not in core_text:
            errors.append(f"preview core missing required token: {token}")
    # Only the exact 2.0.0 equality is allowed for contractVersion.
    if core_text.count('params.get("contractVersion") == LITE_PREVIEW_CONTRACT_VERSION') != 1:
        errors.append("contractVersion must be checked exactly once against the Lite preview constant")
    if core_text.count('LITE_PREVIEW_CONTRACT_VERSION = "2.0.0"') != 1:
        errors.append("Lite preview contract version constant must be exactly 2.0.0")
    for token in FORBIDDEN_TOKENS:
        if token == 'params.get("contractVersion")':
            continue
        if token in handler_text or token in core_text:
            errors.append(f"forbidden broad opt-in token: {token}")
    combined_text = handler_text + "\n" + core_text
    if "login" in combined_text or "system.init" in combined_text or "ui.contract" in combined_text:
        errors.append("api.onchange Lite preview must not reference startup chain outputs")
    if errors:
        print("Unified Semantic Page Contract Lite api.onchange preview guard failed:")
        for error in errors:
            print(f"- {error}")
        return 1
    print("Unified Semantic Page Contract Lite api.onchange preview guard passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
