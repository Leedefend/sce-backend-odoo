#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

import importlib.util
import sys
import types
import unittest
from datetime import date
from decimal import Decimal
from pathlib import Path
from types import SimpleNamespace


ROOT = Path(__file__).resolve().parents[3]
SMART_CORE = ROOT / "addons/smart_core"


def _install_module(name, **attrs):
    module = types.ModuleType(name)
    for key, value in attrs.items():
        setattr(module, key, value)
    sys.modules[name] = module
    return module


def _load_module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


def _install_basic_odoo():
    exc_mod = _install_module(
        "odoo.exceptions",
        AccessError=type("AccessError", (Exception,), {}),
        MissingError=type("MissingError", (Exception,), {}),
        ValidationError=type("ValidationError", (Exception,), {}),
    )
    odoo = _install_module(
        "odoo",
        SUPERUSER_ID=1,
        api=SimpleNamespace(Environment=lambda cr, uid, ctx: None),
        exceptions=exc_mod,
        fields=SimpleNamespace(Datetime=SimpleNamespace(now=lambda: "2026-01-01 00:00:00")),
    )
    sys.modules["odoo"] = odoo
    sys.modules.setdefault("odoo.addons", types.ModuleType("odoo.addons"))
    smart_core_pkg = sys.modules.setdefault("odoo.addons.smart_core", types.ModuleType("odoo.addons.smart_core"))
    smart_core_pkg.__path__ = [str(SMART_CORE)]
    return odoo


def _load_business_config_surface():
    _install_basic_odoo()
    handlers_pkg = _install_module("odoo.addons.smart_core.handlers")
    core_pkg = _install_module("odoo.addons.smart_core.core")
    handlers_pkg.__path__ = [str(SMART_CORE / "handlers")]
    core_pkg.__path__ = [str(SMART_CORE / "core")]
    base_mod = _install_module("odoo.addons.smart_core.core.base_handler")
    base_mod.BaseIntentHandler = type("BaseIntentHandler", (), {})
    return _load_module(
        "odoo.addons.smart_core.handlers.business_config_surface",
        SMART_CORE / "handlers/business_config_surface.py",
    )


def _load_snapshot_service():
    _install_basic_odoo()
    core_pkg = sys.modules.setdefault("odoo.addons.smart_core.core", types.ModuleType("odoo.addons.smart_core.core"))
    delivery_pkg = sys.modules.setdefault("odoo.addons.smart_core.delivery", types.ModuleType("odoo.addons.smart_core.delivery"))
    modules_pkg = sys.modules.setdefault("odoo.modules", types.ModuleType("odoo.modules"))
    core_pkg.__path__ = [str(SMART_CORE / "core")]
    delivery_pkg.__path__ = [str(SMART_CORE / "delivery")]
    registry_mod = _install_module("odoo.modules.registry", Registry=lambda db: None)
    modules_pkg.registry = registry_mod

    _load_module(
        "odoo.addons.smart_core.core.source_authority",
        SMART_CORE / "core/source_authority.py",
    )
    delivery_engine = _install_module("odoo.addons.smart_core.delivery.delivery_engine")
    delivery_engine.DeliveryEngine = type("DeliveryEngine", (), {"__init__": lambda self, env: None})
    promotion = _install_module("odoo.addons.smart_core.delivery.edition_release_snapshot_promotion_service")
    promotion.EditionReleaseSnapshotPromotionService = type(
        "EditionReleaseSnapshotPromotionService",
        (),
        {"__init__": lambda self, env: None},
    )
    policy = _install_module("odoo.addons.smart_core.delivery.product_policy_service")
    policy.ProductPolicyService = type("ProductPolicyService", (), {"__init__": lambda self, env: None})
    return _load_module(
        "odoo.addons.smart_core.delivery.edition_release_snapshot_service",
        SMART_CORE / "delivery/edition_release_snapshot_service.py",
    )


def _load_middlewares():
    return _load_module("smart_core_test_middlewares", SMART_CORE / "core/middlewares.py")


