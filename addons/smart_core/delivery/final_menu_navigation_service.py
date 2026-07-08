# -*- coding: utf-8 -*-
from __future__ import annotations

try:
    from odoo import SUPERUSER_ID, api
except Exception:  # pragma: no cover - lightweight unit-test stubs
    SUPERUSER_ID = 1
    api = None

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


def _to_int(value) -> int:
    try:
        parsed = int(value or 0)
    except Exception:
        return 0
    return parsed if parsed > 0 else 0


def _text(value) -> str:
    return str(value or "").strip()


def _delivery_node_menu_id(node: dict) -> int:
    meta = node.get("meta") if isinstance(node.get("meta"), dict) else {}
    for candidate in (node.get("menu_id"), meta.get("menu_id"), node.get("id")):
        menu_id = _to_int(candidate)
        if menu_id:
            return menu_id
    return 0


def _delivery_node_config_menu_id(node: dict) -> int:
    meta = node.get("meta") if isinstance(node.get("meta"), dict) else {}
    config_ref = node.get("config_ref") if isinstance(node.get("config_ref"), dict) else meta.get("config_ref")
    config_ref = config_ref if isinstance(config_ref, dict) else {}
    for candidate in (
        node.get("config_menu_id"),
        meta.get("config_menu_id"),
        config_ref.get("id") if _text(config_ref.get("model") or "ir.ui.menu") == "ir.ui.menu" else 0,
    ):
        menu_id = _to_int(candidate)
        if menu_id:
            return menu_id
    return _delivery_node_menu_id(node)


def _delivery_node_label(node: dict) -> str:
    return _text(node.get("name") or node.get("label") or node.get("title"))


def _delivery_node_to_fact(node: dict) -> dict:
    meta = node.get("meta") if isinstance(node.get("meta"), dict) else {}
    config_ref = node.get("config_ref") if isinstance(node.get("config_ref"), dict) else meta.get("config_ref")
    config_ref = config_ref if isinstance(config_ref, dict) else {}
    children = [_delivery_node_to_fact(child) for child in node.get("children") or [] if isinstance(child, dict)]
    runtime_menu_id = _delivery_node_menu_id(node)
    menu_id = _delivery_node_config_menu_id(node)
    label = _delivery_node_label(node)
    configurable = bool(menu_id and _text((config_ref or {}).get("model") or "ir.ui.menu") == "ir.ui.menu")
    action_id = _to_int(node.get("action_id") or meta.get("action_id"))
    model = _text(node.get("model") or meta.get("model"))
    action_raw = _text(node.get("action") or meta.get("action") or (f"ir.actions.act_window,{action_id}" if action_id else ""))
    out = {
        "menu_id": menu_id,
        "runtime_menu_id": runtime_menu_id,
        "config_menu_id": menu_id,
        "config_ref": config_ref or ({"model": "ir.ui.menu", "id": menu_id} if menu_id else {}),
        "configurable": configurable,
        "synthetic": bool(runtime_menu_id and menu_id and runtime_menu_id != menu_id),
        "node_kind": "group" if children else "leaf",
        "key": f"menu:{menu_id}" if menu_id else "menu:unknown",
        "name": label,
        "label": label,
        "title": label,
        "parent_id": _to_int(node.get("parent_id") or meta.get("parent_id")),
        "complete_name": _text(node.get("complete_name") or label),
        "sequence": _to_int(node.get("sequence") or meta.get("sequence")),
        "groups": node.get("groups") if isinstance(node.get("groups"), list) else [],
        "web_icon": _text(node.get("web_icon") or meta.get("web_icon")),
        "has_children": bool(children),
        "action_raw": action_raw,
        "action_type": "ir.actions.act_window" if action_id else "",
        "action_id": action_id or None,
        "action_exists": bool(action_id),
        "action_meta": {
            "model": model,
            "route": _text(node.get("route") or meta.get("route")),
            "entry_target": meta.get("entry_target") if isinstance(meta.get("entry_target"), dict) else {},
        },
        "children": children,
    }
    return out


def _flatten_fact_tree(nodes: list[dict]) -> list[dict]:
    flat: list[dict] = []

    def walk(items: list[dict]):
        for item in items or []:
            if not isinstance(item, dict):
                continue
            flat.append({
                key: value
                for key, value in item.items()
                if key != "children"
            } | {"child_ids": [_to_int(child.get("menu_id")) for child in item.get("children") or [] if _to_int(child.get("menu_id"))]})
            walk(item.get("children") or [])

    walk(nodes)
    return flat


