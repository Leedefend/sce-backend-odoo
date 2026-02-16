#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

from pathlib import Path
import re
import sys


ROOT = Path(__file__).resolve().parents[2]
SCENE_CONTROLLER = ROOT / "addons/smart_construction_core/controllers/scene_controller.py"
LEGACY_CONTRACT = ROOT / "scripts/common/scene_legacy_contract.py"

REQUIRED_PATTERNS = (
    (r'"status"\s*:\s*"deprecated"', "missing deprecation.status=deprecated payload"),
    (r'"sunset_date"\s*:\s*_LEGACY_SCENES_SUNSET_DATE', "missing payload sunset_date constant wiring"),
    (r'\("Deprecation",\s*"true"\)', "missing Deprecation header"),
    (r'\("Sunset",\s*_LEGACY_SCENES_SUNSET_HTTP\)', "missing Sunset header constant wiring"),
    (r'\("X-Legacy-Endpoint",\s*_LEGACY_SCENES_ENDPOINT_NAME\)', "missing X-Legacy-Endpoint header"),
    (r'rel=\\"successor-version\\"', "missing successor-version Link header"),
    (r'_LEGACY_SCENES_SUCCESSOR\s*=\s*"([^"]+)"', "missing successor endpoint constant"),
    (r'_LEGACY_SCENES_SUNSET_DATE\s*=\s*"([^"]+)"', "missing sunset date constant"),
    (r'_LEGACY_SCENES_ENDPOINT_NAME\s*=\s*"([^"]+)"', "missing legacy endpoint name constant"),
    (r'fail\("AUTH_REQUIRED".*headers=_legacy_response_headers\(\)\)', "missing legacy headers on auth failure"),
    (r'fail\("SERVER_ERROR".*headers=_legacy_response_headers\(\)\)', "missing legacy headers on server error"),
)


def _has_pattern(pattern: str, text: str) -> bool:
    return bool(re.search(pattern, text, flags=re.MULTILINE | re.DOTALL))


def _extract_constant(text: str, name: str) -> str:
    match = re.search(rf'{re.escape(name)}\s*=\s*"([^"]+)"', text)
    return str(match.group(1) or "").strip() if match else ""


def main() -> int:
    if not SCENE_CONTROLLER.is_file():
        print("[scene_legacy_contract_guard] FAIL")
        print(f"missing file: {SCENE_CONTROLLER.as_posix()}")
        return 1
    if not LEGACY_CONTRACT.is_file():
        print("[scene_legacy_contract_guard] FAIL")
        print(f"missing file: {LEGACY_CONTRACT.as_posix()}")
        return 1

    text = SCENE_CONTROLLER.read_text(encoding="utf-8", errors="ignore")
    legacy_text = LEGACY_CONTRACT.read_text(encoding="utf-8", errors="ignore")
    violations: list[str] = []

    for pattern, message in REQUIRED_PATTERNS:
        if not _has_pattern(pattern, text):
            violations.append(message)

    controller_successor = _extract_constant(text, "_LEGACY_SCENES_SUCCESSOR")
    controller_sunset = _extract_constant(text, "_LEGACY_SCENES_SUNSET_DATE")
    controller_endpoint_name = _extract_constant(text, "_LEGACY_SCENES_ENDPOINT_NAME")
    contract_successor = _extract_constant(legacy_text, "LEGACY_SCENES_SUCCESSOR")
    contract_sunset = _extract_constant(legacy_text, "LEGACY_SCENES_SUNSET_DATE")
    contract_endpoint_name = _extract_constant(legacy_text, "LEGACY_SCENES_ENDPOINT_NAME")

    if not contract_successor:
        violations.append("missing LEGACY_SCENES_SUCCESSOR in scripts/common/scene_legacy_contract.py")
    if not contract_sunset:
        violations.append("missing LEGACY_SCENES_SUNSET_DATE in scripts/common/scene_legacy_contract.py")
    if not contract_endpoint_name:
        violations.append("missing LEGACY_SCENES_ENDPOINT_NAME in scripts/common/scene_legacy_contract.py")
    if controller_successor and contract_successor and controller_successor != contract_successor:
        violations.append(
            f"successor constant mismatch: controller={controller_successor} common={contract_successor}"
        )
    if controller_sunset and contract_sunset and controller_sunset != contract_sunset:
        violations.append(
            f"sunset date constant mismatch: controller={controller_sunset} common={contract_sunset}"
        )
    if controller_endpoint_name and contract_endpoint_name and controller_endpoint_name != contract_endpoint_name:
        violations.append(
            "endpoint name constant mismatch: "
            f"controller={controller_endpoint_name} common={contract_endpoint_name}"
        )

    if violations:
        print("[scene_legacy_contract_guard] FAIL")
        for item in violations:
            print(item)
        return 1

    print("[scene_legacy_contract_guard] PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
