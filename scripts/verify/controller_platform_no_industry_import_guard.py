#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

import ast
import json
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[2]
CONTROLLERS_ROOT = ROOT / "addons" / "smart_core" / "controllers"
ARTIFACT_JSON = ROOT / "artifacts" / "controller_platform_no_industry_import_guard.json"
FORBIDDEN_PREFIX = "odoo.addons.smart_construction_core.controllers"


def _iter_py_files():
    for path in sorted(CONTROLLERS_ROOT.rglob("*.py")):
        if path.name == "__init__.py":
            continue
        yield path


def _violations_for_file(path: Path) -> list[str]:
    text = path.read_text(encoding="utf-8", errors="ignore")
    try:
        tree = ast.parse(text)
    except SyntaxError as exc:
        return [f"{path.relative_to(ROOT).as_posix()}: syntax error: {exc}"]

    violations: list[str] = []
    rel = path.relative_to(ROOT).as_posix()
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom):
            mod = node.module or ""
            if mod.startswith(FORBIDDEN_PREFIX):
                violations.append(f"{rel}:{node.lineno}: forbidden import-from {mod}")
        elif isinstance(node, ast.Import):
            for alias in node.names:
                name = alias.name or ""
                if name.startswith(FORBIDDEN_PREFIX):
                    violations.append(f"{rel}:{node.lineno}: forbidden import {name}")
    return violations


def main() -> int:
    violations: list[str] = []
    scanned = 0
    for file_path in _iter_py_files():
        scanned += 1
        violations.extend(_violations_for_file(file_path))

    report = {
        "ok": not violations,
        "summary": {
            "controller_root": CONTROLLERS_ROOT.relative_to(ROOT).as_posix(),
            "scanned_file_count": scanned,
            "violation_count": len(violations),
            "forbidden_prefix": FORBIDDEN_PREFIX,
        },
        "violations": violations,
    }
    ARTIFACT_JSON.parent.mkdir(parents=True, exist_ok=True)
    ARTIFACT_JSON.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(str(ARTIFACT_JSON))
    if violations:
        print("[controller_platform_no_industry_import_guard] FAIL")
        for item in violations:
            print(item)
        return 1

    print("[controller_platform_no_industry_import_guard] PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
