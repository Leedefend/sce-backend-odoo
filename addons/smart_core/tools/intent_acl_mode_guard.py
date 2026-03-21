#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

import ast
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]


def _handler_dirs():
    addons_root = ROOT / "addons"
    if not addons_root.is_dir():
        return []
    return [path for path in sorted(addons_root.glob("*/handlers")) if path.is_dir()]
ALLOWED_ACL_MODES = {"record_rule", "explicit_check"}
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
    for handler_dir in _handler_dirs():
        if not handler_dir.is_dir():
            continue
        for path in sorted(handler_dir.glob("*.py")):
            tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
            classes = [node for node in tree.body if isinstance(node, ast.ClassDef)]
            if classes:
                yield path, classes


def _class_attr_literal(cls: ast.ClassDef, attr_name: str):
    for stmt in cls.body:
        if not isinstance(stmt, ast.Assign):
            continue
        for target in stmt.targets:
            if isinstance(target, ast.Name) and target.id == attr_name:
                return _literal(stmt.value)
    return None


def _resolve_attr(class_map: dict[str, ast.ClassDef], cls: ast.ClassDef, attr_name: str, visited: set[str] | None = None):
    visited = visited or set()
    if cls.name in visited:
        return None
    visited.add(cls.name)
    value = _class_attr_literal(cls, attr_name)
    if value is not None:
        return value
    for base in cls.bases:
        if isinstance(base, ast.Name):
            base_cls = class_map.get(base.id)
            if base_cls is not None:
                inherited = _resolve_attr(class_map, base_cls, attr_name, visited=visited)
                if inherited is not None:
                    return inherited
    return None


def _meta(path: Path, cls: ast.ClassDef, class_map: dict[str, ast.ClassDef]):
    intent_type = _resolve_attr(class_map, cls, "INTENT_TYPE")
    if not isinstance(intent_type, str) or not intent_type.strip():
        return None
    non_idempotent_allowed = bool(str(_resolve_attr(class_map, cls, "NON_IDEMPOTENT_ALLOWED") or "").strip())
    is_write = bool(WRITE_HINT_PATTERN.search(intent_type)) or non_idempotent_allowed
    acl_mode = _resolve_attr(class_map, cls, "ACL_MODE")
    if isinstance(acl_mode, str):
        acl_mode = acl_mode.strip()
    else:
        acl_mode = ""
    return {
        "intent_type": intent_type.strip(),
        "is_write": is_write,
        "acl_mode": acl_mode,
        "source": str(path.relative_to(ROOT)),
        "class_name": cls.name,
    }


def main() -> int:
    scanned = 0
    write_count = 0
    violations = []
    for path, classes in _iter_handler_classes():
        class_map = {cls.name: cls for cls in classes}
        for cls in classes:
            meta = _meta(path, cls, class_map)
            if not meta:
                continue
            scanned += 1
            if not meta["is_write"]:
                continue
            write_count += 1
            if meta["acl_mode"] in ALLOWED_ACL_MODES:
                continue
            violations.append(meta)

    print(f"[intent_acl_mode_guard] scanned_handlers={scanned} write_handlers={write_count} violations={len(violations)}")
    if not violations:
        print("[intent_acl_mode_guard] PASS")
        return 0

    print("[intent_acl_mode_guard] FAIL write intents missing/invalid ACL_MODE:")
    for item in violations:
        print(
            f"- {item['intent_type']} ({item['source']}::{item['class_name']}) acl_mode='{item['acl_mode']}'"
        )
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
