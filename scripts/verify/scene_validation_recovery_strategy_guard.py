#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

from pathlib import Path
import json


ROOT = Path(__file__).resolve().parents[2]
STRATEGY_PATH = ROOT / "frontend" / "apps" / "web" / "src" / "app" / "sceneValidationRecoveryStrategy.ts"
SESSION_PATH = ROOT / "frontend" / "apps" / "web" / "src" / "stores" / "session.ts"
FORM_PATH = ROOT / "frontend" / "apps" / "web" / "src" / "pages" / "ContractFormPage.vue"
SYSTEM_INIT_PATH = ROOT / "addons" / "smart_core" / "handlers" / "system_init.py"
BASELINE_PATH = ROOT / "scripts" / "verify" / "baselines" / "scene_validation_recovery_strategy_schema_guard.json"


def _assert(condition: bool, message: str, errors: list[str]) -> None:
    if not condition:
        errors.append(message)


def main() -> int:
    errors: list[str] = []
    for path in (STRATEGY_PATH, SESSION_PATH, FORM_PATH, SYSTEM_INIT_PATH, BASELINE_PATH):
        if not path.is_file():
            errors.append(f"missing file: {path}")
    if errors:
        print("[scene_validation_recovery_strategy_guard] FAIL")
        for item in errors:
            print(f" - {item}")
        return 1

    strategy_text = STRATEGY_PATH.read_text(encoding="utf-8")
    session_text = SESSION_PATH.read_text(encoding="utf-8")
    form_text = FORM_PATH.read_text(encoding="utf-8")
    system_init_text = SYSTEM_INIT_PATH.read_text(encoding="utf-8")
    baseline = json.loads(BASELINE_PATH.read_text(encoding="utf-8"))
    required_top_keys = baseline.get("required_top_keys") if isinstance(baseline.get("required_top_keys"), list) else []
    required_strategy_keys = baseline.get("required_strategy_keys") if isinstance(baseline.get("required_strategy_keys"), list) else []
    required_session_tokens = baseline.get("required_session_tokens") if isinstance(baseline.get("required_session_tokens"), list) else []

    for token in (
        "setSceneValidationRecoveryStrategy",
        "applySceneValidationRecoveryStrategyRuntime",
        "resolveSceneValidationSuggestedAction",
    ):
        _assert(token in strategy_text, f"strategy missing token: {token}", errors)

    for token in required_top_keys:
        _assert(str(token) in strategy_text, f"strategy missing schema top key: {token}", errors)

    for token in required_strategy_keys:
        _assert(str(token) in strategy_text, f"strategy missing schema strategy key: {token}", errors)

    _assert(
        "applySceneValidationRecoveryStrategyRuntime" in session_text,
        "session init missing runtime strategy wiring",
        errors,
    )
    for token in required_session_tokens:
        _assert(str(token) in session_text, f"session missing runtime strategy token: {token}", errors)

    _assert(
        "data[\"scene_validation_recovery_strategy\"]" in system_init_text,
        "system.init missing scene_validation_recovery_strategy output",
        errors,
    )
    _assert(
        "_load_scene_validation_recovery_strategy" in system_init_text,
        "system.init missing scene validation strategy loader",
        errors,
    )

    _assert(
        "resolveSceneValidationSuggestedAction" in form_text,
        "contract form missing strategy resolve hook",
        errors,
    )

    if errors:
        print("[scene_validation_recovery_strategy_guard] FAIL")
        for item in errors:
            print(f" - {item}")
        return 1

    print("[scene_validation_recovery_strategy_guard] PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