class FinalMenuNavigationService:
    def __init__(self, env):
        self.env = env

    def build(self, *, scene_map: dict | None = None, policy: dict | None = None) -> dict:
        delivery_navigation = self._build_delivery_navigation_contract()
        if delivery_navigation:
            return delivery_navigation
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

    def _business_root_xmlid(self) -> str:
        root_xmlid = _text(call_extension_hook_first(self.env, "smart_core_business_root_menu_xmlid", self.env))
        if root_xmlid:
            return root_xmlid
        try:
            return _text(self.env["ir.config_parameter"].sudo().get_param("smart_core.business_root_menu_xmlid", ""))
        except Exception:
            return ""

    def _business_root_menu_id(self) -> int:
        root_xmlid = self._business_root_xmlid()
        if not root_xmlid:
            return 0
        try:
            root = self.env.ref(root_xmlid, raise_if_not_found=False)
        except Exception:
            root = None
        return _to_int(getattr(root, "id", 0)) if root and _text(getattr(root, "_name", "")) == "ir.ui.menu" else 0

    def _runtime_role_surface(self) -> dict:
        is_platform_admin = self._is_platform_admin_user()
        is_business_config_admin = self._is_business_config_user()
        return {
            "role_code": "business_config_admin" if is_business_config_admin else "",
            "is_platform_admin": is_platform_admin,
            "is_business_config_admin": is_business_config_admin,
        }

    def _current_delivery_identity(self) -> dict:
        identity = call_extension_hook_first(self.env, "smart_core_resolve_startup_delivery_identity", self.env, {})
        return identity if isinstance(identity, dict) else {}

    def _build_delivery_navigation_contract(self) -> dict:
        try:
            if api is None:
                raise RuntimeError("odoo_api_unavailable")
            from odoo.addons.smart_core.adapters.nav_tree_cleaner import NavTreeCleaner
            from odoo.addons.smart_core.adapters.odoo_nav_adapter import OdooNavAdapter
            from odoo.addons.smart_core.app_config_engine.services.dispatchers.nav_dispatcher import NavDispatcher
            from odoo.addons.smart_core.core.system_init_nav_request_builder import SystemInitNavRequestBuilder
            from odoo.addons.smart_core.delivery.delivery_engine import DeliveryEngine

            params = {}
            root_menu_id = self._business_root_menu_id()
            if root_menu_id:
                params["root_menu_id"] = root_menu_id
            su_env = api.Environment(self.env.cr, SUPERUSER_ID, dict(self.env.context or {}))
            nav_request = SystemInitNavRequestBuilder.build(params, "web")
            nav_data, nav_versions = NavDispatcher(self.env, su_env).build_nav(nav_request)
            native_nav = NavTreeCleaner().clean(nav_data.get("nav") if isinstance(nav_data, dict) else [])
            OdooNavAdapter().enrich(self.env, native_nav)
            identity = self._current_delivery_identity()
            delivery_payload = DeliveryEngine(self.env).build(
                data={"role_surface": self._runtime_role_surface()},
                product_key=_text(identity.get("product_key")) if isinstance(identity, dict) else "",
                edition_key=_text(identity.get("edition_key")) if isinstance(identity, dict) else "",
                base_product_key=_text(identity.get("base_product_key")) if isinstance(identity, dict) else "",
                native_nav=native_nav,
            )
            delivery_nav = delivery_payload.get("nav") if isinstance(delivery_payload, dict) else []
            if not isinstance(delivery_nav, list) or not delivery_nav:
                return {}
            tree = [_delivery_node_to_fact(node) for node in delivery_nav if isinstance(node, dict)]
            flat = _flatten_fact_tree(tree)
            if not flat:
                return {}
            nav_fact = {"flat": flat, "tree": tree}
            return {
                "nav_fact": nav_fact,
                "nav_explained": nav_fact,
                "meta": {
                    "source_authority": source_authority_contract(),
                    "menu_fact_source_authority": {},
                    "delivery_convergence": {"source": "delivery_engine_v1"},
                    "delivery_engine": {
                        "source": "delivery_engine_v1",
                        "nav_versions": nav_versions if isinstance(nav_versions, dict) else {},
                    },
                    "user_menu_config": delivery_payload.get("meta", {}).get("user_menu_config", {}) if isinstance(delivery_payload.get("meta"), dict) else {},
                },
            }
        except Exception:
            return {}

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
