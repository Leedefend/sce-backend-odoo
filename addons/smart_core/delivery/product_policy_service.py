# -*- coding: utf-8 -*-
from __future__ import annotations

import copy

try:
    from odoo import SUPERUSER_ID, api
    from odoo.modules.registry import Registry
except Exception:
    SUPERUSER_ID = 1
    api = None
    Registry = None

from odoo.addons.smart_core.core.source_authority import build_source_authority_contract

try:
    from .product_identity import LEGACY_DEFAULT_BASE_PRODUCT_KEY
except Exception:
    LEGACY_DEFAULT_BASE_PRODUCT_KEY = "platform"
try:
    from odoo.addons.smart_core.utils.extension_hooks import call_extension_hook_first
except Exception:
    call_extension_hook_first = None

DEFAULT_POLICY_SOURCE_KIND = "platform_default_product_policy_provider"
DEFAULT_POLICY_NODE_SOURCE_KIND = "platform_default_product_policy_node_projection"


DEFAULT_PRODUCT_POLICY = {
    "product_key": "platform.standard",
    "base_product_key": "platform",
    "edition_key": "standard",
    "state": "stable",
    "access_level": "public",
    "allowed_role_codes": [],
    "label": "Platform Standard",
    "version": "v1",
    "scene_version_bindings": {},
    "menu_groups": [],
    "scenes": [],
    "capabilities": [],
}


def _minimal_default_product_policy(*, base_product_key: str, edition_key: str) -> dict:
    base_key = str(base_product_key or "").strip() or "platform"
    edition = str(edition_key or "").strip() or "standard"
    product_key = f"{base_key}.{edition}"
    base_label = base_key.replace("_", " ").replace("-", " ").title() or "Platform"
    edition_label = edition.replace("_", " ").replace("-", " ").title() or "Standard"
    return {
        "product_key": product_key,
        "base_product_key": base_key,
        "edition_key": edition,
        "state": "stable",
        "access_level": "public",
        "allowed_role_codes": [],
        "label": f"{base_label} {edition_label}",
        "version": "v1",
        "scene_version_bindings": {},
        "menu_groups": [],
        "scenes": [],
        "capabilities": [],
        "policy_source_authority": {
            "kind": "minimal_default_product_policy_provider",
            "authorities": ["requested_product_identity"],
            "projection_only": True,
            "no_business_fact_authority": True,
        },
    }


def default_policy_node_source_authority_contract() -> dict:
    return build_source_authority_contract(
        kind=DEFAULT_POLICY_NODE_SOURCE_KIND,
        authorities=("DEFAULT_PRODUCT_POLICY.menu_groups", "DEFAULT_PRODUCT_POLICY.scenes", "DEFAULT_PRODUCT_POLICY.capabilities"),
        rebuildable=None,
        no_business_fact_authority=True,
        platform_default=True,
    )


def _mark_legacy_default_policy_nodes(payload: dict) -> dict:
    if not isinstance(payload, dict):
        return payload
    source = default_policy_node_source_authority_contract()
    for group in payload.get("menu_groups") or []:
        if not isinstance(group, dict):
            continue
        group.setdefault("policy_node_source_authority", source)
        for menu in group.get("menus") or []:
            if isinstance(menu, dict):
                menu.setdefault("policy_node_source_authority", source)
    for bucket in ("scenes", "capabilities"):
        for row in payload.get(bucket) or []:
            if isinstance(row, dict):
                row.setdefault("policy_node_source_authority", source)
    return payload


