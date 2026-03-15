#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

from pathlib import Path
import json


ROOT = Path(__file__).resolve().parents[2]
SYSTEM_INIT_PATH = ROOT / "addons" / "smart_core" / "handlers" / "system_init.py"
SESSION_PATH = ROOT / "frontend" / "apps" / "web" / "src" / "stores" / "session.ts"
STRATEGY_PATH = ROOT / "frontend" / "apps" / "web" / "src" / "app" / "sceneValidationRecoveryStrategy.ts"
FORM_PATH = ROOT / "frontend" / "apps" / "web" / "src" / "pages" / "ContractFormPage.vue"
BEHAVIOR_BASELINE_PATH = ROOT / "scripts" / "verify" / "baselines" / "scene_validation_recovery_strategy_behavior_smoke_guard.json"


def _assert(condition: bool, message: str, errors: list[str]) -> None:
    if not condition:
        errors.append(message)


def _index_of(text: str, token: str) -> int:
    try:
        return text.index(token)
    except ValueError:
        return -1


def _normalize_str_list(values: object, lower: bool = False) -> list[str]:
    if not isinstance(values, list):
        return []
    out: list[str] = []
    for item in values:
        value = str(item or "").strip()
        if not value:
            continue
        out.append(value.lower() if lower else value)
    return out


def _merge_strategy(base: dict[str, list[str]], ext: object) -> dict[str, list[str]]:
    row = ext if isinstance(ext, dict) else {}
    return {
        "preferredRecordModels": _normalize_str_list(row.get("preferredRecordModels"))
        if isinstance(row, dict) and isinstance(row.get("preferredRecordModels"), list)
        else list(base.get("preferredRecordModels", [])),
        "actionPreferredRoleTokens": _normalize_str_list(row.get("actionPreferredRoleTokens"), lower=True)
        if isinstance(row, dict) and isinstance(row.get("actionPreferredRoleTokens"), list)
        else list(base.get("actionPreferredRoleTokens", [])),
    }


def _resolve_runtime_strategy(payload: dict[str, object], runtime_context: dict[str, object]) -> dict[str, list[str]]:
    role_code = str(runtime_context.get("roleCode") or "").strip().lower()
    company_number = int(runtime_context.get("companyId") or 0)
    company_key = str(company_number) if company_number > 0 else ""
    base = _merge_strategy(
        {
            "preferredRecordModels": ["project.project", "project.task", "purchase.order", "account.move"],
            "actionPreferredRoleTokens": ["operator", "staff", "clerk"],
        },
        payload.get("default"),
    )
    resolved = {
        "preferredRecordModels": list(base["preferredRecordModels"]),
        "actionPreferredRoleTokens": list(base["actionPreferredRoleTokens"]),
    }

    by_company = payload.get("by_company") if isinstance(payload.get("by_company"), dict) else {}
    by_role = payload.get("by_role") if isinstance(payload.get("by_role"), dict) else {}
    by_company_role = payload.get("by_company_role") if isinstance(payload.get("by_company_role"), dict) else {}

    if company_key and isinstance(by_company, dict) and company_key in by_company:
        resolved = _merge_strategy(resolved, by_company.get(company_key))
    if role_code and isinstance(by_role, dict) and role_code in by_role:
        resolved = _merge_strategy(resolved, by_role.get(role_code))
    if company_key and role_code and isinstance(by_company_role, dict):
        key = f"{company_key}:{role_code}"
        if key in by_company_role:
            resolved = _merge_strategy(resolved, by_company_role.get(key))
    return resolved


def _resolve_action(strategy: dict[str, list[str]], ctx: dict[str, object]) -> str:
    model_name = str(ctx.get("modelName") or "").strip()
    role_code = str(ctx.get("roleCode") or "").strip().lower()
    scene_key = str(ctx.get("sceneKey") or "").strip()
    record_id = int(ctx.get("recordId") or 0)
    action_id = int(ctx.get("actionId") or 0)

    if record_id > 0 and model_name and model_name in strategy.get("preferredRecordModels", []):
        return f"open_record:{model_name}:{record_id}"
    if action_id > 0 and any(token in role_code for token in strategy.get("actionPreferredRoleTokens", [])):
        return f"open_action:{action_id}"
    if scene_key:
        return f"open_scene:{scene_key}"
    if action_id > 0:
        return f"open_action:{action_id}"
    return "copy_reason"


def main() -> int:
    errors: list[str] = []
    for path in (SYSTEM_INIT_PATH, SESSION_PATH, STRATEGY_PATH, FORM_PATH, BEHAVIOR_BASELINE_PATH):
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
    behavior_baseline = json.loads(BEHAVIOR_BASELINE_PATH.read_text(encoding="utf-8"))

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
        "open_record:${modelName}:${recordId}",
        "open_action:${actionId}",
        "open_scene:${sceneKey}",
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

    runtime_payload = behavior_baseline.get("runtime_payload") if isinstance(behavior_baseline, dict) else {}
    cases = behavior_baseline.get("cases") if isinstance(behavior_baseline, dict) else []
    _assert(isinstance(runtime_payload, dict), "behavior baseline missing runtime_payload object", errors)
    _assert(isinstance(cases, list) and len(cases) >= 3, "behavior baseline cases must include >= 3 scenarios", errors)
    if isinstance(runtime_payload, dict) and isinstance(cases, list):
        for row in cases:
            if not isinstance(row, dict):
                errors.append("behavior baseline case must be object")
                continue
            name = str(row.get("name") or "").strip() or "unnamed"
            runtime_context = row.get("runtime_context") if isinstance(row.get("runtime_context"), dict) else {}
            resolve_context = row.get("resolve_context") if isinstance(row.get("resolve_context"), dict) else {}
            expected = str(row.get("expected") or "").strip()
            if not expected:
                errors.append(f"behavior case missing expected output: {name}")
                continue
            runtime_strategy = _resolve_runtime_strategy(runtime_payload, runtime_context)
            actual = _resolve_action(runtime_strategy, resolve_context)
            if actual != expected:
                errors.append(f"behavior case mismatch [{name}] expected={expected} actual={actual}")

    if errors:
        print("[scene_validation_recovery_strategy_e2e_smoke_guard] FAIL")
        for item in errors:
            print(f" - {item}")
        return 1

    print("[scene_validation_recovery_strategy_e2e_smoke_guard] PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
