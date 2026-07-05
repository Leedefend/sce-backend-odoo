# -*- coding: utf-8 -*-
from __future__ import annotations

from odoo.addons.smart_core.core.source_authority import build_source_authority_contract

from .capability_service import CapabilityService
from .menu_service import MenuService
from .product_policy_service import ProductPolicyService
from .scene_service import SceneService


def _text(value) -> str:
    return str(value or "").strip()


def _to_int(value) -> int:
    try:
        parsed = int(value)
    except Exception:
        return 0
    return parsed if parsed > 0 else 0


class DeliveryEngine:
    SOURCE_KIND = "delivery_engine_projection"
    SOURCE_AUTHORITIES = ("delivery_product_policy_projection", "delivery_menu_projection", "delivery_scene_projection")
    NO_BUSINESS_FACT_AUTHORITY = True

    def __init__(self, env):
        self.env = env
        self.menu_service = MenuService(env)
        self.scene_service = SceneService(env)
        self.capability_service = CapabilityService()
        self.product_policy_service = ProductPolicyService(env)

    def _has_group(self, xmlid: str) -> bool:
        try:
            return bool(self.env.user.has_group(xmlid))
        except Exception:
            return False

    def _runtime_role_surface(self, runtime: dict) -> dict:
        role_surface = runtime.get("role_surface") if isinstance(runtime.get("role_surface"), dict) else {}
        resolved = dict(role_surface)
        if "is_platform_admin" not in resolved:
            resolved["is_platform_admin"] = self._has_group("smart_core.group_smart_core_admin")
        if "is_business_config_admin" not in resolved:
            resolved["is_business_config_admin"] = self._has_group("smart_core.group_smart_core_business_config_admin")
        return resolved

    @classmethod
    def source_authority_contract(cls) -> dict:
        return build_source_authority_contract(
            kind=cls.SOURCE_KIND,
            authorities=cls.SOURCE_AUTHORITIES,
            no_business_fact_authority=cls.NO_BUSINESS_FACT_AUTHORITY,
            runtime_carrier="delivery_engine_v1",
        )

    def _resolve_xmlid_record(self, xmlid: str, expected_model: str = "", expected_prefix: str = ""):
        value = _text(xmlid)
        if not value or "." not in value:
            return None
        try:
            rec = self.env.ref(value, raise_if_not_found=False)
        except Exception:
            return None
        if not rec:
            return None
        model_name = _text(getattr(rec, "_name", ""))
        if expected_model and model_name != expected_model:
            return None
        if expected_prefix and not model_name.startswith(expected_prefix):
            return None
        return rec

    def _normalize_entry_target_refs(
        self,
        *,
        entry_target: dict,
        menu_id: int,
        action_id: int,
        model: str,
        view_modes: list[str],
        route: str,
    ) -> dict:
        if not isinstance(entry_target, dict):
            entry_target = {}
        if _text(entry_target.get("type")) == "scene":
            next_target = dict(entry_target)
            refs = dict(next_target.get("compatibility_refs") or {})
            if menu_id:
                refs["menu_id"] = menu_id
            if action_id:
                refs["action_id"] = action_id
            if model:
                refs["model"] = model
            if view_modes:
                refs["view_modes"] = view_modes
            if refs:
                next_target["compatibility_refs"] = refs
            return next_target

        refs = dict(entry_target.get("compatibility_refs") or {})
        if menu_id:
            refs["menu_id"] = menu_id
        if action_id:
            refs["action_id"] = action_id
        if model:
            refs["model"] = model
        if view_modes:
            refs["view_modes"] = view_modes
        return {
            "type": "compatibility",
            "route": route or _text(entry_target.get("route")),
            "compatibility_refs": refs,
        }

    def _normalize_delivery_nav_node_refs(self, node: dict) -> None:
        if not isinstance(node, dict):
            return
        children = node.get("children") if isinstance(node.get("children"), list) else []
        for child in children:
            self._normalize_delivery_nav_node_refs(child)
        if children:
            return

        meta = node.get("meta") if isinstance(node.get("meta"), dict) else {}
        if not meta:
            return

        menu_xmlid = _text(meta.get("menu_xmlid") or node.get("menu_xmlid"))
        action_xmlid = _text(meta.get("action_xmlid") or node.get("action_xmlid"))
        menu = self._resolve_xmlid_record(menu_xmlid, expected_model="ir.ui.menu") if menu_xmlid else None
        if menu and not bool(getattr(menu, "active", False)):
            menu = None
        action = self._resolve_xmlid_record(action_xmlid, expected_prefix="ir.actions.") if action_xmlid else None
        if menu and not action:
            try:
                action = menu.action
            except Exception:
                action = None

        menu_id = _to_int(getattr(menu, "id", 0)) or _to_int(meta.get("menu_id"))
        action_id = _to_int(getattr(action, "id", 0)) or _to_int(meta.get("action_id"))
        model = _text(getattr(action, "res_model", "")) if action and _text(getattr(action, "_name", "")) == "ir.actions.act_window" else _text(meta.get("model"))
        view_mode_raw = _text(getattr(action, "view_mode", "")) if action and _text(getattr(action, "_name", "")) == "ir.actions.act_window" else ""
        view_modes = [_text(item) for item in view_mode_raw.split(",") if _text(item)]
        if not view_modes and isinstance(meta.get("view_modes"), list):
            view_modes = [_text(item) for item in meta.get("view_modes") if _text(item)]

        if not (menu or action):
            return

        if menu_id:
            node["menu_id"] = menu_id
            meta["menu_id"] = menu_id
        if action_id:
            meta["action_id"] = action_id
        if model:
            meta["model"] = model
        if view_modes:
            meta["view_modes"] = view_modes

        current_route = _text(meta.get("route") or node.get("route"))
        if action_id and not current_route.startswith("/s/"):
            route = f"/a/{action_id}"
            if menu_id:
                route = f"{route}?menu_id={menu_id}"
            meta["route"] = route
        else:
            route = current_route

        meta["entry_target"] = self._normalize_entry_target_refs(
            entry_target=meta.get("entry_target") if isinstance(meta.get("entry_target"), dict) else {},
            menu_id=menu_id,
            action_id=action_id,
            model=model,
            view_modes=view_modes,
            route=route,
        )
        node["meta"] = meta

    def _normalize_delivery_nav_refs(self, nav: list[dict]) -> list[dict]:
        for node in nav or []:
            self._normalize_delivery_nav_node_refs(node)
        return nav

    def build(
        self,
        *,
        data: dict,
        product_key: str | None = None,
        edition_key: str | None = None,
        base_product_key: str | None = None,
        native_nav: list[dict] | None = None,
    ) -> dict:
        runtime = data if isinstance(data, dict) else {}
        role_surface = self._runtime_role_surface(runtime)
        policy = self.product_policy_service.get_policy(
            product_key=product_key,
            edition_key=edition_key,
            base_product_key=base_product_key,
            role_code=str(role_surface.get("role_code") or "").strip(),
            enforce_release=True,
            enforce_access=True,
        )
        nav = self.menu_service.build_nav(
            policy=policy,
            role_surface=role_surface,
            native_nav=native_nav if isinstance(native_nav, list) else [],
        )
        nav = self._normalize_delivery_nav_refs(nav)
        scenes = self.scene_service.build_entries(policy=policy, scenes=runtime.get("scenes") or [])
        capabilities = self.capability_service.build_entries(policy=policy, capabilities=runtime.get("capabilities") or [])
        nav_meta = self.menu_service.describe_nav(nav)
        policy_source_authority = policy.get("policy_source_authority") if isinstance(policy.get("policy_source_authority"), dict) else {}
        policy_source_kind = str(policy_source_authority.get("kind") or "").strip()
        policy_empty = not (policy.get("menu_groups") or policy.get("scenes") or policy.get("capabilities"))
        policy_empty_reason = "MINIMAL_DEFAULT_PRODUCT_POLICY" if policy_source_kind == "minimal_default_product_policy_provider" else ""
        return {
            "contract_version": "v1",
            "source": "delivery_engine_v1",
            "source_authority": self.source_authority_contract(),
            "product_key": str(policy.get("product_key") or "").strip(),
            "base_product_key": str(policy.get("base_product_key") or "").strip(),
            "edition_key": str(policy.get("edition_key") or "").strip(),
            "role_code": str(role_surface.get("role_code") or "").strip(),
            "nav": nav,
            "scenes": scenes,
            "capabilities": capabilities,
            "product_policy": {
                "product_key": str(policy.get("product_key") or "").strip(),
                "base_product_key": str(policy.get("base_product_key") or "").strip(),
                "edition_key": str(policy.get("edition_key") or "").strip(),
                "label": str(policy.get("label") or "").strip(),
                "version": str(policy.get("version") or "").strip(),
                "policy_source_authority": policy_source_authority,
                "policy_source_kind": policy_source_kind,
                "policy_empty": bool(policy_empty),
                "policy_empty_reason": policy_empty_reason,
                "menu_keys": [
                    str(menu.get("menu_key") or "").strip()
                    for group in policy.get("menu_groups") or []
                    if isinstance(group, dict)
                    for menu in group.get("menus") or []
                    if isinstance(menu, dict) and str(menu.get("menu_key") or "").strip()
                ],
                "scene_keys": [
                    str(row.get("scene_key") or "").strip()
                    for row in policy.get("scenes") or []
                    if isinstance(row, dict) and str(row.get("scene_key") or "").strip()
                ],
                "scene_version_bindings": policy.get("scene_version_bindings") if isinstance(policy.get("scene_version_bindings"), dict) else {},
                "scene_binding_diagnostics": policy.get("scene_binding_diagnostics") if isinstance(policy.get("scene_binding_diagnostics"), dict) else {},
                "edition_diagnostics": policy.get("edition_diagnostics") if isinstance(policy.get("edition_diagnostics"), dict) else {},
                "capability_keys": [
                    str(row.get("capability_key") or row.get("key") or "").strip()
                    for row in policy.get("capabilities") or []
                    if isinstance(row, dict) and str(row.get("capability_key") or row.get("key") or "").strip()
                ],
            },
            "meta": {
                "nav_root_count": len(nav),
                "scene_count": len(scenes),
                "capability_count": len(capabilities),
                "nav_source_authority": nav_meta.get("source_authority") if isinstance(nav_meta.get("source_authority"), dict) else {},
                "capability_source_authority": self.capability_service.source_authority_contract(),
                "group_count": int(nav_meta.get("group_count") or 0),
                "stable_group_count": int(nav_meta.get("stable_group_count") or 0),
                "native_preview_group_count": int(nav_meta.get("native_preview_group_count") or 0),
                "stable_leaf_count": int(nav_meta.get("stable_leaf_count") or 0),
                "native_preview_leaf_count": int(nav_meta.get("native_preview_leaf_count") or 0),
                "native_preview_group_key": str(nav_meta.get("native_preview_group_key") or ""),
                "nav_group_keys": nav_meta.get("group_keys") if isinstance(nav_meta.get("group_keys"), list) else [],
                "edition_diagnostics": policy.get("edition_diagnostics") if isinstance(policy.get("edition_diagnostics"), dict) else {},
                "policy_source_kind": policy_source_kind,
                "policy_empty": bool(policy_empty),
                "policy_empty_reason": policy_empty_reason,
            },
        }
