# -*- coding: utf-8 -*-
from __future__ import annotations

import importlib.util
import sys
import types
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
MODULE_PATH = ROOT / "addons" / "smart_core" / "delivery" / "menu_service.py"


def _install_module(name: str, **attrs):
    module = types.ModuleType(name)
    for key, value in attrs.items():
        setattr(module, key, value)
    sys.modules[name] = module
    return module


def _install_stubs(extension_hook=None):
    for name in list(sys.modules):
        if name.startswith("odoo"):
            sys.modules.pop(name, None)
    _install_module("odoo")
    _install_module("odoo.addons")
    _install_module("odoo.addons.smart_core")
    _install_module("odoo.addons.smart_core.core")
    _install_module("odoo.addons.smart_core.delivery")
    _install_module("odoo.addons.smart_core.utils")
    _install_module(
        "odoo.addons.smart_core.core.source_authority",
        build_source_authority_contract=lambda **kwargs: dict(kwargs),
    )
    _install_module(
        "odoo.addons.smart_core.core.delivery_menu_defaults",
        build_delivery_menu_child=lambda **kwargs: dict(kwargs),
        build_delivery_menu_group=lambda **kwargs: dict(kwargs),
        build_delivery_menu_root=lambda **kwargs: dict(kwargs),
        synthetic_menu_id=lambda *parts: abs(hash(parts)) % 1000000,
    )

    class _MenuDeliveryConvergenceService:
        def __init__(self, env=None):
            self.env = env
            self.rename_labels = {}

        def _classify_leaf(self, *args, **kwargs):
            return "delivery_user"

    _install_module(
        "odoo.addons.smart_core.delivery.menu_delivery_convergence_service",
        MenuDeliveryConvergenceService=_MenuDeliveryConvergenceService,
    )
    _install_module(
        "odoo.addons.smart_core.delivery.native_config_menu_projection",
        native_config_delivery_groups=lambda env=None: [],
    )
    _install_module(
        "odoo.addons.smart_core.utils.backend_contract_boundaries",
        MENU_CONFIG_POLICY_MODEL="ui.menu.config.policy",
    )
    _install_module(
        "odoo.addons.smart_core.utils.extension_hooks",
        call_extension_hook_first=extension_hook or (lambda *args, **kwargs: None),
    )


def _load_menu_service(extension_hook=None):
    _install_stubs(extension_hook=extension_hook)
    sys.modules.pop("smart_core_menu_service_under_test", None)
    spec = importlib.util.spec_from_file_location("smart_core_menu_service_under_test", MODULE_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


class DeliveryMenuGroupOrderBoundaryTests(unittest.TestCase):
    def test_core_default_group_order_does_not_embed_construction_finance_group(self):
        module = _load_menu_service()

        self.assertNotIn("财务中心", module.MenuService.BUSINESS_GROUP_DISPLAY_ORDER)
        self.assertNotIn("财务中心", module.MenuService()._business_group_display_order)

    def test_construction_finance_group_order_must_be_supplied_by_extension_hook(self):
        module = _load_menu_service(
            extension_hook=lambda env, hook_name, *args, **kwargs: {"财务中心": 60}
            if hook_name == "smart_core_business_nav_group_display_order"
            else None
        )

        self.assertEqual(module.MenuService(env=object())._business_group_display_order.get("财务中心"), 60)


if __name__ == "__main__":
    unittest.main()