def _load_nav_dispatcher():
    _install_basic_odoo()
    app_pkg = sys.modules.setdefault("odoo.addons.smart_core.app_config_engine", types.ModuleType("odoo.addons.smart_core.app_config_engine"))
    services_pkg = sys.modules.setdefault(
        "odoo.addons.smart_core.app_config_engine.services",
        types.ModuleType("odoo.addons.smart_core.app_config_engine.services"),
    )
    dispatchers_pkg = sys.modules.setdefault(
        "odoo.addons.smart_core.app_config_engine.services.dispatchers",
        types.ModuleType("odoo.addons.smart_core.app_config_engine.services.dispatchers"),
    )
    resolvers_pkg = sys.modules.setdefault(
        "odoo.addons.smart_core.app_config_engine.services.resolvers",
        types.ModuleType("odoo.addons.smart_core.app_config_engine.services.resolvers"),
    )
    security_pkg = sys.modules.setdefault("odoo.addons.smart_core.security", types.ModuleType("odoo.addons.smart_core.security"))
    app_pkg.__path__ = [str(SMART_CORE / "app_config_engine")]
    services_pkg.__path__ = [str(SMART_CORE / "app_config_engine/services")]
    dispatchers_pkg.__path__ = [str(SMART_CORE / "app_config_engine/services/dispatchers")]
    resolvers_pkg.__path__ = [str(SMART_CORE / "app_config_engine/services/resolvers")]
    security_pkg.__path__ = [str(SMART_CORE / "security")]

    platform_admin = _install_module("odoo.addons.smart_core.security.platform_admin")
    platform_admin.user_is_platform_admin = lambda env, user=None: False
    action_resolver = _install_module("odoo.addons.smart_core.app_config_engine.services.resolvers.action_resolver")
    action_resolver.ActionResolver = type("ActionResolver", (), {"__init__": lambda self, *args, **kwargs: None})
    return _load_module(
        "odoo.addons.smart_core.app_config_engine.services.dispatchers.nav_dispatcher",
        SMART_CORE / "app_config_engine/services/dispatchers/nav_dispatcher.py",
    )


class StableSerializationBoundaryTests(unittest.TestCase):
    def test_business_config_hash_accepts_projection_scalars(self):
        module = _load_business_config_surface()

        digest = module._hash_payload({"day": date(2026, 6, 30), "amount": Decimal("12.30")})

        self.assertRegex(digest, r"^[0-9a-f]{64}$")

    def test_release_snapshot_stable_json_accepts_projection_scalars(self):
        module = _load_snapshot_service()

        value = module._stable_json({"day": date(2026, 6, 30), "amount": Decimal("12.30")})

        self.assertEqual(value, '{"amount":"12.30","day":"2026-06-30"}')

    def test_middleware_cache_key_accepts_projection_scalars(self):
        module = _load_middlewares()
        middleware = module.CachingMiddleware()
        context = SimpleNamespace(
            params={"day": date(2026, 6, 30)},
            ctx={"amount": Decimal("12.30")},
        )

        value = middleware._generate_cache_key("x.intent", context)

        self.assertRegex(value, r"^[0-9a-f]{32}$")

    def test_nav_fingerprint_accepts_projection_scalars(self):
        module = _load_nav_dispatcher()

        value = module.NavDispatcher._nav_fingerprint(
            1,
            date(2026, 6, 30),
            ["base.group_user", Decimal("12.30")],
        )

        self.assertRegex(value, r"^[0-9a-f]{32}$")

    def test_nav_front_contract_preserves_record_scope_policy_with_project_alias(self):
        module = _load_nav_dispatcher()
        dispatcher = module.NavDispatcher(None, None)

        nodes = dispatcher._to_front_contract(
            [
                {
                    "menu_id": 1,
                    "label": "Explicit",
                    "record_scope_policy": "global",
                    "project_scope_policy": "current_project",
                },
                {
                    "menu_id": 2,
                    "label": "Legacy",
                    "project_scope_policy": "current_project",
                },
            ]
        )

        explicit_meta = nodes[0]["meta"]
        legacy_meta = nodes[1]["meta"]
        self.assertEqual(explicit_meta["record_scope_policy"], "global")
        self.assertEqual(explicit_meta["project_scope_policy"], "current_project")
        self.assertEqual(legacy_meta["record_scope_policy"], "current_record")
        self.assertEqual(legacy_meta["project_scope_policy"], "current_project")


if __name__ == "__main__":
    unittest.main()
