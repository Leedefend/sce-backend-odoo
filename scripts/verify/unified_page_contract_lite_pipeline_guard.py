#!/usr/bin/env python3
"""Guard the offline raw source -> normalizer -> Lite adapter pipeline."""

from __future__ import annotations

import argparse
import importlib.util
import json
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
SOURCE_NORMALIZER = ROOT / "addons" / "smart_core" / "core" / "unified_page_contract_lite_source_normalizer.py"
PATCH_NORMALIZER = ROOT / "addons" / "smart_core" / "core" / "unified_page_contract_lite_patch_normalizer.py"
ADAPTER = ROOT / "addons" / "smart_core" / "core" / "unified_page_contract_lite_adapter.py"


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"unable to load module: {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--raw-contract-source", required=True, type=Path)
    parser.add_argument("--contract-snapshot", required=True, type=Path)
    parser.add_argument("--raw-patch-source", required=True, type=Path)
    parser.add_argument("--patch-snapshot", required=True, type=Path)
    args = parser.parse_args()

    source_normalizer = load_module("unified_page_contract_lite_source_normalizer_pipeline", SOURCE_NORMALIZER)
    patch_normalizer = load_module("unified_page_contract_lite_patch_normalizer_pipeline", PATCH_NORMALIZER)
    adapter = load_module("unified_page_contract_lite_adapter_pipeline", ADAPTER)

    errors: list[str] = []
    raw_contract_source = load_json(args.raw_contract_source)
    expected_contract = load_json(args.contract_snapshot)
    normalized_contract_source = source_normalizer.normalize_lite_contract_source(raw_contract_source)
    actual_contract = adapter.build_lite_contract(normalized_contract_source, client_type=normalized_contract_source.get("client_type", "web_pc"))
    if actual_contract != expected_contract:
        errors.append(f"pipeline contract output does not match snapshot: {args.contract_snapshot}")

    raw_patch_source = load_json(args.raw_patch_source)
    expected_patch = load_json(args.patch_snapshot)
    normalized_patch_source = patch_normalizer.normalize_lite_patch_source(raw_patch_source)
    actual_patch = adapter.build_lite_patch(normalized_patch_source)
    if actual_patch != expected_patch:
        errors.append(f"pipeline patch output does not match snapshot: {args.patch_snapshot}")

    if errors:
        print("Unified Semantic Page Contract Lite pipeline guard failed:")
        for error in errors:
            print(f"- {error}")
        return 1

    print("Unified Semantic Page Contract Lite pipeline guard passed")
    print(f"- contract snapshot: {args.contract_snapshot}")
    print(f"- patch snapshot: {args.patch_snapshot}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
