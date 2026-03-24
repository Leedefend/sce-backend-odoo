# -*- coding: utf-8 -*-
from __future__ import annotations

from .capability_service import CapabilityService
from .menu_service import MenuService
from .product_policy_service import ProductPolicyService
from .scene_service import SceneService


class DeliveryEngine:
    def __init__(self, env):
        self.env = env
        self.menu_service = MenuService()
        self.scene_service = SceneService(env)
        self.capability_service = CapabilityService()
        self.product_policy_service = ProductPolicyService(env)

    def build(
        self,
        *,
        data: dict,
        product_key: str | None = None,
        edition_key: str | None = None,
        base_product_key: str | None = None,
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
        nav = self.menu_service.build_nav(policy=policy, role_surface=role_surface)
        scenes = self.scene_service.build_entries(policy=policy, scenes=runtime.get("scenes") or [])
        capabilities = self.capability_service.build_entries(policy=policy, capabilities=runtime.get("capabilities") or [])
        return {
            "contract_version": "v1",
            "source": "delivery_engine_v1",
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
                "group_count": len((nav[0].get("children") if nav else []) or []),
                "edition_diagnostics": policy.get("edition_diagnostics") if isinstance(policy.get("edition_diagnostics"), dict) else {},
            },
        }
