#!/usr/bin/env python3
"""Guard the Lite runtime opt-in envelope spec."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


REQUIRED_KEYS = {"contractMode", "contractVersion", "entryPoint", "clientType"}
ENTRY_POINTS = {"load_contract", "ui_contract", "api_onchange"}
CLIENT_TYPES = {"web_pc", "wx_mini", "harmony_h5"}


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--schema", required=True, type=Path)
    parser.add_argument("--example", required=True, type=Path)
    parser.add_argument("--plan", required=True, type=Path)
    args = parser.parse_args()

    errors: list[str] = []
    schema = load_json(args.schema)
    example = load_json(args.example)
    required = set(schema.get("required") or [])
    if required != REQUIRED_KEYS:
        errors.append(f"opt-in envelope required keys drifted: {sorted(required)}")
    properties = schema.get("properties") or {}
    if properties.get("contractMode", {}).get("const") != "lite_preview":
        errors.append("contractMode must be const lite_preview")
    if properties.get("contractVersion", {}).get("const") != "2.0.0":
        errors.append("contractVersion must be const 2.0.0")
    if set(properties.get("entryPoint", {}).get("enum") or []) != ENTRY_POINTS:
        errors.append("entryPoint enum drifted")
    if set(properties.get("clientType", {}).get("enum") or []) != CLIENT_TYPES:
        errors.append("clientType enum drifted")
    if properties.get("fallbackMode", {}).get("const") != "legacy_default":
        errors.append("fallbackMode must be const legacy_default")
    if schema.get("additionalProperties") is not False:
        errors.append("opt-in envelope schema must forbid additionalProperties")

    if example.get("contractMode") != "lite_preview":
        errors.append("example contractMode must be lite_preview")
    if example.get("contractVersion") != "2.0.0":
        errors.append("example contractVersion must be 2.0.0")
    if example.get("entryPoint") not in ENTRY_POINTS:
        errors.append("example entryPoint is not allowed")
    if example.get("clientType") not in CLIENT_TYPES:
        errors.append("example clientType is not allowed")
    if example.get("fallbackMode") != "legacy_default":
        errors.append("example fallbackMode must be legacy_default")

    plan_text = args.plan.read_text(encoding="utf-8")
    for token in ("opt-in only", "default response remains unchanged", "default ui.contract remains unchanged", "default onchange response remains unchanged"):
        if token not in plan_text:
            errors.append(f"integration plan missing opt-in token: {token}")

    if errors:
        print("Unified Semantic Page Contract Lite opt-in envelope guard failed:")
        for error in errors:
            print(f"- {error}")
        return 1

    print("Unified Semantic Page Contract Lite opt-in envelope guard passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
