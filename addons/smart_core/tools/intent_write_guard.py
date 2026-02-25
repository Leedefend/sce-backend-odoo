#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

import ast
import re
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
HANDLER_DIRS = [
    ROOT / "addons" / "smart_core" / "handlers",
    ROOT / "addons" / "smart_construction_core" / "handlers",
]
WRITE_HINT_PATTERN = re.compile(
    r"(create|write|unlink|delete|batch|execute|upload|cancel|approve|reject|submit|done|import|rollback|pin|set)",
    re.IGNORECASE,
)


def _literal(node):
    try:
        return ast.literal_eval(node)
    except Exception:
        return None


def _iter_handler_classes():
    for handler_dir in HANDLER_DIRS:
        if not handler_dir.is_dir():
            continue
        for path in sorted(handler_dir.glob("*.py")):
            tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
            for node in tree.body:
                if isinstance(node, ast.ClassDef):
                    yield path, node


def _extract_handler_meta(path: Path, cls: ast.ClassDef):
    intent_type = ""
    required_groups: list[str] = []
    non_idempotent_allowed = False
    for stmt in cls.body:
        if not isinstance(stmt, ast.Assign):
            continue
        for target in stmt.targets:
            if not isinstance(target, ast.Name):
                continue
            key = target.id
            value = _literal(stmt.value)
            if key == "INTENT_TYPE" and isinstance(value, str):
                intent_type = value.strip()
            elif key == "REQUIRED_GROUPS" and isinstance(value, list):
                required_groups = [str(x).strip() for x in value if str(x).strip()]
            elif key == "NON_IDEMPOTENT_ALLOWED":
                non_idempotent_allowed = bool(str(value or "").strip())
    if not intent_type:
        return None
    is_write = bool(WRITE_HINT_PATTERN.search(intent_type)) or non_idempotent_allowed
    return {
        "intent_type": intent_type,
        "required_groups": required_groups,
        "is_write": is_write,
        "source": str(path.relative_to(ROOT)),
        "class_name": cls.name,
    }


def main() -> int:
    violations = []
    scanned = 0
    write_count = 0
    for path, cls in _iter_handler_classes():
        meta = _extract_handler_meta(path, cls)
        if not meta:
            continue
        scanned += 1
        if not meta["is_write"]:
            continue
        write_count += 1
        if meta["required_groups"]:
            continue
        violations.append(meta)

    print(f"[intent_write_guard] scanned_handlers={scanned} write_handlers={write_count} violations={len(violations)}")
    if not violations:
        print("[intent_write_guard] PASS")
        return 0

    print("[intent_write_guard] FAIL write intents without REQUIRED_GROUPS:")
    for item in violations:
        print(
            f"- {item['intent_type']} ({item['source']}::{item['class_name']})"
        )
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
