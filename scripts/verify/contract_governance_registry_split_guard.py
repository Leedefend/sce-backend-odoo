#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
GOVERNANCE = ROOT / "addons/smart_core/utils/contract_governance.py"
REGISTRY = ROOT / "addons/smart_core/utils/contract_governance_registry.py"
CI = ROOT / "make/ci.mk"

MAX_GOVERNANCE_LINES = 4655

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

    if errors:
        print("[contract_governance_registry_split_guard] FAIL")
        for error in errors:
            print(f"- {error}")
        return 1
    print("[contract_governance_registry_split_guard] PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
