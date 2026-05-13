#!/usr/bin/env python3
"""Guard RuntimeContract v2+ control-plane semantics without requiring Odoo."""

from __future__ import annotations

import argparse
import importlib.util
import json
import sys
import types
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
CORE_DIR = ROOT / "addons/smart_core/core"
RUNTIME_PATH = ROOT / "addons/smart_core/core/unified_page_contract_v2_runtime.py"


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def load_runtime_module():
    sys.modules.setdefault("odoo", types.ModuleType("odoo"))
    sys.modules.setdefault("odoo.addons", types.ModuleType("odoo.addons"))
    smart_core_pkg = sys.modules.setdefault("odoo.addons.smart_core", types.ModuleType("odoo.addons.smart_core"))
    smart_core_pkg.__path__ = [str(CORE_DIR.parent)]
    core_pkg = sys.modules.setdefault("odoo.addons.smart_core.core", types.ModuleType("odoo.addons.smart_core.core"))
    core_pkg.__path__ = [str(CORE_DIR)]
    spec = importlib.util.spec_from_file_location(
        "odoo.addons.smart_core.core.unified_page_contract_v2_runtime_guard_target",
        RUNTIME_PATH,
    )
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load runtime module from {RUNTIME_PATH}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def fail(errors: list[str], message: str) -> None:
    errors.append(message)


def compare_subset(actual: dict[str, Any], expected: dict[str, Any], path: str, errors: list[str]) -> None:
    for key, expected_value in expected.items():
        if isinstance(expected_value, dict):
            compare_subset(actual.get(key) or {}, expected_value, f"{path}.{key}", errors)
        elif actual.get(key) != expected_value:
            fail(errors, f"{path}.{key}: expected {expected_value!r}, got {actual.get(key)!r}")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--fixture", required=True, type=Path)
    parser.add_argument("--snapshot", required=True, type=Path)
    parser.add_argument("--schema", required=True, type=Path)
    args = parser.parse_args()

    target = load_runtime_module()
    contract = load_json(args.fixture)
    snapshot = load_json(args.snapshot)
    schema = load_json(args.schema)
    runtime = target.build_runtime_contract_v2(contract)
    contract["runtimeContract"] = runtime
    errors: list[str] = []

    schema_props = schema.get("$defs", {}).get("runtimeContract", {}).get("properties", {})
    for key in ("patchOperations", "tracePolicy", "complexityBudget", "aiEnvelope", "hydration", "renderStrategy"):
        if key not in schema_props:
            fail(errors, f"runtimeContract schema missing {key}")

    expected = snapshot.get("expected") if isinstance(snapshot.get("expected"), dict) else {}
    compare_subset(runtime, expected, "runtimeContract", errors)
    issues = target.find_runtime_guard_issues(contract)
    for issue in issues:
        fail(errors, issue)

    if len(runtime.get("patchOperations") or []) != 6:
        fail(errors, "patchOperations must expose the fixed six-operation registry")
    if runtime.get("aiEnvelope", {}).get("executable") is not False:
        fail(errors, "aiEnvelope must be non-executable")
    if not runtime.get("tracePolicy", {}).get("required"):
        fail(errors, "tracePolicy.required must default to true")

    if errors:
        print("Unified Page Contract v2+ runtime guard failed:")
        for error in errors:
            print(f"- {error}")
        return 1

    print("Unified Page Contract v2+ runtime guard passed: score=%s" % runtime.get("complexityBudget", {}).get("score"))
    return 0


if __name__ == "__main__":
    sys.exit(main())
