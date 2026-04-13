#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations

import ast
import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
HANDLER_ROOT = ROOT / "addons" / "smart_core" / "handlers"
ENTRY_MODULES_FILE = ROOT / "addons" / "smart_core" / "intents" / "registry_entries" / "__init__.py"
OUT = ROOT / "artifacts" / "architecture" / "intent_registry_audit_v1.json"

REQUIRED_FIELDS = [
    "intent_name",
    "handler_class",
    "request_schema",
    "response_contract",
    "capability_code",
    "permission_mode",
    "idempotent",
    "version",
    "tags",
]


def _load_entries_from_file(path: Path) -> list[dict[str, Any]]:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    for node in tree.body:
        if not isinstance(node, ast.Assign):
            continue
        if len(node.targets) != 1 or not isinstance(node.targets[0], ast.Name):
            continue
        if node.targets[0].id != "ENTRIES":
            continue
        value = ast.literal_eval(node.value)
        if isinstance(value, list):
            return [item for item in value if isinstance(item, dict)]
    return []


def _load_entry_modules(path: Path) -> list[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    for node in tree.body:
        if not isinstance(node, ast.Assign):
            continue
        if len(node.targets) != 1 or not isinstance(node.targets[0], ast.Name):
            continue
        if node.targets[0].id != "ENTRY_MODULES":
            continue
        value = ast.literal_eval(node.value)
        if isinstance(value, list):
            return [str(item).strip() for item in value if str(item).strip()]
    return []


def _module_to_file(module_name: str) -> Path:
    return ROOT / (module_name.replace(".", "/") + ".py")


def _load_entries() -> list[dict[str, Any]]:
    modules = _load_entry_modules(ENTRY_MODULES_FILE)
    entries: list[dict[str, Any]] = []
    for module_name in modules:
        file_path = _module_to_file(module_name)
        if not file_path.exists():
            continue
        entries.extend(_load_entries_from_file(file_path))
    return entries


def _discover_handler_intents(handler_root: Path) -> list[str]:
    intents: list[str] = []
    for path in sorted(handler_root.rglob("*.py")):
        if path.name.startswith("_"):
            continue
        try:
            tree = ast.parse(path.read_text(encoding="utf-8"))
        except Exception:
            continue
        for node in ast.walk(tree):
            if not isinstance(node, ast.Assign):
                continue
            if len(node.targets) != 1 or not isinstance(node.targets[0], ast.Name):
                continue
            if node.targets[0].id != "INTENT_TYPE":
                continue
            if isinstance(node.value, ast.Constant) and isinstance(node.value.value, str):
                value = node.value.value.strip()
                if value and value != "base.intent":
                    intents.append(value)
    return sorted(set(intents))


def main() -> int:
    entries = _load_entries()
    discovered = _discover_handler_intents(HANDLER_ROOT)

    entry_names = [str(item.get("intent_name") or "").strip() for item in entries]
    duplicates = sorted({name for name in entry_names if name and entry_names.count(name) > 1})

    invalid_entries: list[str] = []
    for item in entries:
        intent_name = str(item.get("intent_name") or "").strip() or "<empty>"
        missing = [field for field in REQUIRED_FIELDS if field not in item or item.get(field) in ("", None)]
        if missing:
            invalid_entries.append(f"{intent_name}:missing={','.join(missing)}")

    registered = {name for name in entry_names if name}
    discovered_set = set(discovered)
    missing_from_registry = sorted(discovered_set - registered)
    stale_registry_entries = sorted(registered - discovered_set)

    status = "PASS" if not duplicates and not invalid_entries else "FAIL"
    payload = {
        "status": status,
        "structure": {
            "entry_count": len(entries),
            "duplicates": duplicates,
            "invalid_entries": invalid_entries,
        },
        "coverage": {
            "discovered_handler_intent_count": len(discovered_set),
            "registered_intent_count": len(registered),
            "missing_from_registry": missing_from_registry,
            "stale_registry_entries": stale_registry_entries,
        },
        "note": "coverage gaps are expected in skeleton phase and reported for next migration batches",
    }

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    if status != "PASS":
        raise SystemExit("[verify.arch.intent_registry_unique] FAIL")

    print(
        "[verify.arch.intent_registry_unique] PASS "
        f"registered={payload['coverage']['registered_intent_count']} "
        f"discovered={payload['coverage']['discovered_handler_intent_count']} "
        f"missing={len(payload['coverage']['missing_from_registry'])}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
