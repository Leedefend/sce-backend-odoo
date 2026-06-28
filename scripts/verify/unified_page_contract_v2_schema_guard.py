#!/usr/bin/env python3
"""Static guard for Unified Page Contract v2+ protocol assets."""

from __future__ import annotations

import argparse
import copy
import json
import re
import sys
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator


TOP_LEVEL_KEYS = {
    "pageInfo",
    "layoutContract",
    "statusContract",
    "actionContract",
    "dataContract",
    "runtimeContract",
    "meta",
}
OPTIONAL_TOP_LEVEL_KEYS = {
    "formStructureContract",
}
TOP_LEVEL_PROPERTIES = TOP_LEVEL_KEYS | OPTIONAL_TOP_LEVEL_KEYS

REQUIRED_DEFS = {
    "pageInfo",
    "layoutContract",
    "container",
    "widget",
    "statusContract",
    "actionContract",
    "actionRule",
    "dataContract",
    "dataMeta",
    "visibleFields",
    "fieldGroups",
    "sourceAuthority",
    "runtimeContract",
    "formStructureContract",
    "formStructureSlot",
    "formStructureGroup",
    "formStructureRole",
    "meta",
}

REQUIRED_CLOSED_OBJECT_DEFS = {
    "containerStatus",
    "widgetStatus",
    "buttonStatus",
    "selectorStatus",
}

LEGACY_ROOT_KEYS = {
    "scene_contract_v1",
    "page_orchestration_v1",
    "ui_contract",
    "ui.contract",
    "api.onchange",
}

FORMAL_V2_FIELD_PATHS = {
    "$defs.layoutContract.properties.listProfile",
    "$defs.actionContract.properties.deletePolicy",
    "$defs.actionContract.properties.surfacePolicies",
    "$defs.dataMeta.properties.businessOperationProfile",
    "$defs.dataMeta.properties.visibleFields",
    "$defs.dataMeta.properties.fieldGroups",
}

SCHEMA_ENUM_REGISTRY_MAP = {
    ("pageInfo", "viewType"): ("viewType",),
    ("pageInfo", "layoutType"): ("layoutType",),
    ("pageInfo", "renderMode"): ("renderMode",),
    ("pageInfo", "clientType"): ("clientType", "stable"),
    ("layoutContract", "layoutType"): ("layoutType",),
    ("layoutContract", "adaptMode"): ("adaptMode",),
    ("container", "containerType"): ("containerType",),
    ("widget", "widgetType"): ("widgetType",),
    ("widgetStatus", "auth"): ("authLevel",),
    ("actionRule", "triggerType"): ("triggerType",),
    ("actionRule", "dispatchMode"): ("dispatchMode",),
    ("actionRule", "targetScope"): ("targetScope",),
    ("actionRule", "refreshMode"): ("refreshMode",),
    ("runtimeContract", "patchStrategy"): ("patchStrategy",),
    ("runtimeContract", "cachePolicy"): ("cachePolicy",),
    ("runtimeContract", "renderStrategy"): ("renderStrategy",),
}

FORBIDDEN_FORMAL_SCHEMA_KEYS = {
    "list_profile",
    "delete_policy",
    "surface_policies",
    "business_operation_profile",
    "visible_fields",
    "field_groups",
    "form_structure_contract",
    "legacyContractProjection",
    "legacy_contract_projection",
}

FORBIDDEN_SCHEMA_ALIAS_CASES = {
    "$.delete_policy": ("delete_policy",),
    "$.surface_policies": ("surface_policies",),
    "$.list_profile": ("list_profile",),
    "$.form_structure_contract": ("form_structure_contract",),
    "$.legacyContractProjection": ("legacyContractProjection",),
    "$.legacy_contract_projection": ("legacy_contract_projection",),
    "$.layoutContract.list_profile": ("layoutContract", "list_profile"),
    "$.actionContract.delete_policy": ("actionContract", "delete_policy"),
    "$.actionContract.surface_policies": ("actionContract", "surface_policies"),
    "$.dataContract.dataMeta.business_operation_profile": (
        "dataContract",
        "dataMeta",
        "business_operation_profile",
    ),
    "$.dataContract.dataMeta.visible_fields": ("dataContract", "dataMeta", "visible_fields"),
    "$.dataContract.dataMeta.field_groups": ("dataContract", "dataMeta", "field_groups"),
    "$.dataContract.dataMeta.legacyContractProjection": (
        "dataContract",
        "dataMeta",
        "legacyContractProjection",
    ),
    "$.dataContract.dataMeta.legacy_contract_projection": (
        "dataContract",
        "dataMeta",
        "legacy_contract_projection",
    ),
}

