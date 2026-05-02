#!/usr/bin/env python3
"""Guard the current-stage Unified Semantic Page Contract Lite."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


TOP_LEVEL = {"pageInfo", "layoutContract", "statusContract", "actionContract", "dataContract", "meta"}
FORBIDDEN_KEYS = {
    "runtimeContract",
    "componentRegistry",
    "capabilities",
    "dataSource",
    "dependencyGraph",
    "selectorStatus",
    "patchOperations",
    "hydration",
    "virtualization",
    "scheduler",
    "aiEnvelope",
    "script",
    "function",
    "eval",
    "expression",
    "jsonLogic",
    "workflowDsl",
    "loop",
    "stream",
    "subscription",
    "consistency",
}


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


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


def validate_contract(payload: dict[str, Any], errors: list[str]) -> None:
    if set(payload.keys()) != TOP_LEVEL:
        fail(errors, f"top-level must be Lite shape only: {sorted(payload.keys())}")
    if payload.get("pageInfo", {}).get("contractVersion") != "2.0.0":
        fail(errors, "contractVersion must be 2.0.0 for Lite")
    if "containerList" not in payload.get("layoutContract", {}):
        fail(errors, "layoutContract.containerList is required")
    if set(payload.get("statusContract", {}).keys()) != {"widgetStatus", "buttonStatus"}:
        fail(errors, "statusContract must only contain widgetStatus/buttonStatus in Lite")
    if set(payload.get("dataContract", {}).keys()) != {"mainData", "relationData", "dictData"}:
        fail(errors, "dataContract must only contain mainData/relationData/dictData in Lite")
    for rule in payload.get("actionContract", {}).get("actionRuleList", []):
        if not isinstance(rule, dict):
            continue
        if rule.get("dispatchMode") != "server":
            fail(errors, f"{rule.get('actionId')}: dispatchMode must be server")
        for forbidden in ("actionType", "conditionBranch", "chainAction", "workflow", "loop"):
            if forbidden in rule:
                fail(errors, f"{rule.get('actionId')}: forbidden action DSL key {forbidden}")


def validate_patch(payload: dict[str, Any], errors: list[str]) -> None:
    if payload.get("updateType") != "partial":
        fail(errors, "patch updateType must be partial")
    if payload.get("operation") not in {"replace", "merge"}:
        fail(errors, "patch operation must be replace or merge")
    for key in ("statusPatch", "dataPatch", "layoutPatch"):
        if key not in payload:
            fail(errors, f"patch missing {key}")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--schema", required=True, type=Path)
    parser.add_argument("--example", required=True, type=Path)
    parser.add_argument("--patch", required=True, type=Path)
    args = parser.parse_args()

    errors: list[str] = []
    schema = load_json(args.schema)
    example = load_json(args.example)
    patch = load_json(args.patch)

    if set(schema.get("required") or []) != TOP_LEVEL:
        fail(errors, "schema top-level required keys must match Lite shape")
    if "runtimeContract" in schema.get("properties", {}):
        fail(errors, "schema must not define runtimeContract")
    validate_contract(example, errors)
    validate_patch(patch, errors)

    for source_name, payload in (("schema", schema), ("example", example), ("patch", patch)):
        for node_path, node in walk(payload):
            if not isinstance(node, dict):
                continue
            for key in node:
                if key in FORBIDDEN_KEYS:
                    fail(errors, f"{source_name}: forbidden key {key!r} at {node_path}")

    if errors:
        print("Unified Semantic Page Contract Lite guard failed:")
        for error in errors:
            print(f"- {error}")
        return 1

    print("Unified Semantic Page Contract Lite guard passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
