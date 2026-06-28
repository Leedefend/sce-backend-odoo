#!/usr/bin/env python3
"""Guard ActionContract v2+ consolidation without requiring Odoo."""

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
ACTION_PATH = ROOT / "addons/smart_core/core/unified_page_contract_v2_action.py"
FORBIDDEN_KEYS = {"script", "function", "eval", "expression", "jsonlogic", "workflowdsl", "componentcode"}
DRIFT_SUFFIX = re.compile(r"(\.|:|-)(admin|user|role|web_pc|wx_mini|harmony_h5|mobile_app|readonly|editable)$")


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def load_action_module():
    sys.modules.setdefault("odoo", types.ModuleType("odoo"))
    sys.modules.setdefault("odoo.addons", types.ModuleType("odoo.addons"))
    smart_core_pkg = sys.modules.setdefault("odoo.addons.smart_core", types.ModuleType("odoo.addons.smart_core"))
    smart_core_pkg.__path__ = [str(CORE_DIR.parent)]
    core_pkg = sys.modules.setdefault("odoo.addons.smart_core.core", types.ModuleType("odoo.addons.smart_core.core"))
    core_pkg.__path__ = [str(CORE_DIR)]
    spec = importlib.util.spec_from_file_location(
        "odoo.addons.smart_core.core.unified_page_contract_v2_action_guard_target",
        ACTION_PATH,
    )
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load action module from {ACTION_PATH}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def walk(value: Any, path: str = "$"):
    yield path, value
    if isinstance(value, dict):
        for key, child in value.items():
            yield from walk(child, f"{path}.{key}")
    elif isinstance(value, list):
        for index, child in enumerate(value):
            yield from walk(child, f"{path}[{index}]")


def fail(errors: list[str], message: str) -> None:
    errors.append(message)


def compare_subset(actual: dict[str, Any], expected: dict[str, Any], path: str, errors: list[str]) -> None:
    for key, expected_value in expected.items():
        if actual.get(key) != expected_value:
            fail(errors, f"{path}.{key}: expected {expected_value!r}, got {actual.get(key)!r}")


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
    parser.add_argument("--patch-fixture", required=True, type=Path)
    parser.add_argument("--snapshot", required=True, type=Path)
    parser.add_argument("--enum-registry", required=True, type=Path)
    args = parser.parse_args()

    target = load_action_module()
    source = load_json(args.fixture)
    patch_source = load_json(args.patch_fixture)
    snapshot = load_json(args.snapshot)
    registry = load_json(args.enum_registry)
    action_contract = target.build_action_contract_v2(source)
    patch = target.build_action_partial_update_v2(patch_source, action_id="form.save")
    errors: list[str] = []

    rules = action_contract.get("actionRuleList") if isinstance(action_contract.get("actionRuleList"), list) else []
    rule_index = {str(row.get("actionId")): row for row in rules if isinstance(row, dict)}
    action_ids = sorted(rule_index)
    expected_ids = sorted(snapshot.get("expectedActionIds") or [])
    if action_ids != expected_ids:
        fail(errors, f"action ids mismatch: expected {expected_ids}, got {action_ids}")
    if len(action_ids) != len(rules):
        fail(errors, "actionId uniqueness guard failed")

    trigger_types = registry_path(registry, ("triggerType",))
    dispatch_modes = registry_path(registry, ("dispatchMode",))
    target_scopes = registry_path(registry, ("targetScope",))
    refresh_modes = registry_path(registry, ("refreshMode",))
    if set(getattr(target, "TRIGGER_TYPES", set())) != set(trigger_types or []):
        fail(errors, "action TRIGGER_TYPES must match enum_registry.triggerType")
    if set(getattr(target, "DISPATCH_MODES", set())) != set(dispatch_modes or []):
        fail(errors, "action DISPATCH_MODES must match enum_registry.dispatchMode")
    if set(getattr(target, "REFRESH_MODES", set())) != set(refresh_modes or []):
        fail(errors, "action REFRESH_MODES must match enum_registry.refreshMode")

    for action_id, expected_rule in (snapshot.get("expectedRules") or {}).items():
        if action_id not in rule_index:
            fail(errors, f"missing action rule {action_id}")
            continue
        compare_subset(rule_index[action_id], expected_rule, action_id, errors)

    graph = action_contract.get("dependencyGraph") if isinstance(action_contract.get("dependencyGraph"), dict) else {}
    for source_id, expected_targets in (snapshot.get("expectedDependencies") or {}).items():
        if sorted(graph.get(source_id) or []) != sorted(expected_targets):
            fail(errors, f"dependencyGraph.{source_id}: expected {expected_targets}, got {graph.get(source_id)}")

    for node_path, node in walk(action_contract):
        if isinstance(node, dict):
            for key, value in node.items():
                if str(key).lower() in FORBIDDEN_KEYS:
                    fail(errors, f"forbidden executable key {key!r} at {node_path}")
                if key in {"actionId", "sourceWidgetId"} and isinstance(value, str) and DRIFT_SUFFIX.search(value):
                    fail(errors, f"unstable suffix in {key}={value!r}")
            if {"triggerType", "dispatchMode", "targetScope", "refreshMode"}.issubset(node):
                if node.get("triggerType") not in trigger_types:
                    fail(errors, f"{node_path}.triggerType must be listed in enum_registry.triggerType")
                if node.get("dispatchMode") not in dispatch_modes:
                    fail(errors, f"{node_path}.dispatchMode must be listed in enum_registry.dispatchMode")
                if node.get("targetScope") not in target_scopes:
                    fail(errors, f"{node_path}.targetScope must be listed in enum_registry.targetScope")
                if node.get("refreshMode") not in refresh_modes:
                    fail(errors, f"{node_path}.refreshMode must be listed in enum_registry.refreshMode")

    expected_patch = snapshot.get("expectedPatch") or {}
    if patch.get("updateType") != expected_patch.get("updateType"):
        fail(errors, "patch updateType mismatch")
    if patch.get("meta", {}).get("actionId") != expected_patch.get("actionId"):
        fail(errors, "patch actionId mismatch")
    if len(patch.get("dataPatch") or {}) < int(expected_patch.get("minDataPatchKeys") or 0):
        fail(errors, "patch dataPatch below baseline")
    if len(patch.get("statusPatch") or {}) < int(expected_patch.get("minStatusPatchKeys") or 0):
        fail(errors, "patch statusPatch below baseline")
    meta = patch.get("meta", {}) if isinstance(patch.get("meta"), dict) else {}
    if meta.get("sourceType") != "api.onchange":
        fail(errors, "patch meta.sourceType must be api.onchange")
    if meta.get("sourceKind") != "unified_page_contract_v2_action_projection":
        fail(errors, "patch meta.sourceKind must be unified_page_contract_v2_action_projection")
    if "compat" in meta:
        fail(errors, "patch meta.compat must be removed")

    if errors:
        print("Unified Page Contract v2+ action guard failed:")
        for error in errors:
            print(f"- {error}")
        return 1

    print("Unified Page Contract v2+ action guard passed: actions=%d" % len(action_ids))
    return 0


if __name__ == "__main__":
    sys.exit(main())
