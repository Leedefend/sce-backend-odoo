#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
STRATEGY_PATH = ROOT / "frontend" / "apps" / "web" / "src" / "app" / "sceneValidationRecoveryStrategy.ts"
SESSION_PATH = ROOT / "frontend" / "apps" / "web" / "src" / "stores" / "session.ts"
FORM_PATH = ROOT / "frontend" / "apps" / "web" / "src" / "pages" / "ContractFormPage.vue"


def _assert(condition: bool, message: str, errors: list[str]) -> None:
    if not condition:
        errors.append(message)


def main() -> int:
    errors: list[str] = []
    for path in (STRATEGY_PATH, SESSION_PATH, FORM_PATH):
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

    for token in (
        "setSceneValidationRecoveryStrategy",
        "applySceneValidationRecoveryStrategyRuntime",
        "resolveSceneValidationSuggestedAction",
        "by_role",
        "by_company",
        "by_company_role",
    ):
        _assert(token in strategy_text, f"strategy missing token: {token}", errors)

    _assert(
        "applySceneValidationRecoveryStrategyRuntime" in session_text,
        "session init missing runtime strategy wiring",
        errors,
    )
    _assert(
        "scene_validation_recovery_strategy" in session_text,
        "session init missing runtime strategy payload hook",
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
