#!/usr/bin/env python3
"""Guard the Lite runtime opt-in response envelope spec."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


REQUIRED_KEYS = {"contractMode", "contractVersion", "entryPoint", "payloadType", "fallbackMode", "payload", "meta"}
ENTRY_POINTS = {"load_contract", "ui_contract", "api_onchange"}
PAYLOAD_TYPES = {"lite_contract", "lite_patch"}


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--schema", required=True, type=Path)
    parser.add_argument("--example", required=True, type=Path)
    parser.add_argument("--request-schema", required=True, type=Path)
    args = parser.parse_args()

    errors: list[str] = []
    schema = load_json(args.schema)
    example = load_json(args.example)
    request_schema = load_json(args.request_schema)

    if set(schema.get("required") or []) != REQUIRED_KEYS:
        errors.append("response envelope required keys drifted")
    properties = schema.get("properties") or {}
    if properties.get("contractMode", {}).get("const") != "lite_preview":
        errors.append("response contractMode must be const lite_preview")
    if properties.get("contractVersion", {}).get("const") != "2.0.0":
        errors.append("response contractVersion must be const 2.0.0")
    if set(properties.get("entryPoint", {}).get("enum") or []) != ENTRY_POINTS:
        errors.append("response entryPoint enum drifted")
    if set(properties.get("payloadType", {}).get("enum") or []) != PAYLOAD_TYPES:
        errors.append("response payloadType enum drifted")
    if properties.get("fallbackMode", {}).get("const") != "legacy_default":
        errors.append("response fallbackMode must be const legacy_default")
    meta_props = (properties.get("meta") or {}).get("properties") or {}
    if meta_props.get("previewOnly", {}).get("const") is not True:
        errors.append("response meta.previewOnly must be const true")
    if meta_props.get("defaultUnchanged", {}).get("const") is not True:
        errors.append("response meta.defaultUnchanged must be const true")
    if schema.get("additionalProperties") is not False:
        errors.append("response envelope schema must forbid additionalProperties")

    request_props = request_schema.get("properties") or {}
    if request_props.get("contractMode", {}).get("const") != properties.get("contractMode", {}).get("const"):
        errors.append("request/response contractMode mismatch")
    if request_props.get("contractVersion", {}).get("const") != properties.get("contractVersion", {}).get("const"):
        errors.append("request/response contractVersion mismatch")
    if set(request_props.get("entryPoint", {}).get("enum") or []) != set(properties.get("entryPoint", {}).get("enum") or []):
        errors.append("request/response entryPoint enum mismatch")
    if request_props.get("fallbackMode", {}).get("const") != properties.get("fallbackMode", {}).get("const"):
        errors.append("request/response fallbackMode mismatch")

    if example.get("contractMode") != "lite_preview":
        errors.append("example contractMode must be lite_preview")
    if example.get("contractVersion") != "2.0.0":
        errors.append("example contractVersion must be 2.0.0")
    if example.get("entryPoint") not in ENTRY_POINTS:
        errors.append("example entryPoint is not allowed")
    if example.get("payloadType") not in PAYLOAD_TYPES:
        errors.append("example payloadType is not allowed")
    if example.get("fallbackMode") != "legacy_default":
        errors.append("example fallbackMode must be legacy_default")
    meta = example.get("meta") if isinstance(example.get("meta"), dict) else {}
    if meta.get("previewOnly") is not True or meta.get("defaultUnchanged") is not True:
        errors.append("example meta must mark previewOnly/defaultUnchanged true")

    if errors:
        print("Unified Semantic Page Contract Lite opt-in response guard failed:")
        for error in errors:
            print(f"- {error}")
        return 1

    print("Unified Semantic Page Contract Lite opt-in response guard passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
