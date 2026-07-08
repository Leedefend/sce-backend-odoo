# -*- coding: utf-8 -*-
from __future__ import annotations

from odoo.addons.smart_core.delivery.menu_delivery_convergence_service import MenuDeliveryConvergenceService
from odoo.addons.smart_core.delivery.menu_fact_service import MenuFactService
from odoo.addons.smart_core.delivery.menu_target_interpreter_service import MenuTargetInterpreterService
from odoo.addons.smart_core.security.platform_admin import user_is_platform_admin
from odoo.addons.smart_core.utils.backend_contract_boundaries import MENU_CONFIG_NAV_ENABLED_PARAM, MENU_CONFIG_POLICY_MODEL
from odoo.addons.smart_core.utils.extension_hooks import call_extension_hook_first


SOURCE_KIND = "platform_menu_delivery_projection"
SOURCE_AUTHORITIES = (
    "ir.ui.menu",
    "ir.actions.act_window",
    "res.groups",
    MENU_CONFIG_POLICY_MODEL,
    "extension_business_config_role_resolver",
)
NO_BUSINESS_FACT_AUTHORITY = True


def source_authority_contract() -> dict:
    return {
        "kind": SOURCE_KIND,
        "authorities": list(SOURCE_AUTHORITIES),
        "projection_only": True,
        "no_business_fact_authority": NO_BUSINESS_FACT_AUTHORITY,
    }


def _fact_node(node: dict) -> dict:
    children = node.get("children") if isinstance(node.get("children"), list) else []
    menu_id = node.get("menu_id")
    return {
        "menu_id": menu_id,
        "key": f"menu:{menu_id}" if isinstance(menu_id, int) else "menu:unknown",
        "name": str(node.get("name") or ""),
        "parent_id": node.get("parent_id"),
        "complete_name": str(node.get("complete_name") or ""),
        "sequence": node.get("sequence"),
        "groups": node.get("groups") if isinstance(node.get("groups"), list) else [],
        "web_icon": str(node.get("web_icon") or ""),
        "has_children": bool(children),
        "action_raw": str(node.get("action_raw") or ""),
        "action_type": str(node.get("action_type") or ""),
        "action_id": node.get("action_id"),
        "action_exists": bool(node.get("action_exists")),
        "action_meta": node.get("action_meta") if isinstance(node.get("action_meta"), dict) else {},
        "children": [_fact_node(child) for child in children],
    }


def _flat_fact_node(node: dict) -> dict:
    menu_id = node.get("menu_id")
    child_ids = node.get("child_ids") if isinstance(node.get("child_ids"), list) else []
    return {
        "menu_id": menu_id,
        "key": f"menu:{menu_id}" if isinstance(menu_id, int) else "menu:unknown",
        "name": str(node.get("name") or ""),
        "parent_id": node.get("parent_id"),
        "complete_name": str(node.get("complete_name") or ""),
        "sequence": node.get("sequence"),
        "groups": node.get("groups") if isinstance(node.get("groups"), list) else [],
        "web_icon": str(node.get("web_icon") or ""),
        "has_children": bool(child_ids),
        "action_raw": str(node.get("action_raw") or ""),
        "action_type": str(node.get("action_type") or ""),
        "action_id": node.get("action_id"),
        "action_exists": bool(node.get("action_exists")),
        "action_meta": node.get("action_meta") if isinstance(node.get("action_meta"), dict) else {},
        "child_ids": child_ids,
    }


