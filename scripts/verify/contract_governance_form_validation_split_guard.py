#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
GOVERNANCE = ROOT / "addons/smart_core/utils/contract_governance.py"
FORM_VALIDATION = ROOT / "addons/smart_core/utils/contract_governance_form_validation.py"
CI = ROOT / "make/ci.mk"

MAX_GOVERNANCE_LINES = 3073


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
    validation_text = _read(FORM_VALIDATION)
    ci_text = _read(CI)

    if not governance_text:
        errors.append(f"missing governance file: {GOVERNANCE.relative_to(ROOT)}")
    if not validation_text:
        errors.append(f"missing form validation module: {FORM_VALIDATION.relative_to(ROOT)}")

    if governance_text:
        line_count = len(governance_text.splitlines())
        if line_count > MAX_GOVERNANCE_LINES:
            errors.append(f"contract_governance.py line budget exceeded: {line_count} > {MAX_GOVERNANCE_LINES}")
        for token in [
            "def _load_form_validation_module()",
            "contract_governance_form_validation.py",
            "return _form_validation.build_form_validation_rules(",
            "return _form_validation.normalize_profile_list(raw, fallback)",
            "_form_validation.apply_business_form_policy(",
        ]:
            if token not in governance_text:
                errors.append(f"contract_governance.py missing form validation split token: {token}")

    if validation_text:
        for token in [
            "def normalize_profile_list(",
            "def build_form_validation_rules(",
            "def apply_business_form_policy(",
            '"SQL_CHECK"',
            '"REQUIRED"',
            '"business_form_policy"',
            '"required_profiles"',
        ]:
            if token not in validation_text:
                errors.append(f"form validation module missing token: {token}")
        for token in (".search(", ".write(", "requests.", "env[", "registry["):
            if token in validation_text:
                errors.append(f"form validation module must remain projection-only; found token: {token}")

    if "python3 scripts/verify/contract_governance_form_validation_split_guard.py" not in ci_text:
        errors.append("ci.local.quick must run contract_governance_form_validation_split_guard.py")

    if not errors:
        governance = _load(GOVERNANCE, "contract_governance_form_validation_split_under_guard")
        profiles = governance._normalize_profile_list(["create", "bogus", "edit", "create"], ["readonly"])
        if profiles != ["create", "edit"]:
            errors.append("profile normalization must keep valid unique profiles")

        data = {
            "fields": {
                "name": {"type": "char", "required": True, "string": "Name"},
                "code": {"type": "char", "string": "Code"},
                "readonly_field": {"type": "char", "readonly": True, "string": "Readonly"},
            },
            "validator": {
                "record_rules": {
                    "sql_checks": [
                        {"name": "uniq_code", "message": "Code must be unique", "definition": "unique(code)"},
                    ]
                }
            },
        }
        rules = governance._build_form_validation_rules(data, "hud")
        if not any(rule.get("code") == "REQUIRED" and rule.get("field") == "name" for rule in rules):
            errors.append("validation rules must include required editable fields")
        sql_rule = next((rule for rule in rules if rule.get("code") == "SQL_CHECK"), {})
        if sql_rule.get("expr") != "unique(code)":
            errors.append("hud validation rules must expose sql check expression")

        policy_data = {
            "fields": {
                "name": {"type": "char", "string": "Name"},
                "code": {"type": "char", "string": "Code"},
                "readonly_field": {"type": "char", "readonly": True, "string": "Readonly"},
            },
            "field_policies": {
                "code": {"visible_profiles": ["edit"], "readonly_profiles": ["readonly"], "group": "advanced"},
            },
            "validation_rules": [{"code": "REQUIRED", "field": "name"}],
            "business_form_policy": {
                "required_fields": ["code", "readonly_field"],
                "fields": [
                    {"name": "code", "visible_profiles": ["create", "edit"], "group": "core"},
                    {"name": "readonly_field", "required_profiles": ["create"], "source_readonly": True},
                ],
            },
        }
        governance._apply_business_form_policy(policy_data)
        code_policy = policy_data.get("field_policies", {}).get("code", {})
        readonly_policy = policy_data.get("field_policies", {}).get("readonly_field", {})
        if code_policy.get("required_profiles") != ["create", "edit"] or code_policy.get("group") != "core":
            errors.append("business form policy must merge required profiles and group")
        if readonly_policy.get("required_profiles"):
            errors.append("readonly business field must not remain required")
        if not any(rule.get("code") == "REQUIRED" and rule.get("field") == "code" for rule in policy_data.get("validation_rules", [])):
            errors.append("business form policy must append missing required validation rule")

    if errors:
        print("[contract_governance_form_validation_split_guard] FAIL")
        for error in errors:
            print(f"- {error}")
        return 1
    print("[contract_governance_form_validation_split_guard] PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
