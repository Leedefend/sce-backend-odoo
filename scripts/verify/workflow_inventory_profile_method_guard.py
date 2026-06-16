#!/usr/bin/env python3
"""Guard workflow inventory method coverage against backend profiles."""

from __future__ import annotations

import ast
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
WORKFLOW_SERVICE = ROOT / "addons/smart_construction_core/models/support/workflow_contract_service.py"
WORKFLOW_INVENTORY = ROOT / "scripts/audit/workflow_state_inventory.py"


def _profile_from_helper_call(node: ast.AST):
    if not isinstance(node, ast.Call) or not isinstance(node.func, ast.Name):
        raise ValueError("unsupported PROFILE_BY_MODEL expression: %r" % node)
    if not node.args:
        raise ValueError("profile helper requires model names: %s" % node.func.id)
    model_names = ast.literal_eval(node.args[0])
    if node.func.id == "_simple_approval_profiles":
        method_by_action = {
            "submit": "action_submit",
            "approve": "action_approve",
            "reopen": "action_reset_draft",
            "cancel": "action_cancel",
        }
    elif node.func.id == "_simple_close_issue_profiles":
        method_by_action = {
            "submit": "action_submit",
            "complete": "action_close",
            "cancel": "action_cancel",
        }
    elif node.func.id == "_submit_confirm_profiles":
        method_by_action = {
            "submit": "action_submit",
            "complete": "action_confirm",
            "reopen": "action_reset_draft",
            "cancel": "action_cancel",
        }
    elif node.func.id == "_in_progress_done_profiles":
        method_by_action = {
            "submit": "action_submit",
            "complete": "action_done",
            "reopen": "action_reset_draft",
            "cancel": "action_cancel",
        }
    elif node.func.id == "_confirm_done_profiles":
        method_by_action = {
            "submit": "action_confirm",
            "complete": "action_done",
            "reopen": "action_reset_draft",
            "cancel": "action_cancel",
        }
    else:
        raise ValueError("unsupported profile helper: %s" % node.func.id)
    return {name: {"method_by_action": method_by_action} for name in model_names}


def _profile_dict(node: ast.AST):
    if not isinstance(node, ast.Dict):
        return ast.literal_eval(node)
    out = {}
    for key, value in zip(node.keys, node.values):
        if key is None:
            out.update(_profile_from_helper_call(value))
            continue
        out[ast.literal_eval(key)] = ast.literal_eval(value)
    return out


def _literal_class_attr(path: Path, class_name: str, attr_name: str):
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    for node in tree.body:
        if not isinstance(node, ast.ClassDef) or node.name != class_name:
            continue
        for child in node.body:
            if isinstance(child, ast.Assign):
                for target in child.targets:
                    if isinstance(target, ast.Name) and target.id == attr_name:
                        return _profile_dict(child.value)
    raise ValueError(f"missing {class_name}.{attr_name} in {path}")


def _literal_module_attr(path: Path, attr_name: str):
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    for node in tree.body:
        if not isinstance(node, ast.Assign):
            continue
        for target in node.targets:
            if isinstance(target, ast.Name) and target.id == attr_name:
                return ast.literal_eval(node.value)
    raise ValueError(f"missing {attr_name} in {path}")


def main() -> int:
    profiles = _literal_class_attr(WORKFLOW_SERVICE, "ScWorkflowContractService", "PROFILE_BY_MODEL")
    inventory_methods = set(_literal_module_attr(WORKFLOW_INVENTORY, "WORKFLOW_METHOD_NAMES"))
    profile_methods = {
        method
        for profile in profiles.values()
        for method in (profile.get("method_by_action") or {}).values()
        if method
    }
    missing = sorted(profile_methods - inventory_methods)
    if missing:
        print(
            "[workflow_inventory_profile_method_guard] FAIL missing inventory methods: %s"
            % ", ".join(missing),
            file=sys.stderr,
        )
        return 1
    print(
        "[workflow_inventory_profile_method_guard] PASS profile_methods=%s inventory_methods=%s"
        % (len(profile_methods), len(inventory_methods))
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
