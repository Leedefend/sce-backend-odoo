#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
GOVERNANCE = ROOT / "addons/smart_core/utils/contract_governance.py"
REGISTRY = ROOT / "addons/smart_core/utils/contract_governance_registry.py"
CI = ROOT / "make/ci.mk"

MAX_GOVERNANCE_LINES = 4490

REQUIRED_EXPORTS = [
    "SOURCE_KIND",
    "SOURCE_AUTHORITIES",
    "NO_BUSINESS_FACT_AUTHORITY",
    "LEGACY_RECORD_CONTEXT_CLEAR_MODELS",
    "LEGACY_DELETE_ONLY_MODELS",
    "_LEGACY_STANDARD_LIST_PROFILE_REGISTRY",
    "_LEGACY_FIELD_PRESENTATION_REGISTRY",
    "_LEGACY_PROJECT_FORM_GOVERNANCE_MODELS",
    "_LEGACY_PROJECT_FORM_PROFILE_REGISTRY",
    "_LEGACY_PROJECT_TASK_FORM_GOVERNANCE_MODELS",
    "_LEGACY_PROJECT_KANBAN_GOVERNANCE_MODELS",
    "_LEGACY_PROJECT_TASK_FORM_PROFILE_REGISTRY",
    "_LEGACY_PROJECT_KANBAN_PROFILE_REGISTRY",
    "_LEGACY_KANBAN_ROW_ACTION_REGISTRY",
    "_CAPABILITY_GROUP_PROFILE_REGISTRY",
    "_SCENE_SEMANTIC_PROFILE_REGISTRY",
    "CONTRACT_MODES",
    "CONTRACT_SURFACES",
    "_USER_SURFACE_PRIMARY_ACTION_MAX",
    "_FORM_CORE_FIELD_MAX",
    "_FORM_ACTION_PRIMARY_KEYWORDS",
    "_FORM_ACTION_READONLY_KEYWORDS",
    "_FORM_PRIMARY_DISABLED_REASON",
    "_FORM_DISABLED_REASON_CAPABILITY",
    "_FORM_DISABLED_REASON_LIFECYCLE",
    "_FORM_DISABLED_REASON_GROUP",
    "_FORM_DISABLED_REASON_ROLE",
    "_FORM_SCENE_PROFILE_DEFAULT",
    "_FORM_SCENE_PROFILE_PROJECT",
    "_CAPABILITY_GROUP_DEFAULTS",
    "_CONTRACT_KEY_CANONICAL_MAP",
]


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="ignore") if path.is_file() else ""


