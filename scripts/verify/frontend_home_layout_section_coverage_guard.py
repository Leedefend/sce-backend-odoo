#!/usr/bin/env python3
from __future__ import annotations

import ast
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
HOME_VIEW = ROOT / "frontend/apps/web/src/views/HomeView.vue"
HOME_BUILDER = ROOT / "addons/smart_core/core/workspace_home_contract_builder.py"


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="ignore") if path.is_file() else ""


def _fail(errors: list[str]) -> int:
    print("[frontend_home_layout_section_coverage_guard] FAIL")
    for err in errors:
        print(f"- {err}")
    return 1


def _dict_get_constant_key(node: ast.Dict, key: str):
    for k, v in zip(node.keys, node.values):
        if isinstance(k, ast.Constant) and k.value == key:
            return v
    return None


def _extract_home_layout_sections(builder_text: str) -> list[tuple[str, str]]:
    tree = ast.parse(builder_text)
    for node in ast.walk(tree):
        if isinstance(node, ast.Return) and isinstance(node.value, ast.Dict):
            layout_node = _dict_get_constant_key(node.value, "layout")
            if not isinstance(layout_node, ast.Dict):
                continue
            sections_node = _dict_get_constant_key(layout_node, "sections")
            if not isinstance(sections_node, ast.List):
                continue
            result: list[tuple[str, str]] = []
            for item in sections_node.elts:
                if not isinstance(item, ast.Dict):
                    continue
                key_node = _dict_get_constant_key(item, "key")
                tag_node = _dict_get_constant_key(item, "tag")
                if isinstance(key_node, ast.Constant) and isinstance(key_node.value, str) and isinstance(tag_node, ast.Constant) and isinstance(tag_node.value, str):
                    result.append((key_node.value.strip(), tag_node.value.strip()))
            if result:
                return result
    return []


def main() -> int:
    home_text = _read(HOME_VIEW)
    if not home_text:
        return _fail([f"missing file: {HOME_VIEW.relative_to(ROOT).as_posix()}"])

    builder_text = _read(HOME_BUILDER)
    if not builder_text:
        return _fail([f"missing file: {HOME_BUILDER.relative_to(ROOT).as_posix()}"])

    sections = _extract_home_layout_sections(builder_text)
    if not sections:
        return _fail(["failed to extract workspace home layout.sections from builder"])

    errors: list[str] = []
    for key, tag in sections:
        if not key:
            continue
        enabled_token = f"isHomeSectionEnabled('{key}')"
        tag_token = f"isHomeSectionTag('{key}', '{tag}')"
        style_token = f"homeSectionStyle('{key}')"

        if enabled_token not in home_text:
            errors.append(f"missing home enabled token: {enabled_token}")
        if tag_token not in home_text:
            errors.append(f"missing home tag token: {tag_token}")
        if style_token not in home_text:
            errors.append(f"missing home style token: {style_token}")
        if tag == "details":
            open_token = f"isHomeSectionOpenDefault('{key}')"
            if open_token not in home_text:
                errors.append(f"missing home details open token: {open_token}")

    if errors:
        return _fail(errors)

    print(
        "[frontend_home_layout_section_coverage_guard] PASS "
        f"(checked_sections={len(sections)})"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