ID_KEYS = {
    "pageId",
    "sceneKey",
    "containerId",
    "widgetId",
    "fieldCode",
    "btnId",
    "actionId",
    "dataKey",
    "sourceWidgetId",
}

ID_DRIFT_SUFFIX = re.compile(
    r"(\.|:|-)(admin|user|role|web_pc|wx_mini|harmony_h5|mobile_app|readonly|editable|visible|hidden)$"
)

VOLATILE_META_PATTERN = re.compile(
    r"(\d{4}-\d{2}-\d{2}t\d{2}:|\d{13,}|[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12})",
    re.IGNORECASE,
)


def load_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:  # pragma: no cover - guard output path
        raise ValueError(f"{path}: invalid JSON: {exc}") from exc


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


def dict_path(value: dict[str, Any], path: str) -> Any:
    node: Any = value
    for item in path.split("."):
        if not isinstance(node, dict):
            return None
        node = node.get(item)
    return node


def registry_path(value: dict[str, Any], path: tuple[str, ...]) -> Any:
    node: Any = value
    for item in path:
        if not isinstance(node, dict):
            return None
        node = node.get(item)
    return node


def validate_schema(schema: dict[str, Any], registry: dict[str, Any], errors: list[str]) -> None:
    required = set(schema.get("required", []))
    if required != TOP_LEVEL_KEYS:
        fail(errors, f"schema top-level required keys mismatch: {sorted(required)}")

    properties = set(schema.get("properties", {}).keys())
    if properties != TOP_LEVEL_PROPERTIES:
        fail(errors, f"schema top-level properties mismatch: {sorted(properties)}")

    defs = set(schema.get("$defs", {}).keys())
    missing_defs = REQUIRED_DEFS - defs
    if missing_defs:
        fail(errors, f"schema missing $defs: {sorted(missing_defs)}")
    for name in sorted(REQUIRED_CLOSED_OBJECT_DEFS):
        definition = schema.get("$defs", {}).get(name, {})
        if definition.get("additionalProperties") is not False:
            fail(errors, f"schema $defs.{name} must set additionalProperties=false")
    for path in sorted(FORMAL_V2_FIELD_PATHS):
        if dict_path(schema, path) is None:
            fail(errors, f"schema missing formal v2 field path: {path}")
    for node_path, node in walk(schema):
        if not isinstance(node, dict):
            continue
        for key in node:
            if key in FORBIDDEN_FORMAL_SCHEMA_KEYS:
                fail(errors, f"schema must not declare compatibility field {key!r} at {node_path}")

    schema_defs = schema.get("$defs", {})
    for (def_name, field_name), registry_key_path in sorted(SCHEMA_ENUM_REGISTRY_MAP.items()):
        schema_enum = (
            schema_defs.get(def_name, {})
            .get("properties", {})
            .get(field_name, {})
            .get("enum")
        )
        registry_enum = registry_path(registry, registry_key_path)
        if not isinstance(schema_enum, list):
            fail(errors, f"schema $defs.{def_name}.properties.{field_name}.enum is required")
            continue
        if schema_enum != registry_enum:
            fail(
                errors,
                f"schema $defs.{def_name}.properties.{field_name}.enum must match "
                f"enum_registry.{'.'.join(registry_key_path)}",
            )

    patch_ops = set(registry.get("patchOperation", []))
    expected_patch_ops = {"replace", "merge", "append", "remove", "reorder", "invalidate"}
    if patch_ops != expected_patch_ops:
        fail(errors, f"patchOperation enum mismatch: {sorted(patch_ops)}")


