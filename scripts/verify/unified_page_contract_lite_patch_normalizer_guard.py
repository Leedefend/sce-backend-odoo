#!/usr/bin/env python3
"""Guard the offline Lite patch normalizer."""

from __future__ import annotations

import argparse
import importlib.util
import json
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
NORMALIZER = ROOT / "addons" / "smart_core" / "core" / "unified_page_contract_lite_patch_normalizer.py"
FORBIDDEN_TOKENS = (
    "BaseIntentHandler",
    "INTENT_TYPE",
    "request",
    "from odoo",
    "import odoo",
    "env[",
    ".sudo(",
    ".search(",
    ".write(",
    ".create(",
    ".unlink(",
)


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def load_normalizer():
    spec = importlib.util.spec_from_file_location("unified_page_contract_lite_patch_normalizer_guard_target", NORMALIZER)
    if spec is None or spec.loader is None:
        raise RuntimeError("unable to load Lite patch normalizer module")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def validate_side_effect_free(errors: list[str]) -> None:
    text = NORMALIZER.read_text(encoding="utf-8")
    for token in FORBIDDEN_TOKENS:
        if token in text:
            errors.append(f"patch normalizer contains forbidden token: {token}")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--raw-patch", required=True, type=Path)
    parser.add_argument("--normalized-snapshot", required=True, type=Path)
    args = parser.parse_args()

    errors: list[str] = []
    validate_side_effect_free(errors)
    normalizer = load_normalizer()
    raw_patch = load_json(args.raw_patch)
    expected = load_json(args.normalized_snapshot)
    actual = normalizer.normalize_lite_patch_source(raw_patch)
    if actual != expected:
        errors.append(f"normalized patch does not match snapshot: {args.normalized_snapshot}")

    if errors:
        print("Unified Semantic Page Contract Lite patch normalizer guard failed:")
        for error in errors:
            print(f"- {error}")
        return 1

    print("Unified Semantic Page Contract Lite patch normalizer guard passed")
    print(f"- normalized snapshot: {args.normalized_snapshot}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
