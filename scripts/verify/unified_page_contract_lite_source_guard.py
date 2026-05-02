#!/usr/bin/env python3
"""Guard normalized Lite adapter source fixtures before runtime integration."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


CONTRACT_SOURCE_KEYS = {
    "page_id",
    "scene_key",
    "client_type",
    "etag",
    "trace_id",
    "render_profile",
    "semantic_page",
    "fields",
    "field_policies",
    "action_policies",
    "access_policy",
    "modifiers",
    "field_modifiers",
    "onchange_fields",
    "record",
    "relation_rows",
    "dict_data",
}
PATCH_SOURCE_KEYS = {
    "schema_version",
    "patch",
    "modifiers_patch",
    "button_status_patch",
    "line_patches",
    "warnings",
    "applied_fields",
}
CLIENT_TYPES = {"web_pc", "wx_mini", "harmony_h5"}
VIEW_TYPES = {"form", "tree", "list", "kanban", "search", "gantt", "popup", "combine"}
RENDER_PROFILES = {"create", "edit", "readonly", "search", "list"}
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
    "actionType",
    "chainAction",
    "conditionBranch",
    "workflowDsl",
    "jsonLogic",
    "script",
    "function",
    "eval",
    "expression",
    "subscription",
    "stream",
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


def text(value: Any) -> str:
    return str(value or "").strip()


def validate_no_forbidden(payload: Any, errors: list[str], source_name: str) -> None:
    for node_path, node in walk(payload):
        if not isinstance(node, dict):
            continue
        for key in node:
            if key in FORBIDDEN_KEYS:
                errors.append(f"{source_name}: forbidden key {key!r} at {node_path}")


def validate_contract_source(payload: dict[str, Any], errors: list[str], source_name: str) -> None:
    keys = set(payload.keys())
    unknown = sorted(keys - CONTRACT_SOURCE_KEYS)
    if unknown:
        errors.append(f"{source_name}: unknown contract source keys: {unknown}")
    for required in ("page_id", "scene_key", "client_type", "semantic_page", "fields"):
        if required not in payload:
            errors.append(f"{source_name}: missing required key {required}")
    if payload.get("client_type") not in CLIENT_TYPES:
        errors.append(f"{source_name}: client_type must be one of {sorted(CLIENT_TYPES)}")
    profile = payload.get("render_profile")
    if profile is not None and profile not in RENDER_PROFILES:
        errors.append(f"{source_name}: render_profile must be one of {sorted(RENDER_PROFILES)}")
    semantic_page = payload.get("semantic_page")
    if not isinstance(semantic_page, dict):
        errors.append(f"{source_name}: semantic_page must be object")
        return
    if not text(semantic_page.get("model")):
        errors.append(f"{source_name}: semantic_page.model is required")
    if semantic_page.get("view_type") not in VIEW_TYPES:
        errors.append(f"{source_name}: semantic_page.view_type must be one of {sorted(VIEW_TYPES)}")
    if not isinstance(payload.get("fields"), dict) or not payload.get("fields"):
        errors.append(f"{source_name}: fields must be a non-empty object")
    for field_name, desc in (payload.get("fields") or {}).items():
        if not text(field_name):
            errors.append(f"{source_name}: field name must not be empty")
        if not isinstance(desc, dict):
            errors.append(f"{source_name}: field {field_name} descriptor must be object")


def validate_patch_source(payload: dict[str, Any], errors: list[str], source_name: str) -> None:
    keys = set(payload.keys())
    unknown = sorted(keys - PATCH_SOURCE_KEYS)
    if unknown:
        errors.append(f"{source_name}: unknown patch source keys: {unknown}")
    for required in ("schema_version", "patch", "modifiers_patch", "line_patches"):
        if required not in payload:
            errors.append(f"{source_name}: missing required key {required}")
    if payload.get("schema_version") != "v1":
        errors.append(f"{source_name}: schema_version must be v1")
    if not isinstance(payload.get("patch"), dict):
        errors.append(f"{source_name}: patch must be object")
    if not isinstance(payload.get("modifiers_patch"), dict):
        errors.append(f"{source_name}: modifiers_patch must be object")
    if not isinstance(payload.get("line_patches"), list):
        errors.append(f"{source_name}: line_patches must be array")
    for index, row in enumerate(payload.get("line_patches") or []):
        if not isinstance(row, dict):
            errors.append(f"{source_name}: line_patches[{index}] must be object")
            continue
        if not text(row.get("field")):
            errors.append(f"{source_name}: line_patches[{index}].field is required")
        if "patch" in row and not isinstance(row.get("patch"), dict):
            errors.append(f"{source_name}: line_patches[{index}].patch must be object")
        if "modifiers_patch" in row and not isinstance(row.get("modifiers_patch"), dict):
            errors.append(f"{source_name}: line_patches[{index}].modifiers_patch must be object")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--contract-source", action="append", required=True, type=Path)
    parser.add_argument("--patch-source", action="append", required=True, type=Path)
    parser.add_argument("--contract-source-schema", required=True, type=Path)
    parser.add_argument("--patch-source-schema", required=True, type=Path)
    args = parser.parse_args()

    errors: list[str] = []
    contract_source_schema = load_json(args.contract_source_schema)
    patch_source_schema = load_json(args.patch_source_schema)
    if set(contract_source_schema.get("required") or []) != {"page_id", "scene_key", "client_type", "semantic_page", "fields"}:
        errors.append("contract source schema required keys drifted")
    if set(patch_source_schema.get("required") or []) != {"schema_version", "patch", "modifiers_patch", "line_patches"}:
        errors.append("patch source schema required keys drifted")
    validate_no_forbidden(contract_source_schema, errors, "contract source schema")
    validate_no_forbidden(patch_source_schema, errors, "patch source schema")

    for source_path in args.contract_source:
        payload = load_json(source_path)
        if not isinstance(payload, dict):
            errors.append(f"{source_path}: contract source must be object")
            continue
        validate_contract_source(payload, errors, str(source_path))
        validate_no_forbidden(payload, errors, str(source_path))
    for source_path in args.patch_source:
        payload = load_json(source_path)
        if not isinstance(payload, dict):
            errors.append(f"{source_path}: patch source must be object")
            continue
        validate_patch_source(payload, errors, str(source_path))
        validate_no_forbidden(payload, errors, str(source_path))

    if errors:
        print("Unified Semantic Page Contract Lite source guard failed:")
        for error in errors:
            print(f"- {error}")
        return 1

    print("Unified Semantic Page Contract Lite source guard passed")
    print(f"- contract sources: {len(args.contract_source)}")
    print(f"- patch sources: {len(args.patch_source)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