def validate_example(path: Path, payload: dict[str, Any], registry: dict[str, Any], errors: list[str]) -> None:
    keys = set(payload.keys())
    if keys != TOP_LEVEL_KEYS:
        fail(errors, f"{path}: top-level keys must equal canonical v2 shape, got {sorted(keys)}")

    page_info = payload.get("pageInfo", {})
    stable_clients = registry.get("clientType", {}).get("stable", [])
    client_type = page_info.get("clientType")
    if client_type not in stable_clients:
        fail(errors, f"{path}: unsupported stable clientType {client_type!r}")

    if page_info.get("pageId") != payload.get("layoutContract", {}).get("pageId"):
        fail(errors, f"{path}: pageInfo.pageId and layoutContract.pageId must match")

    meta = payload.get("meta", {})
    for required_meta in ("etag", "snapshotId", "traceId", "requestId", "sourceType"):
        if required_meta not in meta:
            fail(errors, f"{path}: meta.{required_meta} is required")
        elif VOLATILE_META_PATTERN.search(str(meta.get(required_meta, ""))):
            fail(errors, f"{path}: meta.{required_meta} must use normalized stable sample value")
    if "compat" in meta:
        fail(errors, f"{path}: meta.compat must be removed")

    forbidden_keys = {str(key).lower() for key in registry.get("forbiddenContractKeys", [])}
    for node_path, node in walk(payload):
        if not isinstance(node, dict):
            continue
        for key, value in node.items():
            lower_key = str(key).lower()
            if lower_key in forbidden_keys or lower_key.startswith("_fe"):
                fail(errors, f"{path}: forbidden DSL-like key {key!r} at {node_path}")
            if key in LEGACY_ROOT_KEYS:
                fail(errors, f"{path}: legacy key {key!r} must be removed")
            if key in ID_KEYS and isinstance(value, str) and ID_DRIFT_SUFFIX.search(value):
                fail(errors, f"{path}: unstable semantic/client suffix in {key}={value!r}")

    component_registry = payload.get("layoutContract", {}).get("componentRegistry", {})
    for node_path, node in walk(payload.get("layoutContract", {})):
        if isinstance(node, dict) and "componentKey" in node:
            component_key = node["componentKey"]
            if component_key not in component_registry:
                fail(errors, f"{path}: componentKey {component_key!r} missing from componentRegistry at {node_path}")
        if isinstance(node, dict) and "capabilities" in node:
            capabilities = node.get("capabilities", [])
            unknown = set(capabilities) - set(registry.get("componentCapability", []))
            if unknown:
                fail(errors, f"{path}: unknown capabilities {sorted(unknown)} at {node_path}")


def validate_example_against_schema(
    path: Path,
    payload: dict[str, Any],
    validator: Draft202012Validator,
    errors: list[str],
) -> None:
    for issue in sorted(validator.iter_errors(payload), key=lambda item: list(item.absolute_path)):
        location = "$"
        if issue.absolute_path:
            location = "$." + ".".join(str(item) for item in issue.absolute_path)
        fail(errors, f"{path}: schema validation failed at {location}: {issue.message}")


def validate_schema_rejects_compatibility_aliases(
    path: Path,
    payload: dict[str, Any],
    validator: Draft202012Validator,
    errors: list[str],
) -> None:
    for alias_path, path_parts in sorted(FORBIDDEN_SCHEMA_ALIAS_CASES.items()):
        mutated = copy.deepcopy(payload)
        parent: Any = mutated
        for part in path_parts[:-1]:
            if not isinstance(parent, dict):
                fail(errors, f"{path}: {alias_path} parent must be an object before alias rejection check")
                parent = None
                break
            parent = parent.setdefault(part, {})
        if parent is None:
            continue
        if not isinstance(parent, dict):
            fail(errors, f"{path}: {alias_path} parent must be an object before alias rejection check")
            continue
        parent[path_parts[-1]] = {}
        if not list(validator.iter_errors(mutated)):
            fail(errors, f"{path}: schema must reject compatibility alias {alias_path}")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--schema", required=True, type=Path)
    parser.add_argument("--enum-registry", required=True, type=Path)
    parser.add_argument("--examples", required=True, type=Path)
    args = parser.parse_args()

    errors: list[str] = []
    schema = load_json(args.schema)
    registry = load_json(args.enum_registry)
    validate_schema(schema, registry, errors)
    validator = Draft202012Validator(schema)

    example_paths = sorted(args.examples.glob("*.json"))
    if not example_paths:
        fail(errors, f"{args.examples}: no example JSON files found")

    for example_path in example_paths:
        payload = load_json(example_path)
        validate_example_against_schema(example_path, payload, validator, errors)
        validate_schema_rejects_compatibility_aliases(example_path, payload, validator, errors)
        validate_example(example_path, payload, registry, errors)

    if errors:
        print("Unified Page Contract v2+ schema guard failed:")
        for error in errors:
            print(f"- {error}")
        return 1

    print(
        "Unified Page Contract v2+ schema guard passed: "
        f"schema={args.schema}, examples={len(example_paths)}"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
