#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

import ast
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[2]
SCAN_DIRS = (
    ROOT / "addons/smart_core",
    ROOT / "addons/smart_construction_core",
    ROOT / "addons/smart_construction_scene",
    ROOT / "addons/smart_construction_portal",
)
FORBIDDEN_PREFIXES = ("odoo.addons.smart_construction_demo", "odoo.addons.smart_construction_seed")


def _iter_py_files():
    for base in SCAN_DIRS:
        if not base.is_dir():
            continue
        for path in base.rglob("*.py"):
            rel = path.relative_to(ROOT).as_posix()
            if "/tests/" in rel:
                continue
            yield path


def _is_forbidden(module: str) -> bool:
    text = str(module or "").strip()
    if not text:
        return False
    return any(text.startswith(prefix) for prefix in FORBIDDEN_PREFIXES)


def main() -> int:
    violations: list[str] = []
    for path in _iter_py_files():
        rel = path.relative_to(ROOT).as_posix()
        try:
            tree = ast.parse(path.read_text(encoding="utf-8", errors="ignore"))
        except SyntaxError as exc:
            violations.append(f"{rel}: syntax error while parsing: {exc}")
            continue
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    mod = str(alias.name or "").strip()
                    if _is_forbidden(mod):
                        violations.append(f"{rel}:{getattr(node, 'lineno', 0)} forbidden import: {mod}")
            elif isinstance(node, ast.ImportFrom):
                mod = str(node.module or "").strip()
                if _is_forbidden(mod):
                    violations.append(f"{rel}:{getattr(node, 'lineno', 0)} forbidden import-from: {mod}")

    if violations:
        print("[seed_demo_import_boundary_guard] FAIL")
        for item in violations:
            print(item)
        return 1

    print("[seed_demo_import_boundary_guard] PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