class FinalMenuNavigationService:
    def __init__(self, env):
        self.env = env

    def build(self, *, scene_map: dict | None = None, policy: dict | None = None) -> dict:
        facts = MenuFactService(self.env).export_visible_menu_facts()
        if not getattr(facts, "flat", None):
            return {
                "nav_fact": {"flat": [], "tree": []},
                "nav_explained": {"flat": [], "tree": []},
                "meta": {
                    "source_authority": source_authority_contract(),
                    "menu_fact_source_authority": getattr(facts, "source_authority", {}),
                    "delivery_convergence": {},
                    "user_menu_config": {},
                    "empty": True,
                },
            }

        nav_fact = {
            "flat": [_flat_fact_node(node) for node in facts.flat],
            "tree": [_fact_node(node) for node in facts.tree],
        }
        nav_explained = MenuTargetInterpreterService(self.env).interpret(
            nav_fact,
            scene_map=scene_map if isinstance(scene_map, dict) else {},
            policy=policy if isinstance(policy, dict) else {},
        )
        nav_fact_filtered, nav_explained_filtered, convergence = MenuDeliveryConvergenceService(self.env).apply(
            nav_fact,
            nav_explained,
            is_admin=self._is_platform_admin_user(),
            is_business_config_admin=self._is_business_config_user(),
        )
        nav_fact_filtered, user_menu_config = self._apply_user_menu_config(nav_fact_filtered)
        nav_explained_filtered, explained_user_menu_config = self._apply_user_menu_config(nav_explained_filtered)
        return {
            "nav_fact": nav_fact_filtered,
            "nav_explained": nav_explained_filtered,
            "meta": {
                "source_authority": source_authority_contract(),
                "menu_fact_source_authority": getattr(facts, "source_authority", {}),
                "delivery_convergence": convergence,
                "user_menu_config": {
                    "nav_fact": user_menu_config,
                    "nav_explained": explained_user_menu_config,
                },
            },
        }

    def _apply_user_menu_config(self, nav_fact: dict) -> tuple[dict, dict]:
        if not isinstance(nav_fact, dict):
            return {"tree": [], "flat": []}, {"applied": False, "reason": "invalid_nav_fact"}
        try:
            raw = self.env["ir.config_parameter"].sudo().get_param(MENU_CONFIG_NAV_ENABLED_PARAM, "")
        except Exception:
            raw = ""
        normalized = str(raw or "").strip().lower()
        if normalized in {"0", "false", "no", "off"}:
            return nav_fact, {
                "applied": False,
                "reason": "disabled",
                MENU_CONFIG_NAV_ENABLED_PARAM: normalized,
                "applied_count": 0,
                "hidden_count": 0,
                "renamed_count": 0,
                "reordered_count": 0,
                "moved_count": 0,
            }
        try:
            policy_model = self.env[MENU_CONFIG_POLICY_MODEL]
        except Exception:
            return nav_fact, {
                "applied": False,
                "reason": "policy_model_unavailable",
                "applied_count": 0,
                "hidden_count": 0,
                "renamed_count": 0,
                "reordered_count": 0,
                "moved_count": 0,
            }
        overlaid, stats = policy_model.apply_runtime_overlay(nav_fact, user=self.env.user)
        if not isinstance(stats, dict):
            stats = {}
        stats.setdefault("applied", True)
        return overlaid, stats

    def _is_platform_admin_user(self) -> bool:
        try:
            return bool(user_is_platform_admin(self.env.user))
        except Exception:
            return False

    def _configured_business_config_admin_group_xmlids(self) -> list[str]:
        hook_groups = call_extension_hook_first(
            self.env,
            "smart_core_business_config_admin_group_xmlids",
            self.env,
        )
        if isinstance(hook_groups, (list, tuple, set)):
            groups = [str(item or "").strip() for item in hook_groups if str(item or "").strip()]
            if groups:
                return groups
        try:
            raw = self.env["ir.config_parameter"].sudo().get_param("smart_core.business_config_admin_group_xmlids", "")
        except Exception:
            raw = ""
        groups = [item.strip() for item in str(raw or "").split(",") if item.strip()]
        return groups or ["smart_core.group_smart_core_business_config_admin"]

    def _is_business_config_user(self) -> bool:
        for group_xmlid in self._configured_business_config_admin_group_xmlids():
            try:
                if self.env.user.has_group(group_xmlid):
                    return True
            except Exception:
                continue
        return False
