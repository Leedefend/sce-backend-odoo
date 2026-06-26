#!/usr/bin/env python3
"""Guard DataContract v2+ consolidation without requiring Odoo."""

from __future__ import annotations

import argparse
import importlib.util
import json
import re
import sys
import types
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
CORE_DIR = ROOT / "addons/smart_core/core"
DATA_PATH = ROOT / "addons/smart_core/core/unified_page_contract_v2_data.py"
DRIFT_SUFFIX = re.compile(r"(\.|:|-)(admin|user|role|web_pc|wx_mini|harmony_h5|mobile_app)$")


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def load_data_module():
    sys.modules.setdefault("odoo", types.ModuleType("odoo"))
    sys.modules.setdefault("odoo.addons", types.ModuleType("odoo.addons"))
    smart_core_pkg = sys.modules.setdefault("odoo.addons.smart_core", types.ModuleType("odoo.addons.smart_core"))
    smart_core_pkg.__path__ = [str(CORE_DIR.parent)]
    core_pkg = sys.modules.setdefault("odoo.addons.smart_core.core", types.ModuleType("odoo.addons.smart_core.core"))
    core_pkg.__path__ = [str(CORE_DIR)]
    spec = importlib.util.spec_from_file_location(
        "odoo.addons.smart_core.core.unified_page_contract_v2_data_guard_target",
        DATA_PATH,
    )
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load data module from {DATA_PATH}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def fail(errors: list[str], message: str) -> None:
    errors.append(message)


def registry_path(value: dict[str, Any], path: tuple[str, ...]) -> Any:
    node: Any = value
    for item in path:
        if not isinstance(node, dict):
            return None
        node = node.get(item)
    return node


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--fixture", required=True, type=Path)
    parser.add_argument("--snapshot", required=True, type=Path)
    parser.add_argument("--schema", required=True, type=Path)
    parser.add_argument("--enum-registry", required=True, type=Path)
    args = parser.parse_args()

    target = load_data_module()
    source = load_json(args.fixture)
    snapshot = load_json(args.snapshot)
    schema = load_json(args.schema)
    registry = load_json(args.enum_registry)
    data_contract = target.build_data_contract_v2(source)
    expected = snapshot.get("expected") if isinstance(snapshot.get("expected"), dict) else {}
    errors: list[str] = []

    required = {"mainData", "tableRows", "relationRows", "dictData", "pagination", "dataSource", "dataMeta"}
    optional = {"treeData", "ganttData"}
    missing = required - set(data_contract)
    if missing:
        fail(errors, f"dataContract missing required keys: {sorted(missing)}")
    schema_props = set(schema.get("$defs", {}).get("dataContract", {}).get("properties", {}).keys())
    if not optional.issubset(schema_props):
        fail(errors, "schema dataContract must expose optional treeData/ganttData extension slots")

    cache_policies = registry_path(registry, ("cachePolicy",))
    consistency_values = registry_path(registry, ("consistency",))
    if set(getattr(target, "ALLOWED_CACHE_POLICIES", set())) != set(cache_policies or []):
        fail(errors, "data ALLOWED_CACHE_POLICIES must match enum_registry.cachePolicy")
    if set(getattr(target, "ALLOWED_CONSISTENCY", set())) != set(consistency_values or []):
        fail(errors, "data ALLOWED_CONSISTENCY must match enum_registry.consistency")

    if sorted(data_contract.get("mainData", {}).keys()) != sorted(expected.get("mainDataKeys") or []):
        fail(errors, "mainData keys mismatch")
    for data_key, expected_len in (expected.get("tableRows") or {}).items():
        if len(data_contract.get("tableRows", {}).get(data_key) or []) != expected_len:
            fail(errors, f"tableRows.{data_key} length mismatch")
    for data_key, expected_len in (expected.get("relationRows") or {}).items():
        if len(data_contract.get("relationRows", {}).get(data_key) or []) != expected_len:
            fail(errors, f"relationRows.{data_key} length mismatch")
    if sorted(data_contract.get("treeData", {}).keys()) != sorted(expected.get("treeDataKeys") or []):
        fail(errors, "treeData keys mismatch")
    if sorted(data_contract.get("dictData", {}).keys()) != sorted(expected.get("dictDataKeys") or []):
        fail(errors, "dictData keys mismatch")
    if sorted(data_contract.get("pagination", {}).keys()) != sorted(expected.get("paginationKeys") or []):
        fail(errors, "pagination keys mismatch")

    for data_key, expected_row in (expected.get("dataSource") or {}).items():
        actual = data_contract.get("dataSource", {}).get(data_key)
        if actual != expected_row:
            fail(errors, f"dataSource.{data_key}: expected {expected_row!r}, got {actual!r}")
    for data_key, row in (data_contract.get("dataSource") or {}).items():
        if not isinstance(row, dict):
            continue
        if row.get("cachePolicy") not in cache_policies:
            fail(errors, f"dataSource.{data_key}.cachePolicy must be listed in enum_registry.cachePolicy")
        if row.get("consistency") not in consistency_values:
            fail(errors, f"dataSource.{data_key}.consistency must be listed in enum_registry.consistency")
    forbidden = target.find_forbidden_data_source_keys(data_contract)
    if forbidden:
        fail(errors, f"dataSource has forbidden semantic/executable keys: {forbidden}")
    for data_key in data_contract.get("dataSource", {}):
        if DRIFT_SUFFIX.search(data_key):
            fail(errors, f"unstable role/client suffix in dataKey {data_key!r}")

    if errors:
        print("Unified Page Contract v2+ data guard failed:")
        for error in errors:
            print(f"- {error}")
        return 1

    print("Unified Page Contract v2+ data guard passed: dataSources=%d" % len(data_contract.get("dataSource") or {}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
