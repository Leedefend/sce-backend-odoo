# -*- coding: utf-8 -*-
from __future__ import annotations

from .capability_service import CapabilityService
from .menu_service import MenuService
from .product_policy_service import ProductPolicyService
from .scene_service import SceneService


class DeliveryEngine:
    SOURCE_KIND = "delivery_engine_projection"
    SOURCE_AUTHORITIES = ("delivery_product_policy_projection", "delivery_menu_projection", "delivery_scene_projection")
    NO_BUSINESS_FACT_AUTHORITY = True

    def __init__(self, env):
        self.env = env
        self.menu_service = MenuService()
        self.scene_service = SceneService(env)
        self.capability_service = CapabilityService()
        self.product_policy_service = ProductPolicyService(env)

    @classmethod
    def source_authority_contract(cls) -> dict:
        return {
            "kind": cls.SOURCE_KIND,
            "authorities": list(cls.SOURCE_AUTHORITIES),
            "projection_only": True,
            "rebuildable": True,
            "no_business_fact_authority": cls.NO_BUSINESS_FACT_AUTHORITY,
            "runtime_carrier": "delivery_engine_v1",
        }

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
        role_surface = runtime.get("role_surface") if isinstance(runtime.get("role_surface"), dict) else {}
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
