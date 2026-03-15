#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

import importlib.util
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
CANONICALIZER_PATH = ROOT / "addons" / "smart_core" / "core" / "ui_base_contract_canonicalizer.py"
PRODUCER_PATH = ROOT / "addons" / "smart_core" / "core" / "ui_base_contract_asset_producer.py"
REPOSITORY_PATH = ROOT / "addons" / "smart_core" / "core" / "ui_base_contract_asset_repository.py"


def _assert(condition: bool, message: str, errors: list[str]) -> None:
    if not condition:
        errors.append(message)


def _load_module(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, str(path))
    if not spec or not spec.loader:
        return None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def main() -> int:
    errors: list[str] = []
    for path in (CANONICALIZER_PATH, PRODUCER_PATH, REPOSITORY_PATH):
        if not path.is_file():
            errors.append(f"missing file: {path}")
    if errors:
        print("[scene_ui_base_contract_canonicalizer_guard] FAIL")
        for item in errors:
            print(f" - {item}")
        return 1

    producer_text = PRODUCER_PATH.read_text(encoding="utf-8")
    repository_text = REPOSITORY_PATH.read_text(encoding="utf-8")
    _assert(
        "canonicalize_ui_base_contract" in producer_text,
        "producer missing canonicalizer wiring",
        errors,
    )
    _assert(
        "canonicalize_ui_base_contract" in repository_text,
        "repository missing canonicalizer wiring",
        errors,
    )

    module = _load_module(CANONICALIZER_PATH, "sc_ui_base_contract_canonicalizer")
    if module is None or not hasattr(module, "canonicalize_ui_base_contract"):
        errors.append("canonicalizer module missing canonicalize_ui_base_contract")
    else:
        canonicalize = module.canonicalize_ui_base_contract
        sample = {
            "views": {"form": {"statusbar": {"field": "state"}}},
            "fields": {"state": {"ttype": "selection"}},
            "toolbar": {"header": [{"key": "approve", "label": "Approve", "payload": {"method": "action_approve"}}]},
            "buttons": [{"key": "create", "label": "Create", "payload": {"method": "create"}}],
        }
        out = canonicalize(sample)
        _assert(isinstance(out, dict), "canonicalizer output must be dict", errors)
        for key in ("views", "fields", "search", "permissions", "workflow", "validator", "actions"):
            _assert(isinstance(out.get(key), dict), f"canonicalizer missing dict key: {key}", errors)
        action_items = out.get("actions", {}).get("items") if isinstance(out.get("actions"), dict) else []
        _assert(isinstance(action_items, list) and len(action_items) >= 2, "canonicalizer actions.items extraction failed", errors)
        workflow = out.get("workflow") if isinstance(out.get("workflow"), dict) else {}
        _assert(workflow.get("state_field") == "state", "canonicalizer workflow state_field fallback failed", errors)
        coverage = out.get("base_fact_coverage") if isinstance(out.get("base_fact_coverage"), dict) else {}
        _assert(bool(coverage), "canonicalizer missing base_fact_coverage", errors)

    if errors:
        print("[scene_ui_base_contract_canonicalizer_guard] FAIL")
        for item in errors:
            print(f" - {item}")
        return 1

    print("[scene_ui_base_contract_canonicalizer_guard] PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

