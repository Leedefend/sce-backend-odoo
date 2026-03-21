#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

import ast
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
BASE_HANDLER = ROOT / "addons" / "smart_core" / "core" / "base_handler.py"
HANDLER_FILES = [
    ROOT / "addons" / "smart_core" / "handlers" / "api_data_write.py",
    ROOT / "addons" / "smart_core" / "handlers" / "api_data_unlink.py",
    ROOT / "addons" / "smart_core" / "handlers" / "execute_button.py",
    ROOT / "addons" / "smart_construction_core" / "handlers" / "payment_request_approval.py",
    ROOT / "addons" / "smart_core" / "handlers" / "scene_governance.py",
]
TARGETS = {
    "api.data.create": "smart_core.group_smart_core_data_operator",
    "api.data.unlink": "smart_core.group_smart_core_data_operator",
    "execute_button": "smart_core.group_smart_core_data_operator",
    "payment.request.submit": "smart_core.group_smart_core_finance_approver",
    "scene.governance.rollback": "smart_core.group_smart_core_scene_admin",
}


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


def _collect_intent_meta() -> dict[str, dict]:
    out: dict[str, dict] = {}
    for path in HANDLER_FILES:
        if not path.is_file():
            continue
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        classes = [node for node in tree.body if isinstance(node, ast.ClassDef)]
        class_map = {cls.name: cls for cls in classes}
        for cls in classes:
            intent = _resolve_attr(class_map, cls, "INTENT_TYPE")
            if not isinstance(intent, str):
                continue
            groups = _resolve_attr(class_map, cls, "REQUIRED_GROUPS") or []
            acl_mode = str(_resolve_attr(class_map, cls, "ACL_MODE") or "").strip()
            out[intent.strip()] = {
                "required_groups": [str(x).strip() for x in groups if str(x).strip()],
                "acl_mode": acl_mode,
                "source": str(path.relative_to(ROOT)),
            }
    return out


def _base_handler_guard_present() -> tuple[bool, bool]:
    text = BASE_HANDLER.read_text(encoding="utf-8") if BASE_HANDLER.is_file() else ""
    has_method = "def enforce_required_groups" in text
    has_run_gate = "if self.is_write():" in text and "self.enforce_required_groups()" in text
    return has_method, has_run_gate


def main() -> int:
    failures: list[str] = []
    catalog = _collect_intent_meta()

    has_method, has_run_gate = _base_handler_guard_present()
    if not has_method:
        failures.append("BaseIntentHandler missing enforce_required_groups()")
    if not has_run_gate:
        failures.append("BaseIntentHandler.run missing write-gate call to enforce_required_groups()")

    for intent, group in TARGETS.items():
        row = catalog.get(intent)
        if not row:
            failures.append(f"{intent}: handler not found")
            continue
        if group not in row["required_groups"]:
            failures.append(f"{intent}: missing required group {group}")
        if row["acl_mode"] not in {"record_rule", "explicit_check"}:
            failures.append(f"{intent}: invalid acl_mode '{row['acl_mode']}'")

    print(f"[intent_write_smoke] targets={len(TARGETS)} failures={len(failures)}")
    if failures:
        for line in failures:
            print(f"- {line}")
        print("[intent_write_smoke] FAIL")
        return 2
    print("[intent_write_smoke] PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
