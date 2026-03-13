#!/usr/bin/env python3
import argparse
import json
from pathlib import Path


def _type_matches(value, type_name: str) -> bool:
    mapping = {
        "object": lambda v: isinstance(v, dict),
        "array": lambda v: isinstance(v, list),
        "string": lambda v: isinstance(v, str),
        "number": lambda v: isinstance(v, (int, float)) and not isinstance(v, bool),
        "integer": lambda v: isinstance(v, int) and not isinstance(v, bool),
        "boolean": lambda v: isinstance(v, bool),
        "null": lambda v: v is None,
    }
    checker = mapping.get(type_name)
    return checker(value) if checker else True


def _resolve_ref(schema: dict, ref: str) -> dict:
    # only supports internal refs like #/$defs/name
    if not ref.startswith("#/"):
        return {}
    node = schema
    for part in ref[2:].split("/"):
        if not isinstance(node, dict) or part not in node:
            return {}
        node = node[part]
    return node if isinstance(node, dict) else {}


def _validate(node, rule: dict, root_schema: dict, path: str, errors: list[str]):
    if not isinstance(rule, dict):
        return

    if "$ref" in rule:
        ref_rule = _resolve_ref(root_schema, str(rule.get("$ref") or ""))
        if not ref_rule:
            errors.append(f"{path}: unresolved $ref {rule.get('$ref')}")
            return
        _validate(node, ref_rule, root_schema, path, errors)
        return

    expected_type = rule.get("type")
    if expected_type is not None:
        if isinstance(expected_type, list):
            if not any(_type_matches(node, t) for t in expected_type):
                errors.append(f"{path}: type mismatch, expected one of {expected_type}")
                return
        elif isinstance(expected_type, str):
            if not _type_matches(node, expected_type):
                errors.append(f"{path}: type mismatch, expected {expected_type}")
                return

    if "enum" in rule and node not in rule.get("enum", []):
        errors.append(f"{path}: value '{node}' not in enum")

    if isinstance(node, str) and isinstance(rule.get("minLength"), int):
        if len(node) < int(rule["minLength"]):
            errors.append(f"{path}: string length < minLength {rule['minLength']}")

    if isinstance(node, list):
        if isinstance(rule.get("maxItems"), int) and len(node) > int(rule["maxItems"]):
            errors.append(f"{path}: array length > maxItems {rule['maxItems']}")
        item_rule = rule.get("items")
        if isinstance(item_rule, dict):
            for i, item in enumerate(node):
                _validate(item, item_rule, root_schema, f"{path}[{i}]", errors)

    if isinstance(node, dict):
        required = rule.get("required")
        if isinstance(required, list):
            for key in required:
                if key not in node:
                    errors.append(f"{path}: missing required key '{key}'")

        properties = rule.get("properties")
        if isinstance(properties, dict):
            for key, subrule in properties.items():
                if key in node:
                    _validate(node[key], subrule, root_schema, f"{path}.{key}", errors)

        additional = rule.get("additionalProperties", True)
        if additional is False and isinstance(properties, dict):
            for key in node.keys():
                if key not in properties:
                    errors.append(f"{path}: additional property '{key}' is not allowed")


def validate_file(schema: dict, path: Path) -> list[str]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        return [f"{path}: invalid json ({exc})"]

    errors: list[str] = []
    _validate(payload, schema, schema, "$", errors)
    return errors


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--schema", default="docs/architecture/native_view_contract/semantic_page_contract_shape_v1.schema.json")
    parser.add_argument("--dir", default="docs/contract/snapshots/native_view")
    args = parser.parse_args()

    schema_file = Path(args.schema)
    root = Path(args.dir)

    if not schema_file.exists():
        print(f"[verify.native_view.semantic_page.schema] FAIL: schema not found: {schema_file}")
        return 2
    if not root.exists():
        print(f"[verify.native_view.semantic_page.schema] FAIL: dir not found: {root}")
        return 2

    try:
        schema = json.loads(schema_file.read_text(encoding="utf-8"))
    except Exception as exc:
        print(f"[verify.native_view.semantic_page.schema] FAIL: invalid schema json ({exc})")
        return 2

    files = sorted(root.glob("*.json"))
    if not files:
        print(f"[verify.native_view.semantic_page.schema] FAIL: no json files in {root}")
        return 2

    all_errors: list[str] = []
    for file in files:
        all_errors.extend(validate_file(schema, file))

    if all_errors:
        print("[verify.native_view.semantic_page.schema] FAIL")
        for err in all_errors:
            print(f" - {err}")
        return 2

    print(f"[verify.native_view.semantic_page.schema] PASS ({len(files)} files)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

