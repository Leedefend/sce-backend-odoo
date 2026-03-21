#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

import ast
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
HANDLER_FILE = ROOT / "addons" / "smart_core" / "handlers" / "scene_governance.py"
TARGETS = {
    "scene.governance.set_channel",
    "scene.governance.rollback",
    "scene.governance.pin_stable",
}
REQUIRED_GROUP = "smart_core.group_smart_core_scene_admin"
REQUIRED_ACL_MODE = "explicit_check"


def _literal(node):
    try:
        return ast.literal_eval(node)
    except Exception:
        return None


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


def main() -> int:
    if not HANDLER_FILE.is_file():
        print(f"[scene_governance_smoke] FAIL missing file: {HANDLER_FILE}")
        return 2

    tree = ast.parse(HANDLER_FILE.read_text(encoding="utf-8"), filename=str(HANDLER_FILE))
    classes = [node for node in tree.body if isinstance(node, ast.ClassDef)]
    class_map = {cls.name: cls for cls in classes}

    rows = {}
    for cls in classes:
        intent = _resolve_attr(class_map, cls, "INTENT_TYPE")
        if not isinstance(intent, str) or intent not in TARGETS:
            continue
        groups = _resolve_attr(class_map, cls, "REQUIRED_GROUPS") or []
        acl_mode = _resolve_attr(class_map, cls, "ACL_MODE")
        groups = [str(x).strip() for x in groups if str(x).strip()]
        rows[intent] = {
            "class_name": cls.name,
            "required_groups": groups,
            "acl_mode": str(acl_mode or "").strip(),
        }

    missing = sorted(TARGETS - set(rows.keys()))
    failures: list[str] = []
    for intent in sorted(TARGETS):
        row = rows.get(intent)
        if not row:
            continue
        if REQUIRED_GROUP not in row["required_groups"]:
            failures.append(f"{intent}: missing required group {REQUIRED_GROUP}")
        if row["acl_mode"] != REQUIRED_ACL_MODE:
            failures.append(f"{intent}: acl_mode={row['acl_mode']} expected={REQUIRED_ACL_MODE}")

    print(f"[scene_governance_smoke] targets={len(TARGETS)} resolved={len(rows)} failures={len(failures) + len(missing)}")
    if missing:
        for intent in missing:
            print(f"- missing handler for {intent}")
    if failures:
        for line in failures:
            print(f"- {line}")
    if missing or failures:
        print("[scene_governance_smoke] FAIL")
        return 2
    print("[scene_governance_smoke] PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
