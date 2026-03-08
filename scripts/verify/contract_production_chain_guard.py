#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Guard: enforce ui.contract as sole production contract intent chain."""

from __future__ import annotations

import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
HANDLER_REGISTRY = ROOT / "addons" / "smart_core" / "core" / "handler_registry.py"
INTENT_DISPATCHER = ROOT / "addons" / "smart_core" / "controllers" / "intent_dispatcher.py"
CONTROLLERS_INIT = ROOT / "addons" / "smart_core" / "controllers" / "__init__.py"
READINESS_POLICY = ROOT / "scripts" / "verify" / "baselines" / "business_increment_readiness_policy.json"
INTENT_SURFACE_GATE = ROOT / "addons" / "smart_construction_core" / "tests" / "test_intent_surface_coverage_gate.py"

LEGACY_INTENTS = {"ui.contract.enhanced", "ui.contract.model.view"}


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="ignore")


def _assert_file(path: Path, failures: list[str]) -> str:
    if not path.is_file():
        failures.append(f"missing file: {path.relative_to(ROOT).as_posix()}")
        return ""
    return _read(path)


def _contains_legacy_intent_literal(text: str) -> bool:
    return any(intent in text for intent in LEGACY_INTENTS)


def main() -> int:
    failures: list[str] = []

    registry_text = _assert_file(HANDLER_REGISTRY, failures)
    if registry_text and '"enhanced_" in name' not in registry_text:
        failures.append("handler_registry must skip enhanced_* modules from runtime registration")

    dispatcher_text = _assert_file(INTENT_DISPATCHER, failures)
    if dispatcher_text and "@http.route('/api/v1/intent'" not in dispatcher_text:
        failures.append("intent_dispatcher missing /api/v1/intent route")

    init_text = _assert_file(CONTROLLERS_INIT, failures)
    if init_text and "enhanced_intent_dispatcher" in init_text:
        failures.append("controllers/__init__.py must not import enhanced_intent_dispatcher")

    policy_text = _assert_file(READINESS_POLICY, failures)
    if policy_text and _contains_legacy_intent_literal(policy_text):
        failures.append("business_increment_readiness_policy must not require legacy enhanced intents")

    gate_text = _assert_file(INTENT_SURFACE_GATE, failures)
    if gate_text and _contains_legacy_intent_literal(gate_text):
        failures.append("intent_surface_coverage gate must not require legacy enhanced intents")

    # Ensure current production handler still declares ui.contract.
    ui_contract_path = ROOT / "addons" / "smart_core" / "handlers" / "ui_contract.py"
    ui_text = _assert_file(ui_contract_path, failures)
    if ui_text and 'INTENT_TYPE = "ui.contract"' not in ui_text:
        failures.append("ui_contract handler must declare INTENT_TYPE=ui.contract")

    if failures:
        print("[contract_production_chain_guard] FAIL")
        for item in failures:
            print(item)
        return 1

    print("[contract_production_chain_guard] PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
