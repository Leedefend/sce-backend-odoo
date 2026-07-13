#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
GOVERNANCE = ROOT / "addons/smart_core/utils/contract_governance.py"
ENTERPRISE_FORMS = ROOT / "addons/smart_core/utils/contract_governance_enterprise_forms.py"
CI = ROOT / "make/ci.mk"

MAX_GOVERNANCE_LINES = 2245


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
    enterprise_text = _read(ENTERPRISE_FORMS)
    ci_text = _read(CI)

    if not governance_text:
        errors.append(f"missing governance file: {GOVERNANCE.relative_to(ROOT)}")
    if not enterprise_text:
        errors.append(f"missing enterprise forms module: {ENTERPRISE_FORMS.relative_to(ROOT)}")

    if governance_text:
        line_count = len(governance_text.splitlines())
        if line_count > MAX_GOVERNANCE_LINES:
            errors.append(f"contract_governance.py line budget exceeded: {line_count} > {MAX_GOVERNANCE_LINES}")
        for token in [
            "def _load_enterprise_forms_module()",
            "contract_governance_enterprise_forms.py",
            "_enterprise_forms.govern_enterprise_company_form(",
            "_enterprise_forms.govern_enterprise_department_form(",
            "_enterprise_forms.govern_enterprise_user_form(",
        ]:
            if token not in governance_text:
                errors.append(f"contract_governance.py missing enterprise forms split token: {token}")

    if enterprise_text:
        for token in [
            "def govern_enterprise_company_form(",
            "def govern_enterprise_department_form(",
            "def govern_enterprise_user_form(",
            "\"enterprise_company_form_sheet\"",
            "\"enterprise_department_form_sheet\"",
            "\"enterprise_user_form_sheet\"",
            "\"sc_role_effective\"",
        ]:
            if token not in enterprise_text:
                errors.append(f"enterprise forms module missing token: {token}")
        for token in (".search(", ".write(", "requests.", "env[", "registry["):
            if token in enterprise_text:
                errors.append(f"enterprise forms module must remain projection-only; found token: {token}")

    if "python3 scripts/verify/contract_governance_enterprise_forms_split_guard.py" not in ci_text:
        errors.append("ci.local.quick must run contract_governance_enterprise_forms_split_guard.py")

    if not errors:
        governance = _load(GOVERNANCE, "contract_governance_enterprise_forms_split_under_guard")
        company_data = {
            "head": {"model": "res.company", "view_type": "form"},
            "model": "res.company",
            "governance": {"primary_model": "res.company"},
            "render_profile": "create",
            "toolbar": {"header": [{"key": "native"}]},
            "buttons": [{"key": "native"}],
            "action_groups": [{"key": "native"}],
            "views": {"form": {"model": "res.company"}},
            "fields": {
                "name": {"type": "char", "string": "公司名称"},
                "sc_short_name": {"type": "char", "string": "公司简称"},
                "message_ids": {"type": "one2many"},
            },
        }
        governance._govern_enterprise_company_form_for_user(company_data)
        if company_data.get("visible_fields") != ["name", "sc_short_name"]:
            errors.append("enterprise company form must select configured visible fields")
        company_layout = (((company_data.get("views") or {}).get("form") or {}).get("layout")) or []
        company_group = ((company_layout[0] or {}).get("children") or [{}])[0] if company_layout else {}
        if company_group.get("string") != "企业基础信息":
            errors.append("enterprise company form must emit core layout group")
        if company_data.get("buttons") != [] or (company_data.get("toolbar") or {}).get("header") != []:
            errors.append("enterprise company create form must clear native actions")
        next_action = (company_data.get("form_governance") or {}).get("next_action") or {}
        if next_action.get("step_key") != "department":
            errors.append("enterprise company form must point next_action to department")

        department_data = {
            "head": {"model": "hr.department", "view_type": "form"},
            "model": "hr.department",
            "governance": {"primary_model": "hr.department"},
            "render_profile": "create",
            "toolbar": {"header": [{"key": "native"}]},
            "views": {"form": {"model": "hr.department"}},
            "fields": {
                "name": {"type": "char", "string": "部门名称"},
                "manager_id": {"type": "many2one", "string": "负责人"},
            },
        }
        governance._govern_enterprise_department_form_for_user(department_data)
        if department_data.get("visible_fields") != ["name"]:
            errors.append("enterprise department form must select configured fields")
        department_next = (department_data.get("form_governance") or {}).get("next_action") or {}
        if department_next.get("step_key") != "user":
            errors.append("enterprise department form must point next_action to user")

        user_data = {
            "head": {"model": "res.users", "view_type": "form"},
            "model": "res.users",
            "governance": {"primary_model": "res.users"},
            "toolbar": {"header": [{"key": "native"}]},
            "buttons": [{"key": "native"}],
            "action_groups": [{"key": "native"}],
            "views": {"form": {"model": "res.users"}},
            "fields": {
                "login": {"type": "char", "required": True},
                "name": {"type": "char", "required": True},
                "email": {"type": "char"},
                "company_id": {"type": "many2one"},
                "sc_role_effective": {"type": "char"},
                "sc_user_role_group_ids": {"type": "many2many"},
            },
        }
        governance._govern_enterprise_user_form_for_user(user_data)
        if user_data.get("visible_fields") != [
            "name",
            "login",
            "email",
            "company_id",
            "sc_role_effective",
            "sc_user_role_group_ids",
        ]:
            errors.append("enterprise user form must keep enterprise field order")
        groups = user_data.get("field_groups") or []
        if [group.get("name") for group in groups] != ["account", "contact", "assignment", "permissions"]:
            errors.append("enterprise user form must emit expected field groups")
        user_form = ((user_data.get("views") or {}).get("form")) or {}
        if user_form.get("statusbar") != {"field": None, "states": []}:
            errors.append("enterprise user form must clear statusbar")
        policies = user_data.get("field_policies") or {}
        if policies.get("login", {}).get("required_profiles") != ["create", "edit"]:
            errors.append("enterprise user required fields must require create/edit profiles")
        if policies.get("sc_role_effective", {}).get("readonly_profiles") != ["create", "edit", "readonly"]:
            errors.append("enterprise user readonly role fields must be readonly in all profiles")
        if user_data.get("buttons") != [] or user_data.get("action_groups") != []:
            errors.append("enterprise user form must clear native actions")

    if errors:
        print("[contract_governance_enterprise_forms_split_guard] FAIL")
        for error in errors:
            print(f"- {error}")
        return 1
    print("[contract_governance_enterprise_forms_split_guard] PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