def _load(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"unable to load {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def main() -> int:
    errors: list[str] = []
    governance_text = _read(GOVERNANCE)
    registry_text = _read(REGISTRY)
    ci_text = _read(CI)

    if not governance_text:
        errors.append(f"missing governance file: {GOVERNANCE.relative_to(ROOT)}")
    if not registry_text:
        errors.append(f"missing registry module: {REGISTRY.relative_to(ROOT)}")

    if governance_text:
        line_count = len(governance_text.splitlines())
        if line_count > MAX_GOVERNANCE_LINES:
            errors.append(f"contract_governance.py line budget exceeded: {line_count} > {MAX_GOVERNANCE_LINES}")
        for token in [
            "def _load_registry_module()",
            "contract_governance_registry.py",
            "globals().update({name: getattr(_registry, name) for name in _REGISTRY_EXPORTS})",
            "NO_BUSINESS_FACT_AUTHORITY = True is defined in contract_governance_registry.py",
            "_registry.register_legacy_standard_list_profile(profile)",
            "_registry.register_legacy_project_form_profile(",
            "_registry.register_legacy_kanban_row_action(model_name, action)",
        ]:
            if token not in governance_text:
                errors.append(f"contract_governance.py missing split compatibility token: {token}")

    if registry_text:
        for token in [
            "SOURCE_KIND = \"ui_contract_governance_projection\"",
            "NO_BUSINESS_FACT_AUTHORITY = True",
            "LEGACY_DELETE_ONLY_MODELS = {\"res.company\", \"hr.department\", \"res.users\"}",
            "_LEGACY_STANDARD_LIST_PROFILE_REGISTRY: list[dict[str, Any]] = []",
            "_RENDER_PROFILE_READONLY = \"readonly\"",
            "_FORM_ACTION_PRIMARY_KEYWORDS = (",
            "_CONTRACT_KEY_CANONICAL_MAP = {",
            "def register_legacy_standard_list_profile(",
            "def register_legacy_project_form_profile(",
            "def register_legacy_kanban_row_action(",
            "def register_scene_semantic_profile(",
        ]:
            if token not in registry_text:
                errors.append(f"contract_governance_registry.py missing registry token: {token}")

    if "python3 scripts/verify/contract_governance_registry_split_guard.py" not in ci_text:
        errors.append("ci.local.quick must run contract_governance_registry_split_guard.py")

    if not errors:
        registry = _load(REGISTRY, "contract_governance_registry_under_guard")
        governance = _load(GOVERNANCE, "contract_governance_under_guard")
        loaded_registry = getattr(governance, "_registry", None)
        for name in REQUIRED_EXPORTS:
            if not hasattr(registry, name):
                errors.append(f"registry module missing export: {name}")
            if not hasattr(governance, name):
                errors.append(f"contract_governance.py missing compatibility export: {name}")
            elif loaded_registry is not None and getattr(governance, name) is not getattr(loaded_registry, name):
                errors.append(f"compatibility export must reference loaded registry object: {name}")
        before = set(governance.LEGACY_RECORD_CONTEXT_CLEAR_MODELS)
        governance.register_legacy_record_context_clear_model("guard.model")
        if loaded_registry is None or "guard.model" not in loaded_registry.LEGACY_RECORD_CONTEXT_CLEAR_MODELS:
            errors.append("registry mutation through contract_governance.py did not update registry module object")
        governance.LEGACY_RECORD_CONTEXT_CLEAR_MODELS.clear()
        governance.LEGACY_RECORD_CONTEXT_CLEAR_MODELS.update(before)
        active_registry = loaded_registry or registry
        active_registry._LEGACY_STANDARD_LIST_PROFILE_REGISTRY.clear()
        governance.register_legacy_standard_list_profile(
            {
                "model_name": "guard.model",
                "columns_order": ["name", "", "state"],
                "column_labels": {"name": "Name", "": "Ignored"},
                "profile_key": "guard.profile",
            }
        )
        if active_registry._LEGACY_STANDARD_LIST_PROFILE_REGISTRY[0].get("columns_order") != ["name", "state"]:
            errors.append("standard list profile registration must normalize columns in registry module")
        governance.register_legacy_project_form_profile(
            "guard.project",
            {
                "primary_fields": ["name", ""],
                "action_noise_markers": [" Demo "],
                "search_noise_markers": [" Filter "],
                "action_group_labels": {"main": "Main", "": "Ignored"},
            },
        )
        project_profile = active_registry._LEGACY_PROJECT_FORM_PROFILE_REGISTRY.get("guard.project") or {}
        if project_profile.get("action_noise_markers") != ["demo"]:
            errors.append("project form profile registration must lowercase action noise markers in registry module")
        if project_profile.get("action_group_labels") != {"main": "Main"}:
            errors.append("project form profile registration must normalize action group labels in registry module")
        action = {"name": "open", "target": {"route": "/guard"}}
        governance.register_legacy_kanban_row_action("guard.project", action)
        action["target"]["route"] = "/mutated"
        registered_action = (active_registry._LEGACY_KANBAN_ROW_ACTION_REGISTRY.get("guard.project") or [{}])[0]
        if registered_action.get("key") != "open" or registered_action.get("target", {}).get("route") != "/guard":
            errors.append("kanban row action registration must clone and normalize action rows in registry module")
        governance.register_scene_semantic_profile(
            {"purpose": "guard", "code_prefixes": [" Demo "], "code_contains": [" Flow "]}
        )
        if active_registry._SCENE_SEMANTIC_PROFILE_REGISTRY[-1].get("code_prefixes") != ("demo",):
            errors.append("scene semantic profile registration must normalize code prefixes in registry module")

    if errors:
        print("[contract_governance_registry_split_guard] FAIL")
        for error in errors:
            print(f"- {error}")
        return 1
    print("[contract_governance_registry_split_guard] PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
