#!/usr/bin/env python3
"""Guard negative cases for Lite runtime opt-in detection."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


ENTRY_POINTS = {"load_contract", "ui_contract", "api_onchange"}
CLIENT_TYPES = {"web_pc", "wx_mini", "harmony_h5"}


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def is_lite_preview(payload: Any) -> bool:
    if not isinstance(payload, dict):
        return False
    return (
        payload.get("contractMode") == "lite_preview"
        and payload.get("contractVersion") == "2.0.0"
        and payload.get("entryPoint") in ENTRY_POINTS
        and payload.get("clientType") in CLIENT_TYPES
        and payload.get("fallbackMode", "legacy_default") == "legacy_default"
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--positive", required=True, type=Path)
    parser.add_argument("--negative", action="append", required=True, type=Path)
    args = parser.parse_args()

    errors: list[str] = []
    positive = load_json(args.positive)
    if not is_lite_preview(positive):
        errors.append(f"positive fixture is not detected as lite preview: {args.positive}")
    for path in args.negative:
        payload = load_json(path)
        if is_lite_preview(payload):
            errors.append(f"negative fixture incorrectly detected as lite preview: {path}")

    if errors:
        print("Unified Semantic Page Contract Lite opt-in negative guard failed:")
        for error in errors:
            print(f"- {error}")
        return 1

    print("Unified Semantic Page Contract Lite opt-in negative guard passed")
    print(f"- negative cases: {len(args.negative)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
