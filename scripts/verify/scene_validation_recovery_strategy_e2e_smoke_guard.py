#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SYSTEM_INIT_PATH = ROOT / "addons" / "smart_core" / "handlers" / "system_init.py"
SESSION_PATH = ROOT / "frontend" / "apps" / "web" / "src" / "stores" / "session.ts"
STRATEGY_PATH = ROOT / "frontend" / "apps" / "web" / "src" / "app" / "sceneValidationRecoveryStrategy.ts"
FORM_PATH = ROOT / "frontend" / "apps" / "web" / "src" / "pages" / "ContractFormPage.vue"


def _assert(condition: bool, message: str, errors: list[str]) -> None:
    if not condition:
        errors.append(message)


def _index_of(text: str, token: str) -> int:
    try:
        return text.index(token)
    except ValueError:
        return -1


def main() -> int:
    errors: list[str] = []
    for path in (SYSTEM_INIT_PATH, SESSION_PATH, STRATEGY_PATH, FORM_PATH):
        if not path.is_file():
            errors.append(f"missing file: {path}")
    if errors:
        print("[scene_validation_recovery_strategy_e2e_smoke_guard] FAIL")
        for item in errors:
            print(f" - {item}")
        return 1

    system_init_text = SYSTEM_INIT_PATH.read_text(encoding="utf-8")
    session_text = SESSION_PATH.read_text(encoding="utf-8")
    strategy_text = STRATEGY_PATH.read_text(encoding="utf-8")
    form_text = FORM_PATH.read_text(encoding="utf-8")

    _assert(
        "_load_scene_validation_recovery_strategy" in system_init_text,
        "backend missing strategy loader",
        errors,
    )
    _assert(
        'data["scene_validation_recovery_strategy"]' in system_init_text,
        "backend missing strategy payload output key",
        errors,
    )

    top_idx = _index_of(session_text, "validationStrategyRaw")
    ext_idx = _index_of(session_text, "extValidationStrategyRaw")
    apply_idx = _index_of(session_text, "applySceneValidationRecoveryStrategyRuntime(\n        validationStrategy")
    role_idx = _index_of(session_text, "roleCode: this.roleSurface.role_code")
    company_idx = _index_of(session_text, "companyId: resolveUserCompanyId(this.user)")

    _assert(top_idx >= 0, "session missing top-level strategy payload", errors)
    _assert(ext_idx >= 0, "session missing ext_facts fallback strategy payload", errors)
    _assert(apply_idx >= 0, "session missing runtime strategy apply invocation", errors)
    _assert(role_idx >= 0, "session runtime apply missing role context", errors)
    _assert(company_idx >= 0, "session runtime apply missing company context", errors)
    if top_idx >= 0 and ext_idx >= 0 and apply_idx >= 0:
        _assert(top_idx < ext_idx < apply_idx, "session strategy source resolution order invalid", errors)

    for token in (
        "SceneValidationRecoveryStrategyRuntimePayload",
        "by_role?",
        "by_company?",
        "by_company_role?",
        "applySceneValidationRecoveryStrategyRuntime",
        "resolveSceneValidationSuggestedAction",
    ):
        _assert(token in strategy_text, f"strategy module missing token: {token}", errors)

    company_merge_idx = _index_of(strategy_text, "payload?.by_company?.[companyKey]")
    role_merge_idx = _index_of(strategy_text, "payload?.by_role?.[roleCode]")
    company_role_merge_idx = _index_of(strategy_text, "payload?.by_company_role?.[key]")
    if company_merge_idx >= 0 and role_merge_idx >= 0 and company_role_merge_idx >= 0:
        _assert(
            company_merge_idx < role_merge_idx < company_role_merge_idx,
            "strategy runtime override precedence invalid",
            errors,
        )

    panel_idx = _index_of(form_text, "const sceneValidationPanel = computed(() =>")
    resolver_idx = _index_of(form_text, "resolveSceneValidationSuggestedAction({")
    hint_idx = _index_of(form_text, "suggestedAction,")
    _assert(panel_idx >= 0, "form page missing scene validation panel", errors)
    _assert(resolver_idx >= 0, "form page missing suggested action resolver", errors)
    _assert(hint_idx >= 0, "form page missing suggestedAction output", errors)
    if panel_idx >= 0 and resolver_idx >= 0 and hint_idx >= 0:
        _assert(panel_idx < resolver_idx < hint_idx, "form page suggested action wiring order invalid", errors)

    if errors:
        print("[scene_validation_recovery_strategy_e2e_smoke_guard] FAIL")
        for item in errors:
            print(f" - {item}")
        return 1

    print("[scene_validation_recovery_strategy_e2e_smoke_guard] PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
