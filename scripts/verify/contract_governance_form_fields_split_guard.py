#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
GOVERNANCE = ROOT / "addons/smart_core/utils/contract_governance.py"
FORM_FIELDS = ROOT / "addons/smart_core/utils/contract_governance_form_fields.py"
CI = ROOT / "make/ci.mk"

MAX_GOVERNANCE_LINES = 2930


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
    fields_text = _read(FORM_FIELDS)
    ci_text = _read(CI)

    if not governance_text:
        errors.append(f"missing governance file: {GOVERNANCE.relative_to(ROOT)}")
    if not fields_text:
        errors.append(f"missing form fields module: {FORM_FIELDS.relative_to(ROOT)}")

    if governance_text:
        line_count = len(governance_text.splitlines())
        if line_count > MAX_GOVERNANCE_LINES:
            errors.append(f"contract_governance.py line budget exceeded: {line_count} > {MAX_GOVERNANCE_LINES}")
        for token in [
            "def _load_form_fields_module()",
            "contract_governance_form_fields.py",
            "return _form_fields.iter_field_order(data)",
            "return _form_fields.derive_form_core_fields(",
            "_form_fields.apply_form_field_groups(",
            "return _form_fields.resolve_contract_required_fields(",
            "return _form_fields.build_form_field_policies(",
        ]:
            if token not in governance_text:
                errors.append(f"contract_governance.py missing form fields split token: {token}")

    if fields_text:
        for token in [
            "def iter_field_order(",
            "def derive_form_core_fields(",
            "def apply_form_field_groups(",
            "def resolve_contract_required_fields(",
            "def build_form_field_policies(",
            "_BUSINESS_DETAIL_RELATION_FIELDS",
            "_FORM_CORE_FIELD_MAX",
            '"source_required"',
        ]:
            if token not in fields_text:
                errors.append(f"form fields module missing token: {token}")
        for token in (".search(", ".write(", "requests.", "env[", "registry["):
            if token in fields_text:
                errors.append(f"form fields module must remain projection-only; found token: {token}")

    if "python3 scripts/verify/contract_governance_form_fields_split_guard.py" not in ci_text:
        errors.append("ci.local.quick must run contract_governance_form_fields_split_guard.py")

    if not errors:
        governance = _load(GOVERNANCE, "contract_governance_form_fields_split_under_guard")
        data = {
            "head": {"view_type": "form"},
            "views": {
                "form": {
                    "layout": [
                        {"type": "group", "children": [{"type": "field", "name": "name"}]},
                        {"type": "field", "name": "code"},
                    ]
                }
            },
            "fields": {
                "name": {"type": "char", "required": True, "string": "Name"},
                "code": {"type": "char", "string": "Code"},
                "message_ids": {"type": "one2many", "string": "Messages"},
            },
        }
        if governance._iter_field_order(data) != ["name", "code", "message_ids"]:
            errors.append("field order must preserve layout order and append missing fields")
        core = governance._derive_form_core_fields(data)
        if "name" not in core or "message_ids" in core:
            errors.append("core field derivation must include required business fields and skip technical fields")
        governance._apply_form_field_groups(data)
        groups = data.get("field_groups") or []
        if groups[0].get("fields") != core:
            errors.append("field groups must reuse derived core fields")
        required = governance._resolve_contract_required_fields(data, data["fields"])
        if required != ["name"]:
            errors.append("required fields must include only editable required fields")
        policy_data = {
            **data,
            "field_groups": [
                {"name": "core", "fields": ["name"]},
                {"name": "advanced", "fields": ["code"]},
            ],
        }
        policies = governance._build_form_field_policies(policy_data)
        if policies.get("name", {}).get("required_profiles") != ["create", "edit"]:
            errors.append("field policies must mark required create/edit profiles")
        if policies.get("code", {}).get("group") != "advanced":
            errors.append("advanced field group must be reflected in field policy")

        project_data = {
            "head": {"view_type": "form", "model": "project.project"},
            "model": "project.project",
            "governance": {"primary_model": "project.project"},
            "views": {"form": {"model": "project.project", "layout": [{"type": "field", "name": "name"}]}},
            "fields": {
                "name": {"type": "char", "required": True},
                "state": {"type": "selection"},
            },
        }
        governance.register_legacy_project_form_governance_model("project.project")
        governance.register_legacy_project_form_profile(
            "project.project",
            {
                "primary_fields": ["name", "state"],
                "create_hidden_fields": ["state"],
            },
        )
        project_policies = governance._build_form_field_policies(project_data)
        state_policy = project_policies.get("state", {})
        if "create" in state_policy.get("visible_profiles", []):
            errors.append("project create-hidden fields must not be visible in create profile")
        if state_policy.get("source_readonly") is not True:
            errors.append("project create-hidden fields must be readonly in policy")

    if errors:
        print("[contract_governance_form_fields_split_guard] FAIL")
        for error in errors:
            print(f"- {error}")
        return 1
    print("[contract_governance_form_fields_split_guard] PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
