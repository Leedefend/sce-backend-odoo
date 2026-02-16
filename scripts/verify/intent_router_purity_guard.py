#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

import ast
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[2]

# Guard only core intent-layer files. Business extensions may legitimately register
# industry intents in their own modules.
TARGET_FILES = (
    ROOT / "addons/smart_core/core/intent_router.py",
    ROOT / "addons/smart_core/core/enhanced_intent_router.py",
    ROOT / "addons/smart_core/controllers/intent_dispatcher.py",
    ROOT / "addons/smart_core/controllers/enhanced_intent_dispatcher.py",
)

FORBIDDEN_KEYWORDS = (
    "project.",
    "material.",
    "settlement.",
    "boq.",
    "payment.request",
)


def _iter_string_literals(tree: ast.AST):
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            yield node.value, getattr(node, "lineno", 0)
        elif isinstance(node, ast.JoinedStr):
            for part in node.values:
                if isinstance(part, ast.Constant) and isinstance(part.value, str):
                    yield part.value, getattr(part, "lineno", getattr(node, "lineno", 0))


def main() -> int:
    violations: list[str] = []
    for path in TARGET_FILES:
        if not path.is_file():
            violations.append(f"missing file: {path.relative_to(ROOT).as_posix()}")
            continue
        text = path.read_text(encoding="utf-8", errors="ignore")
        try:
            tree = ast.parse(text)
        except SyntaxError as exc:
            violations.append(f"{path.relative_to(ROOT).as_posix()}: syntax error while parsing: {exc}")
            continue
        rel = path.relative_to(ROOT).as_posix()
        for literal, lineno in _iter_string_literals(tree):
            lowered = literal.lower()
            for keyword in FORBIDDEN_KEYWORDS:
                if keyword in lowered:
                    violations.append(f"{rel}:{lineno}: forbidden industry keyword in intent layer: {keyword}")

    if violations:
        print("[intent_router_purity_guard] FAIL")
        for item in violations:
            print(item)
        return 1

    print("[intent_router_purity_guard] PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
