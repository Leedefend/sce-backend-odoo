#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

import ast
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
SOURCE_KIND = "intent_write_static_guard"
SOURCE_AUTHORITIES = ("smart_core.handlers", "python_ast")
NO_BUSINESS_FACT_AUTHORITY = True


def source_authority_contract() -> dict:
    return {
        "kind": SOURCE_KIND,
        "authorities": list(SOURCE_AUTHORITIES),
        "projection_only": True,
        "rebuildable": True,
        "no_business_fact_authority": NO_BUSINESS_FACT_AUTHORITY,
        "static_guard_only": True,
    }


def _handler_dirs():
    addons_root = ROOT / "addons"
    if not addons_root.is_dir():
        return []
    return [path for path in sorted(addons_root.glob("*/handlers")) if path.is_dir()]
WRITE_INTENT_TOKENS = {
    "approve", "batch", "cancel", "complete", "create", "delete", "done",
    "execute", "freeze", "import", "pin", "promote", "publish", "reject",
    "rollback", "save", "schedule", "set", "submit", "sync", "track",
    "unlink", "update", "upload", "write",
}


def _literal(node, module_constants: dict[str, object] | None = None):
    module_constants = module_constants or {}
    if isinstance(node, ast.Name):
        return module_constants.get(node.id)
    if isinstance(node, ast.List):
        return [_literal(item, module_constants) for item in node.elts]
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
            module_constants = _module_constants(tree)
            class_defs = [node for node in tree.body if isinstance(node, ast.ClassDef)]
            if class_defs:
                yield path, class_defs, module_constants


def _module_constants(tree: ast.Module) -> dict[str, object]:
    out: dict[str, object] = {}
    for stmt in tree.body:
        if not isinstance(stmt, ast.Assign):
            continue
        value = _literal(stmt.value, out)
        if value is None:
            continue
        for target in stmt.targets:
            if isinstance(target, ast.Name):
                out[target.id] = value
    return out


def _class_attr_literal(cls: ast.ClassDef, attr_name: str, module_constants: dict[str, object]):
    for stmt in cls.body:
        if not isinstance(stmt, ast.Assign):
            continue
        for target in stmt.targets:
            if isinstance(target, ast.Name) and target.id == attr_name:
                return _literal(stmt.value, module_constants)
    return None


def _resolve_required_groups(
    class_map: dict[str, ast.ClassDef],
    cls: ast.ClassDef,
    module_constants: dict[str, object],
    visited: set[str] | None = None,
) -> list[str]:
    visited = visited or set()
    if cls.name in visited:
        return []
    visited.add(cls.name)
    value = _class_attr_literal(cls, "REQUIRED_GROUPS", module_constants)
    if isinstance(value, list):
        return [str(x).strip() for x in value if str(x).strip()]
    for base in cls.bases:
        if isinstance(base, ast.Name):
            base_cls = class_map.get(base.id)
            if base_cls is not None:
                inherited = _resolve_required_groups(class_map, base_cls, module_constants, visited=visited)
                if inherited:
                    return inherited
    return []


def _is_write_intent(intent_type: str, *, non_idempotent: bool = False) -> bool:
    if non_idempotent:
        return True
    tokens = [token for token in re_split(intent_type) if token]
    return any(token in WRITE_INTENT_TOKENS for token in tokens)


def re_split(value: str) -> list[str]:
    import re

    return re.split(r"[._:-]+", str(value or "").strip().lower())


def _extract_handler_meta(path: Path, cls: ast.ClassDef, class_map: dict[str, ast.ClassDef], module_constants: dict[str, object]):
    intent_type = ""
    required_groups: list[str] = _resolve_required_groups(class_map, cls, module_constants)
    non_idempotent_allowed = False
    for stmt in cls.body:
        if not isinstance(stmt, ast.Assign):
            continue
        for target in stmt.targets:
            if not isinstance(target, ast.Name):
                continue
            key = target.id
            value = _literal(stmt.value, module_constants)
            if key == "INTENT_TYPE" and isinstance(value, str):
                intent_type = value.strip()
            elif key == "REQUIRED_GROUPS" and isinstance(value, list):
                required_groups = [str(x).strip() for x in value if str(x).strip()]
            elif key == "NON_IDEMPOTENT_ALLOWED":
                non_idempotent_allowed = bool(str(value or "").strip())
    if not intent_type:
        return None
    is_write = _is_write_intent(intent_type, non_idempotent=non_idempotent_allowed)
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
    for path, classes, module_constants in _iter_handler_classes():
        class_map = {cls.name: cls for cls in classes}
        for cls in classes:
            meta = _extract_handler_meta(path, cls, class_map, module_constants)
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