class ProductPolicyService:
    SOURCE_KIND = "delivery_product_policy_projection"
    SOURCE_AUTHORITIES = (
        "sc.product.policy",
        "platform_db.sc.product.policy",
        "sc.scene.snapshot",
        "default_product_policy_provider",
    )
    NO_BUSINESS_FACT_AUTHORITY = True
    DEFAULT_POLICY_SOURCE_KIND = DEFAULT_POLICY_SOURCE_KIND
    RELEASEABLE_STATES = {"preview", "stable"}

    def __init__(self, env):
        self.env = env

    @classmethod
    def source_authority_contract(cls) -> dict:
        return build_source_authority_contract(
            kind=cls.SOURCE_KIND,
            authorities=cls.SOURCE_AUTHORITIES,
            no_business_fact_authority=cls.NO_BUSINESS_FACT_AUTHORITY,
            fallback_policy_provider=cls.DEFAULT_POLICY_SOURCE_KIND,
        )

    @classmethod
    def default_policy_source_authority_contract(cls) -> dict:
        return build_source_authority_contract(
            kind=cls.DEFAULT_POLICY_SOURCE_KIND,
            authorities=("DEFAULT_PRODUCT_POLICY", "extension_hook:smart_core_build_default_product_policy"),
            rebuildable=None,
            no_business_fact_authority=True,
            platform_default=True,
            default_policy_node_source=DEFAULT_POLICY_NODE_SOURCE_KIND,
        )

    @classmethod
    def platform_policy_source_authority_contract(cls, *, platform_db: str = "") -> dict:
        return build_source_authority_contract(
            kind="platform_product_policy_projection",
            authorities=("sc.product.policy", "ir.config_parameter:smart_core.platform_release_db"),
            no_business_fact_authority=cls.NO_BUSINESS_FACT_AUTHORITY,
            platform_db=str(platform_db or "").strip(),
            runtime_carrier="delivery_engine_v1.product_policy",
        )

    def _platform_policy_db(self) -> str:
        try:
            configured = self.env["ir.config_parameter"].sudo().get_param("smart_core.platform_release_db", "")
        except Exception:
            configured = ""
        return str(configured or "").strip() or "sc_platform_core"

    def _load_platform_policy(self, *, product_key: str) -> dict | None:
        if api is None or Registry is None:
            return None
        platform_db = self._platform_policy_db()
        current_db = str(getattr(getattr(self.env, "cr", None), "dbname", "") or "").strip()
        if not platform_db or platform_db == current_db:
            return None
        try:
            registry = Registry(platform_db)
            with registry.cursor() as cr:
                read_env = api.Environment(cr, SUPERUSER_ID, dict(getattr(self.env, "context", {}) or {}))
                rec = read_env["sc.product.policy"].sudo().search(
                    [("product_key", "=", str(product_key or "").strip()), ("active", "=", True)],
                    limit=1,
                )
                if not rec:
                    return None
                payload = rec.to_runtime_dict()
                if not isinstance(payload, dict) or not payload.get("product_key"):
                    return None
                payload["policy_source_authority"] = self.platform_policy_source_authority_contract(
                    platform_db=platform_db,
                )
                payload["platform_policy_db"] = platform_db
                return payload
        except Exception:
            return None

    def _default_product_policy(self) -> dict:
        if callable(call_extension_hook_first):
            hook_payload = call_extension_hook_first(
                self.env,
                "smart_core_build_default_product_policy",
                self.env,
            )
            if isinstance(hook_payload, dict) and str(hook_payload.get("product_key") or "").strip():
                payload = copy.deepcopy(hook_payload)
                payload.setdefault("policy_source_authority", {
                    "kind": "extension_default_product_policy_provider",
                    "authorities": ["extension_hook:smart_core_build_default_product_policy"],
                    "projection_only": True,
                    "no_business_fact_authority": True,
                })
                return payload
        payload = copy.deepcopy(DEFAULT_PRODUCT_POLICY)
        payload.setdefault("policy_source_authority", self.default_policy_source_authority_contract())
        _mark_legacy_default_policy_nodes(payload)
        return payload

    def _default_policy_for_identity(self, *, base_product_key: str, edition_key: str) -> dict:
        base_key = str(base_product_key or "").strip() or LEGACY_DEFAULT_BASE_PRODUCT_KEY
        edition = str(edition_key or "").strip() or "standard"
        return _minimal_default_product_policy(base_product_key=base_key, edition_key=edition)

    def _minimal_policy_for_resolved_identity(self, *, product_key: str, base_product_key: str, edition_key: str) -> dict:
        payload = self._default_policy_for_identity(base_product_key=base_product_key, edition_key=edition_key)
        payload["product_key"] = str(product_key or "").strip() or payload.get("product_key")
        payload["base_product_key"] = str(base_product_key or "").strip() or payload.get("base_product_key")
        payload["edition_key"] = str(edition_key or "").strip() or payload.get("edition_key")
        return payload

    def _catalog_backed_policy(self, *, product_key: str) -> dict | None:
        if not self._model_registered("ir.ui.menu"):
            return None
        try:
            from odoo.addons.smart_core.delivery.product_policy_catalog_sync_service import (
                ProductPolicyCatalogSyncService,
            )

            payload = ProductPolicyCatalogSyncService(self.env).build_catalog_policy_payload(
                product_key=product_key,
            )
        except Exception:
            return None
        if not isinstance(payload, dict) or not payload.get("product_key"):
            return None
        if not (payload.get("menu_groups") or payload.get("scenes") or payload.get("capabilities")):
            return None
        return payload

    def _policy_has_surface(self, payload: dict) -> bool:
        return bool(
            isinstance(payload, dict)
            and (payload.get("menu_groups") or payload.get("scenes") or payload.get("capabilities"))
        )

    def _policy_needs_catalog_refresh(self, payload: dict) -> bool:
        if not isinstance(payload, dict):
            return True
        # Native action/menu release policies can be complete without scene entries:
        # scenes are only required for scene-first products, while user-visible
        # menu publishing is driven by menu_groups plus capabilities.
        return not (payload.get("menu_groups") and payload.get("capabilities"))

    def _is_catalog_backed_product(self, *, base_product_key: str) -> bool:
        try:
            from odoo.addons.smart_core.delivery.product_policy_catalog_sync_service import (
                ProductPolicyCatalogSyncService,
            )

            key, base_key, edition_key = self.resolve_policy_identity(
                base_product_key=base_product_key,
            )
            return ProductPolicyCatalogSyncService(self.env)._is_catalog_backed_product(
                identity={
                    "product_key": key,
                    "base_product_key": base_key,
                    "edition_key": edition_key,
                }
            )
        except Exception:
            return False

    def _stable_policy_domain(self, *, base_product_key: str):
        return [
            ("base_product_key", "=", str(base_product_key or "").strip() or LEGACY_DEFAULT_BASE_PRODUCT_KEY),
            ("state", "=", "stable"),
            ("access_level", "=", "public"),
            ("active", "=", True),
        ]

    def resolve_policy_identity(
        self,
        *,
        product_key: str | None = None,
        edition_key: str | None = None,
        base_product_key: str | None = None,
    ) -> tuple[str, str, str]:
        explicit_product_key = str(product_key or "").strip()
        explicit_edition_key = str(edition_key or "").strip()
        explicit_base_product_key = str(base_product_key or "").strip() or LEGACY_DEFAULT_BASE_PRODUCT_KEY
        if explicit_product_key:
            parts = explicit_product_key.split(".", 1)
            if len(parts) == 2 and parts[0] and parts[1]:
                return explicit_product_key, parts[0], parts[1]
            return explicit_product_key, explicit_base_product_key, explicit_edition_key or "standard"
        resolved_edition_key = explicit_edition_key or DEFAULT_PRODUCT_POLICY["edition_key"]
        resolved_base_product_key = explicit_base_product_key or DEFAULT_PRODUCT_POLICY["base_product_key"]
        return (
            f"{resolved_base_product_key}.{resolved_edition_key}",
            resolved_base_product_key,
            resolved_edition_key,
        )

    def _model_registered(self, model_name: str) -> bool:
        token = str(model_name or "").strip()
        if not token:
            return False
        registry = getattr(self.env, "registry", None)
        models = getattr(registry, "models", {}) if registry is not None else {}
        return token in models

    def _snapshot_binding_is_releaseable(self, *, scene_key: str, product_key: str, binding: dict | None) -> bool:
        if not self._model_registered("sc.scene.snapshot"):
            return False
        row = binding if isinstance(binding, dict) else {}
        version = str(row.get("version") or "").strip() or "v1"
        channel = str(row.get("channel") or "").strip() or "stable"
        rec = self.env["sc.scene.snapshot"].sudo().search(
            [
                ("scene_key", "=", scene_key),
                ("product_key", "=", product_key),
                ("version", "=", version),
                ("channel", "=", channel),
                ("state", "=", "stable"),
                ("is_active", "=", True),
                ("active", "=", True),
            ],
            limit=1,
        )
        return bool(rec)

    def _access_allowed(self, payload: dict, *, role_code: str) -> bool:
        access_level = str(payload.get("access_level") or "").strip() or "public"
        if access_level == "public":
            return True
        if access_level == "internal":
            return False
        if access_level == "role_restricted":
            allowed = payload.get("allowed_role_codes") if isinstance(payload.get("allowed_role_codes"), list) else []
            return str(role_code or "").strip() in {str(item or "").strip() for item in allowed if str(item or "").strip()}
        return False

    def _policy_releaseable(self, payload: dict) -> bool:
        state = str(payload.get("state") or "").strip() or "draft"
        return state in self.RELEASEABLE_STATES

    def _attach_edition_diagnostics(
        self,
        payload: dict,
        *,
        requested_product_key: str,
        requested_base_product_key: str,
        requested_edition_key: str,
        role_code: str,
        fallback_reason: str = "",
        access_allowed: bool = True,
    ) -> dict:
        row = copy.deepcopy(payload if isinstance(payload, dict) else {})
        row["edition_diagnostics"] = {
            "requested_product_key": requested_product_key,
            "requested_base_product_key": requested_base_product_key,
            "requested_edition_key": requested_edition_key,
            "resolved_product_key": str(row.get("product_key") or "").strip(),
            "resolved_base_product_key": str(row.get("base_product_key") or "").strip(),
            "resolved_edition_key": str(row.get("edition_key") or "").strip(),
            "requested_role_code": str(role_code or "").strip(),
            "policy_state": str(row.get("state") or "").strip(),
            "access_level": str(row.get("access_level") or "").strip(),
            "access_allowed": bool(access_allowed),
            "fallback_reason": str(fallback_reason or "").strip(),
            "fallback_applied": bool(fallback_reason),
        }
        return row

    def _fallback_stable_policy(self, *, base_product_key: str) -> dict:
        try:
            rec = self.env["sc.product.policy"].sudo().search(
                self._stable_policy_domain(base_product_key=base_product_key),
                order="edition_key asc, id asc",
                limit=1,
            )
        except Exception:
            rec = None
        if rec:
            return rec.to_runtime_dict()
        fallback = self._default_policy_for_identity(base_product_key=base_product_key, edition_key="standard")
        fallback["state"] = "stable"
        fallback["access_level"] = "public"
        fallback["allowed_role_codes"] = []
        return fallback

    def _sanitize_scene_version_bindings(self, payload: dict) -> dict:
        bindings = payload.get("scene_version_bindings") if isinstance(payload.get("scene_version_bindings"), dict) else {}
        sanitized = {}
        diagnostics = {}
        for scene_key, binding in bindings.items():
            key = str(scene_key or "").strip()
            if not key:
                continue
            row = binding if isinstance(binding, dict) else {}
            product_key = ""
            for scene_row in payload.get("scenes") or []:
                if isinstance(scene_row, dict) and str(scene_row.get("scene_key") or "").strip() == key:
                    product_key = str(scene_row.get("product_key") or "").strip()
                    break
            if not product_key:
                diagnostics[key] = {
                    "binding_allowed": False,
                    "reason": "SCENE_POLICY_MISSING",
                }
                continue
            if self._snapshot_binding_is_releaseable(scene_key=key, product_key=product_key, binding=row):
                sanitized[key] = {
                    "version": str(row.get("version") or "").strip() or "v1",
                    "channel": str(row.get("channel") or "").strip() or "stable",
                }
                diagnostics[key] = {
                    "binding_allowed": True,
                    "reason": "ACTIVE_STABLE_BOUND",
                }
            else:
                diagnostics[key] = {
                    "binding_allowed": False,
                    "reason": "SNAPSHOT_NOT_ACTIVE_STABLE",
                }
        payload["scene_version_bindings"] = sanitized
        payload["scene_binding_diagnostics"] = diagnostics
        return payload

    def get_policy(
        self,
        product_key: str | None = None,
        *,
        edition_key: str | None = None,
        base_product_key: str | None = None,
        role_code: str | None = None,
        enforce_release: bool = False,
        enforce_access: bool = False,
    ) -> dict:
        key, resolved_base_product_key, resolved_edition_key = self.resolve_policy_identity(
            product_key=product_key,
            edition_key=edition_key,
            base_product_key=base_product_key,
        )
        resolved_role_code = str(role_code or "").strip()
        try:
            rec = self.env["sc.product.policy"].sudo().search([("product_key", "=", key), ("active", "=", True)], limit=1)
        except Exception:
            rec = None
        if rec:
            payload = rec.to_runtime_dict()
            if isinstance(payload, dict) and payload.get("product_key"):
                if self._is_catalog_backed_product(base_product_key=resolved_base_product_key) and self._policy_needs_catalog_refresh(payload):
                    catalog_payload = self._catalog_backed_policy(product_key=key)
                    if catalog_payload:
                        payload = catalog_payload
                if (
                    not isinstance(payload.get("policy_source_authority"), dict)
                    or not self._policy_has_surface(payload)
                ):
                    payload = self._minimal_policy_for_resolved_identity(
                        product_key=key,
                        base_product_key=resolved_base_product_key,
                        edition_key=resolved_edition_key,
                    )
                payload = self._sanitize_scene_version_bindings(payload)
                access_allowed = self._access_allowed(payload, role_code=resolved_role_code) if enforce_access else True
                release_allowed = self._policy_releaseable(payload) if enforce_release else True
                if access_allowed and release_allowed:
                    return self._attach_edition_diagnostics(
                        payload,
                        requested_product_key=key,
                        requested_base_product_key=resolved_base_product_key,
                        requested_edition_key=resolved_edition_key,
                        role_code=resolved_role_code,
                        access_allowed=access_allowed,
                    )
                fallback_reason = "EDITION_ACCESS_DENIED" if not access_allowed else "EDITION_STATE_NOT_RELEASEABLE"
                fallback = self._sanitize_scene_version_bindings(
                    self._fallback_stable_policy(base_product_key=resolved_base_product_key)
                )
                return self._attach_edition_diagnostics(
                    fallback,
                    requested_product_key=key,
                    requested_base_product_key=resolved_base_product_key,
                    requested_edition_key=resolved_edition_key,
                    role_code=resolved_role_code,
                    fallback_reason=fallback_reason,
                    access_allowed=access_allowed,
                )
        platform_payload = self._load_platform_policy(product_key=key)
        if platform_payload:
            if self._is_catalog_backed_product(base_product_key=resolved_base_product_key) and self._policy_needs_catalog_refresh(platform_payload):
                catalog_payload = self._catalog_backed_policy(product_key=key)
                if catalog_payload:
                    platform_payload = catalog_payload
            if (
                not isinstance(platform_payload.get("policy_source_authority"), dict)
                or not self._policy_has_surface(platform_payload)
            ):
                platform_payload = self._minimal_policy_for_resolved_identity(
                    product_key=key,
                    base_product_key=resolved_base_product_key,
                    edition_key=resolved_edition_key,
                )
            payload = self._sanitize_scene_version_bindings(platform_payload)
            access_allowed = self._access_allowed(payload, role_code=resolved_role_code) if enforce_access else True
            release_allowed = self._policy_releaseable(payload) if enforce_release else True
            if access_allowed and release_allowed:
                return self._attach_edition_diagnostics(
                    payload,
                    requested_product_key=key,
                    requested_base_product_key=resolved_base_product_key,
                    requested_edition_key=resolved_edition_key,
                    role_code=resolved_role_code,
                    access_allowed=access_allowed,
                )
            fallback_reason = "PLATFORM_EDITION_ACCESS_DENIED" if not access_allowed else "PLATFORM_EDITION_STATE_NOT_RELEASEABLE"
            fallback = self._sanitize_scene_version_bindings(
                self._fallback_stable_policy(base_product_key=resolved_base_product_key)
            )
            return self._attach_edition_diagnostics(
                fallback,
                requested_product_key=key,
                requested_base_product_key=resolved_base_product_key,
                requested_edition_key=resolved_edition_key,
                role_code=resolved_role_code,
                fallback_reason=fallback_reason,
                access_allowed=access_allowed,
            )
        fallback = self._minimal_policy_for_resolved_identity(
            product_key=key,
            base_product_key=resolved_base_product_key,
            edition_key=resolved_edition_key,
        )
        catalog_fallback_applied = False
        if self._is_catalog_backed_product(base_product_key=resolved_base_product_key):
            catalog_payload = self._catalog_backed_policy(product_key=key)
            if catalog_payload:
                fallback = catalog_payload
                catalog_fallback_applied = True
        if (enforce_release or enforce_access) and not catalog_fallback_applied:
            fallback = self._sanitize_scene_version_bindings(
                self._fallback_stable_policy(base_product_key=resolved_base_product_key)
            )
        else:
            fallback = self._sanitize_scene_version_bindings(fallback)
        return self._attach_edition_diagnostics(
            fallback,
            requested_product_key=key,
            requested_base_product_key=resolved_base_product_key,
            requested_edition_key=resolved_edition_key,
            role_code=resolved_role_code,
            fallback_reason="POLICY_NOT_FOUND",
            access_allowed=True,
        )
