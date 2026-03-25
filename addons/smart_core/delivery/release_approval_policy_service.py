# -*- coding: utf-8 -*-
from __future__ import annotations

from typing import Any

from odoo import SUPERUSER_ID, fields


def _text(value: Any) -> str:
    return str(value or "").strip()


def _list(value: Any) -> list[Any]:
    return value if isinstance(value, list) else []


class ReleaseApprovalPolicyService:
    def __init__(self, env):
        self.env = env

    def now(self):
        return fields.Datetime.now()

    def _release_identity(self, *, product_key: str) -> dict[str, str]:
        product = _text(product_key)
        if "." in product:
            base_product_key, edition_key = product.split(".", 1)
        else:
            base_product_key, edition_key = "construction", "standard"
        return {
            "product_key": product,
            "base_product_key": _text(base_product_key) or "construction",
            "edition_key": _text(edition_key) or "standard",
        }

    def _role_codes_for_user(self, user) -> list[str]:
        if not user:
            return []
        roles: set[str] = set()
        group_xmlids = set(user.groups_id.get_external_id().values())
        prefix = "smart_construction_core.group_sc_role_"
        for xmlid in group_xmlids:
            text = _text(xmlid)
            if text.startswith(prefix):
                roles.add(text[len(prefix):])
        try:
            if user.has_group("smart_construction_core.group_sc_cap_project_read") or user.has_group(
                "smart_construction_core.group_sc_cap_project_manager"
            ):
                roles.add("pm")
            if user.has_group("smart_construction_core.group_sc_super_admin") or user.has_group(
                "smart_construction_core.group_sc_business_full"
            ):
                roles.add("executive")
        except Exception:
            pass
        if (
            int(user.id or 0) == int(SUPERUSER_ID)
            or user.has_group("base.group_system")
            or user.has_group("smart_core.group_smart_core_admin")
        ):
            roles.add("admin")
            roles.add("executive")
        return sorted(roles)

    def resolve_policy(self, *, action_type: str, product_key: str) -> dict[str, Any]:
        identity = self._release_identity(product_key=product_key)
        edition_key = identity["edition_key"]
        action = _text(action_type)
        if action == "promote_snapshot" and edition_key == "preview":
            return {
                "policy_key": "release.promote.preview.direct",
                "approval_required": False,
                "allow_self_approval": True,
                "allowed_executor_role_codes": ["pm", "executive", "admin"],
                "required_approver_role_codes": [],
            }
        if action == "promote_snapshot":
            return {
                "policy_key": "release.promote.standard.approval_required",
                "approval_required": True,
                "allow_self_approval": True,
                "allowed_executor_role_codes": ["pm", "executive", "admin"],
                "required_approver_role_codes": ["executive", "admin"],
            }
        if action == "rollback_snapshot":
            return {
                "policy_key": "release.rollback.controlled",
                "approval_required": True,
                "allow_self_approval": True,
                "allowed_executor_role_codes": ["executive", "admin"],
                "required_approver_role_codes": ["executive", "admin"],
            }
        raise ValueError(f"UNSUPPORTED_RELEASE_ACTION_TYPE:{action}")

    def build_action_policy(self, *, action_type: str, product_key: str, user) -> dict[str, Any]:
        identity = self._release_identity(product_key=product_key)
        policy = self.resolve_policy(action_type=action_type, product_key=product_key)
        actor_roles = self._role_codes_for_user(user)
        approval_required = bool(policy.get("approval_required", False))
        return {
            "policy_key": _text(policy.get("policy_key")),
            "approval_required": approval_required,
            "approval_state": "pending_approval" if approval_required else "not_required",
            "allowed_executor_role_codes_json": list(_list(policy.get("allowed_executor_role_codes"))),
            "required_approver_role_codes_json": list(_list(policy.get("required_approver_role_codes"))),
            "policy_snapshot_json": {
                "policy_key": _text(policy.get("policy_key")),
                "product_key": identity["product_key"],
                "base_product_key": identity["base_product_key"],
                "edition_key": identity["edition_key"],
                "approval_required": approval_required,
                "allow_self_approval": bool(policy.get("allow_self_approval", False)),
                "allowed_executor_role_codes": list(_list(policy.get("allowed_executor_role_codes"))),
                "required_approver_role_codes": list(_list(policy.get("required_approver_role_codes"))),
                "requested_by_user_id": int(user.id) if user else 0,
                "requested_actor_role_codes": actor_roles,
            },
        }

    def _role_match(self, actor_roles: list[str], required_roles: list[str]) -> bool:
        if not required_roles:
            return True
        return bool(set(actor_roles) & set(required_roles))

    def can_execute(self, *, action, user) -> tuple[bool, str, dict[str, Any]]:
        actor_roles = self._role_codes_for_user(user)
        allowed_roles = list(_list(action.allowed_executor_role_codes_json))
        allowed = self._role_match(actor_roles, allowed_roles)
        return allowed, "OK" if allowed else "RELEASE_EXECUTOR_NOT_ALLOWED", {
            "actor_role_codes": actor_roles,
            "allowed_executor_role_codes": allowed_roles,
        }

    def can_approve(self, *, action, user) -> tuple[bool, str, dict[str, Any]]:
        actor_roles = self._role_codes_for_user(user)
        required_roles = list(_list(action.required_approver_role_codes_json))
        allowed = self._role_match(actor_roles, required_roles)
        return allowed, "OK" if allowed else "RELEASE_APPROVER_NOT_ALLOWED", {
            "actor_role_codes": actor_roles,
            "required_approver_role_codes": required_roles,
        }

    def approve_action(self, *, action, user, note: str = "", auto: bool = False) -> dict[str, Any]:
        if not bool(action.approval_required):
            action.write({"approval_state": "not_required", "approved_by_user_id": False, "approved_at": False, "approval_note": ""})
            return action.to_runtime_dict()
        allowed, reason, diagnostics = self.can_approve(action=action, user=user)
        if not allowed:
            raise ValueError(reason)
        action.write(
            {
                "approval_state": "approved",
                "approved_by_user_id": int(user.id) if user else False,
                "approved_at": self.now(),
                "approval_note": _text(note) or ("auto approved by release policy" if auto else "approved by release policy"),
                "diagnostics_json": {
                    **(action.diagnostics_json if isinstance(action.diagnostics_json, dict) else {}),
                    "approval": diagnostics,
                    "approval_mode": "auto" if auto else "manual",
                },
            }
        )
        return action.to_runtime_dict()
