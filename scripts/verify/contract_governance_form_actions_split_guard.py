#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
GOVERNANCE = ROOT / "addons/smart_core/utils/contract_governance.py"
FORM_ACTIONS = ROOT / "addons/smart_core/utils/contract_governance_form_actions.py"
CI = ROOT / "make/ci.mk"

MAX_GOVERNANCE_LINES = 3212


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
    form_actions_text = _read(FORM_ACTIONS)
    ci_text = _read(CI)

    if not governance_text:
        errors.append(f"missing governance file: {GOVERNANCE.relative_to(ROOT)}")
    if not form_actions_text:
        errors.append(f"missing form actions module: {FORM_ACTIONS.relative_to(ROOT)}")

    if governance_text:
        line_count = len(governance_text.splitlines())
        if line_count > MAX_GOVERNANCE_LINES:
            errors.append(f"contract_governance.py line budget exceeded: {line_count} > {MAX_GOVERNANCE_LINES}")
        for token in [
            "def _load_form_actions_module()",
            "contract_governance_form_actions.py",
            "return _form_actions.infer_action_semantic(action)",
            "_form_actions.annotate_form_actions(data, is_form_contract=_is_form_contract)",
            "return _form_actions.build_form_action_policies(",
        ]:
            if token not in governance_text:
                errors.append(f"contract_governance.py missing form actions split token: {token}")

    if form_actions_text:
        for token in [
            "def infer_action_semantic(",
            "def infer_visible_profiles(",
            "def annotate_form_actions(",
            "def default_action_policy(",
            "def resolve_action_policy_template_keys(",
            "def apply_action_policy_templates(",
            "def merge_policy_constraints(",
            "def append_primary_action_conditions(",
            "def build_form_action_policies(",
            "scene.project.form.primary",
        ]:
            if token not in form_actions_text:
                errors.append(f"form actions module missing token: {token}")
        for token in (".search(", ".write(", "requests.", "env[", "registry["):
            if token in form_actions_text:
                errors.append(f"form actions module must remain projection-only; found token: {token}")

    if "python3 scripts/verify/contract_governance_form_actions_split_guard.py" not in ci_text:
        errors.append("ci.local.quick must run contract_governance_form_actions_split_guard.py")

    if not errors:
        governance = _load(GOVERNANCE, "contract_governance_form_actions_split_under_guard")
        data = {
            "head": {"view_type": "form"},
            "fields": {
                "name": {"type": "char", "required": True},
                "stage_id": {"type": "many2one"},
                "phase_key": {"type": "selection"},
                "lifecycle_state": {
                    "type": "selection",
                    "selection": [["open", "Open"], ["done", "Done"], ["archive", "Archived"]],
                },
            },
            "buttons": [
                {"key": "save", "label": "提交", "required_capabilities": ["project.write"]},
                {"key": "archive", "label": "Archive", "groups_xmlids": ["base.group_user"]},
            ],
            "views": {"form": {}},
        }
        governance._annotate_form_actions(data)
        buttons = data.get("buttons") or []
        if buttons[0].get("semantic") != "primary_action":
            errors.append("submit action must infer primary_action")
        if buttons[1].get("semantic") != "danger":
            errors.append("archive action must infer danger semantic")
        policies = governance._build_form_action_policies(data)
        save_policy = policies.get("save") or {}
        enabled_when = save_policy.get("enabled_when") or {}
        if save_policy.get("disabled_reason") != governance._FORM_PRIMARY_DISABLED_REASON:
            errors.append("primary action must keep primary disabled reason")
        if enabled_when.get("required_fields") != ["name"]:
            errors.append("primary action must carry required field constraints")
        if enabled_when.get("required_capabilities") != ["project.write"]:
            errors.append("primary action must carry required capabilities")
        if enabled_when.get("lifecycle", {}).get("field") != "lifecycle_state":
            errors.append("primary action must carry lifecycle constraints")
        archive_policy = policies.get("archive") or {}
        if archive_policy.get("enabled_when", {}).get("required_groups") != ["base.group_user"]:
            errors.append("group-constrained action must carry required groups")

        project_policy = governance._default_action_policy("primary_action", ["create", "edit"], ["name"])
        governance._apply_action_policy_templates(
            project_policy,
            ["scene.project.form.primary"],
            required_fields=["name"],
            required_capabilities=[],
            lifecycle_field="",
            lifecycle_blocked_states=[],
            required_groups=[],
            required_roles=[],
            fields_map=data["fields"],
        )
        condition_fields = [
            item.get("field")
            for item in project_policy.get("enabled_when", {}).get("conditions", [])
            if isinstance(item, dict)
        ]
        if "phase_key" not in condition_fields or "stage_id" not in condition_fields:
            errors.append("project primary action template must include phase and stage conditions")

    if errors:
        print("[contract_governance_form_actions_split_guard] FAIL")
        for error in errors:
            print(f"- {error}")
        return 1
    print("[contract_governance_form_actions_split_guard] PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
