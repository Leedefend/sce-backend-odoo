# -*- coding: utf-8 -*-
from __future__ import annotations

from typing import Any

from odoo import SUPERUSER_ID, fields
from odoo.addons.smart_core.core.source_authority import build_source_authority_contract
from odoo.addons.smart_core.security.platform_admin import user_is_platform_admin

from .product_identity import resolve_product_identity
from odoo.addons.smart_core.utils.extension_hooks import call_extension_hook_first


def _text(value: Any) -> str:
    return str(value or "").strip()


def _list(value: Any) -> list[Any]:
    return value if isinstance(value, list) else []


class ReleaseApprovalPolicyService:
    SOURCE_KIND = "release_approval_policy_projection"
    SOURCE_AUTHORITIES = ("release_action_policy", "res.groups", "extension_role_resolver")
    NO_BUSINESS_FACT_AUTHORITY = True

    def __init__(self, env):
        self.env = env

    @classmethod
    def source_authority_contract(cls) -> dict[str, Any]:
        return build_source_authority_contract(
            kind=cls.SOURCE_KIND,
            authorities=cls.SOURCE_AUTHORITIES,
            rebuildable=None,
            no_business_fact_authority=cls.NO_BUSINESS_FACT_AUTHORITY,
            runtime_carrier="release_operator_policy",
        )

    def now(self):
        return fields.Datetime.now()

    def _release_identity(self, *, product_key: str) -> dict[str, str]:
        return resolve_product_identity(product_key=product_key)

    def _role_codes_for_user(self, user) -> list[str]:
        return list(self.resolve_actor_role_context(user).get("actor_role_codes") or [])

    def resolve_actor_role_context(self, user) -> dict[str, Any]:
        if not user:
            return {
                "actor_role_codes": [],
                "role_source": "none",
                "source_authority": self.source_authority_contract(),
            }
        hook_roles = call_extension_hook_first(
            self.env,
            "smart_core_resolve_release_actor_role_codes",
            self.env,
            user,
        )
        if isinstance(hook_roles, (list, tuple)):
            normalized_hook_roles = sorted({_text(item) for item in hook_roles if _text(item)})
            if normalized_hook_roles:
                return {
                    "actor_role_codes": normalized_hook_roles,
                    "role_source": "extension_hook",
                    "source_authority": self.source_authority_contract(),
                }
        roles: set[str] = set()
        if int(user.id or 0) == int(SUPERUSER_ID) or user_is_platform_admin(user):
            roles.add("admin")
            roles.add("executive")
        return {
            "actor_role_codes": sorted(roles),
            "role_source": "platform_admin_groups",
            "source_authority": self.source_authority_contract(),
        }

    def resolve_actor_role_codes(self, user) -> list[str]:
        return self._role_codes_for_user(user)

    def roles_match(self, actor_roles: list[str], required_roles: list[str]) -> bool:
        return self._role_match(actor_roles, required_roles)

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
        role_context = self.resolve_actor_role_context(user)
        actor_roles = list(role_context.get("actor_role_codes") or [])
        allowed_roles = list(_list(action.allowed_executor_role_codes_json))
        allowed = self._role_match(actor_roles, allowed_roles)
        return allowed, "OK" if allowed else "RELEASE_EXECUTOR_NOT_ALLOWED", {
            "actor_role_codes": actor_roles,
            "allowed_executor_role_codes": allowed_roles,
            "role_context": role_context,
        }

    def can_approve(self, *, action, user) -> tuple[bool, str, dict[str, Any]]:
        role_context = self.resolve_actor_role_context(user)
        actor_roles = list(role_context.get("actor_role_codes") or [])
        required_roles = list(_list(action.required_approver_role_codes_json))
        allowed = self._role_match(actor_roles, required_roles)
        return allowed, "OK" if allowed else "RELEASE_APPROVER_NOT_ALLOWED", {
            "actor_role_codes": actor_roles,
            "required_approver_role_codes": required_roles,
            "role_context": role_context,
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
