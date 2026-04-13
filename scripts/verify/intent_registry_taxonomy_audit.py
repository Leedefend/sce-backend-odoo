#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations

import ast
import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
ENTRY_MODULES_FILE = ROOT / "addons" / "smart_core" / "intents" / "registry_entries" / "__init__.py"
OUT = ROOT / "artifacts" / "architecture" / "intent_registry_taxonomy_audit_v1.json"
ALLOWED_CLASSES = {"system", "app", "ui", "meta", "api", "domain"}


def _load_entries_from_file(path: Path) -> list[dict[str, Any]]:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    for node in tree.body:
        if isinstance(node, ast.Assign) and len(node.targets) == 1 and isinstance(node.targets[0], ast.Name):
            if node.targets[0].id == "ENTRIES":
                value = ast.literal_eval(node.value)
                if isinstance(value, list):
                    return [item for item in value if isinstance(item, dict)]
    return []


def _load_entry_modules(path: Path) -> list[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    for node in tree.body:
        if isinstance(node, ast.Assign) and len(node.targets) == 1 and isinstance(node.targets[0], ast.Name):
            if node.targets[0].id == "ENTRY_MODULES":
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


def main() -> int:
    entries = _load_entries()
    invalid_class: list[str] = []
    invalid_canonical: list[str] = []

    for row in entries:
        intent_name = str(row.get("intent_name") or "").strip() or "<empty>"
        intent_class = str(row.get("intent_class") or "").strip().lower()
        canonical = str(row.get("canonical_intent") or "").strip()

        if intent_class not in ALLOWED_CLASSES:
            invalid_class.append(intent_name)

        if not canonical:
            invalid_canonical.append(f"{intent_name}:empty")
            continue
        if "." not in canonical:
            invalid_canonical.append(f"{intent_name}:missing_prefix")
            continue
        prefix = canonical.split(".", 1)[0].strip().lower()
        if prefix not in ALLOWED_CLASSES:
            invalid_canonical.append(f"{intent_name}:prefix={prefix}")

    payload = {
        "status": "PASS" if not invalid_class and not invalid_canonical else "FAIL",
        "entry_count": len(entries),
        "allowed_intent_classes": sorted(ALLOWED_CLASSES),
        "invalid_intent_class_entries": sorted(set(invalid_class)),
        "invalid_canonical_intent_entries": sorted(set(invalid_canonical)),
    }

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    if payload["status"] != "PASS":
        raise SystemExit("[verify.arch.intent_taxonomy] FAIL")

    print(f"[verify.arch.intent_taxonomy] PASS entries={payload['entry_count']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
