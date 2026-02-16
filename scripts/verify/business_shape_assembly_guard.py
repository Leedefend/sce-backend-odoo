#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

import ast
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[2]
HANDLERS_ROOT = ROOT / "addons/smart_construction_core/handlers"
FORBIDDEN_SHAPE_KEYS = {"scenes", "capabilities", "layout", "tiles"}


def _iter_handler_files():
    if not HANDLERS_ROOT.is_dir():
        return
    for path in HANDLERS_ROOT.rglob("*.py"):
        yield path


def _dict_keys(node: ast.Dict) -> set[str]:
    keys: set[str] = set()
    for key in node.keys:
        if isinstance(key, ast.Constant) and isinstance(key.value, str):
            keys.add(str(key.value))
    return keys


def _subscript_key(node: ast.Subscript) -> str | None:
    slice_node = node.slice
    if isinstance(slice_node, ast.Constant) and isinstance(slice_node.value, str):
        return str(slice_node.value)
    return None


def main() -> int:
    if not HANDLERS_ROOT.is_dir():
        print("[business_shape_assembly_guard] FAIL")
        print(f"missing dir: {HANDLERS_ROOT.relative_to(ROOT).as_posix()}")
        return 1

    violations: list[str] = []
    for path in _iter_handler_files():
        rel = path.relative_to(ROOT).as_posix()
        text = path.read_text(encoding="utf-8", errors="ignore")
        try:
            tree = ast.parse(text)
        except SyntaxError:
            continue

        for node in ast.walk(tree):
            if isinstance(node, ast.Return) and isinstance(node.value, ast.Dict):
                hits = sorted(_dict_keys(node.value) & FORBIDDEN_SHAPE_KEYS)
                for hit in hits:
                    violations.append(
                        f"{rel}:{node.lineno}: forbidden runtime shape key in handler return dict: {hit}"
                    )
            if isinstance(node, ast.Assign):
                for target in node.targets:
                    if not isinstance(target, ast.Subscript):
                        continue
                    if not isinstance(target.value, ast.Name) or target.value.id != "data":
                        continue
                    key = _subscript_key(target)
                    if key in FORBIDDEN_SHAPE_KEYS:
                        violations.append(
                            f"{rel}:{node.lineno}: forbidden runtime shape key write data['{key}'] in handler"
                        )

    if violations:
        print("[business_shape_assembly_guard] FAIL")
        for item in violations:
            print(item)
        return 1

    print("[business_shape_assembly_guard] PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
