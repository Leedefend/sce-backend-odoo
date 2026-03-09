#!/usr/bin/env python3
from __future__ import annotations

import ast
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
HOME_BUILDER = ROOT / "addons/smart_core/core/workspace_home_contract_builder.py"
ALLOWED_TAGS = {"header", "section", "details", "div"}


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="ignore") if path.is_file() else ""


def _fail(errors: list[str]) -> int:
    print("[workspace_home_sections_schema_guard] FAIL")
    for err in errors:
        print(f"- {err}")
    return 1


def _dict_get_constant_key(node: ast.Dict, key: str):
    for k, v in zip(node.keys, node.values):
        if isinstance(k, ast.Constant) and k.value == key:
            return v
    return None


def _extract_sections(builder_text: str) -> list[dict[str, object]]:
    tree = ast.parse(builder_text)
    for node in ast.walk(tree):
        if isinstance(node, ast.Return) and isinstance(node.value, ast.Dict):
            layout_node = _dict_get_constant_key(node.value, "layout")
            if not isinstance(layout_node, ast.Dict):
                continue
            sections_node = _dict_get_constant_key(layout_node, "sections")
            if not isinstance(sections_node, ast.List):
                continue
            result: list[dict[str, object]] = []
            for item in sections_node.elts:
                if not isinstance(item, ast.Dict):
                    continue
                key_node = _dict_get_constant_key(item, "key")
                enabled_node = _dict_get_constant_key(item, "enabled")
                tag_node = _dict_get_constant_key(item, "tag")
                open_node = _dict_get_constant_key(item, "open")
                rec: dict[str, object] = {}
                if isinstance(key_node, ast.Constant):
                    rec["key"] = key_node.value
                if isinstance(enabled_node, ast.Constant):
                    rec["enabled"] = enabled_node.value
                if isinstance(tag_node, ast.Constant):
                    rec["tag"] = tag_node.value
                if isinstance(open_node, ast.Constant):
                    rec["open"] = open_node.value
                result.append(rec)
            if result:
                return result
    return []


def main() -> int:
    builder_text = _read(HOME_BUILDER)
    if not builder_text:
        return _fail([f"missing file: {HOME_BUILDER.relative_to(ROOT).as_posix()}"])

    sections = _extract_sections(builder_text)
    if not sections:
        return _fail(["failed to extract layout.sections from workspace_home_contract_builder.py"])

    errors: list[str] = []
    seen_keys: set[str] = set()
    for idx, sec in enumerate(sections):
        prefix = f"layout.sections[{idx}]"
        key = sec.get("key")
        enabled = sec.get("enabled")
        tag = sec.get("tag")
        has_open = "open" in sec
        open_value = sec.get("open")

        if not isinstance(key, str) or not key.strip():
            errors.append(f"{prefix}.key must be non-empty string")
        elif key in seen_keys:
            errors.append(f"{prefix}.key duplicate: {key}")
        else:
            seen_keys.add(key)

        if not isinstance(enabled, bool):
            errors.append(f"{prefix}.enabled must be bool")

        if not isinstance(tag, str) or tag not in ALLOWED_TAGS:
            errors.append(f"{prefix}.tag must be one of {sorted(ALLOWED_TAGS)}")
        elif tag == "details":
            if not has_open:
                errors.append(f"{prefix}.open is required when tag=details")
            elif not isinstance(open_value, bool):
                errors.append(f"{prefix}.open must be bool when tag=details")
        elif has_open and not isinstance(open_value, bool):
            errors.append(f"{prefix}.open must be bool when present")

    if errors:
        return _fail(errors)

    print(f"[workspace_home_sections_schema_guard] PASS (checked_sections={len(sections)})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
