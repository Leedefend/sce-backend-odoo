#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations

import ast
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
HANDLER_ROOT = ROOT / "addons" / "smart_core" / "handlers"
DISPATCHER_FILE = ROOT / "addons" / "smart_core" / "controllers" / "intent_dispatcher.py"
OUT = ROOT / "artifacts" / "architecture" / "intent_alias_duplication_audit_v1.json"


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
            if isinstance(node, ast.Assign) and len(node.targets) == 1 and isinstance(node.targets[0], ast.Name):
                if node.targets[0].id == "INTENT_TYPE" and isinstance(node.value, ast.Constant) and isinstance(node.value.value, str):
                    value = node.value.value.strip()
                    if value and value != "base.intent":
                        intents.append(value)
    return sorted(set(intents))


def _load_alias_map(path: Path) -> dict[str, str]:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    for node in tree.body:
        if isinstance(node, ast.Assign) and len(node.targets) == 1 and isinstance(node.targets[0], ast.Name):
            if node.targets[0].id == "INTENT_ALIASES":
                value = ast.literal_eval(node.value)
                if isinstance(value, dict):
                    return {str(k).strip(): str(v).strip() for k, v in value.items()}
    return {}


def main() -> int:
    handler_intents = _discover_handler_intents(HANDLER_ROOT)
    alias_map = _load_alias_map(DISPATCHER_FILE)

    canonical_to_aliases: dict[str, list[str]] = {}
    for alias, canonical in alias_map.items():
        canonical_to_aliases.setdefault(canonical, []).append(alias)

    missing_canonical_handlers = sorted(
        canonical for canonical in canonical_to_aliases if canonical not in set(handler_intents)
    )
    alias_to_self = sorted(alias for alias, canonical in alias_map.items() if alias == canonical)
    duplicate_semantic_surfaces = {
        canonical: sorted(set(aliases))
        for canonical, aliases in canonical_to_aliases.items()
        if len(set(aliases)) > 1
    }

    payload = {
        "status": "PASS",
        "handler_intent_count": len(handler_intents),
        "alias_count": len(alias_map),
        "alias_to_self": alias_to_self,
        "missing_canonical_handlers": missing_canonical_handlers,
        "duplicate_semantic_surfaces": duplicate_semantic_surfaces,
        "recommendation": {
            "next_step": "freeze one canonical intent per semantic surface and move aliases into compatibility layer",
            "priority_canonical_candidates": sorted(duplicate_semantic_surfaces.keys()),
        },
    }

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    print(
        "[verify.arch.intent_alias_duplication] PASS "
        f"handler_intents={payload['handler_intent_count']} "
        f"aliases={payload['alias_count']} "
        f"duplicate_surfaces={len(duplicate_semantic_surfaces)}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

