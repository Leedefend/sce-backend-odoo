# -*- coding: utf-8 -*-
import importlib.util
import sys
import types
import unittest
from pathlib import Path


class _BaseIntentHandler:
    def __init__(self, env=None, request=None, params=None, context=None):
        self.env = env or types.SimpleNamespace(uid=9)
        self.request = request
        self.params = params or {}
        self.context = context or {}


def _install_module(name, **attrs):
    module = types.ModuleType(name)
    for key, value in attrs.items():
        setattr(module, key, value)
    sys.modules[name] = module
    return module


def _load_handler():
    root = Path(__file__).resolve().parents[1]
    _install_module("odoo")
    _install_module("odoo.addons")
    smart_core_mod = _install_module("odoo.addons.smart_core")
    handlers_mod = _install_module("odoo.addons.smart_core.handlers")
    core_mod = _install_module("odoo.addons.smart_core.core")
    smart_core_mod.__path__ = [str(root)]
    handlers_mod.__path__ = [str(root / "handlers")]
    core_mod.__path__ = [str(root / "core")]

    _install_module("odoo.addons.smart_core.core.base_handler", BaseIntentHandler=_BaseIntentHandler)
    _install_module(
        "odoo.addons.smart_core.core.scene_provider",
        load_scenes_from_db_or_fallback=lambda *args, **kwargs: {
            "scenes": [{"key": "workspace.home", "label": "Home", "target": {"route": "/s/workspace.home"}}]
        },
    )
    _install_module(
        "odoo.addons.smart_core.core.unified_page_contract_v2_client",
        resolve_client_type=lambda headers, payload: "web_mobile",
        resolve_delivery_profile=lambda client_type, payload=None: "mobile_compact",
        trim_navigation_contract_for_client=lambda contract, **kwargs: {
            **contract,
            "trim_kwargs": kwargs,
        },
    )

    request_params_name = "odoo.addons.smart_core.core.request_params"
    sys.modules.pop(request_params_name, None)
    request_params_spec = importlib.util.spec_from_file_location(
        request_params_name, root / "core" / "request_params.py"
    )
    request_params_module = importlib.util.module_from_spec(request_params_spec)
    sys.modules[request_params_name] = request_params_module
    request_params_spec.loader.exec_module(request_params_module)

    module_name = "odoo.addons.smart_core.handlers.app_shell"
    sys.modules.pop(module_name, None)
    spec = importlib.util.spec_from_file_location(module_name, root / "handlers" / "app_shell.py")
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


class TestAppShellBoundaries(unittest.TestCase):
    def setUp(self):
        self.module = _load_handler()

    def test_nav_rejects_invalid_max_items(self):
        handler = self.module.AppNavHandler(env=types.SimpleNamespace(uid=9))

        result = handler.handle(payload={"params": {"max_items": "bad"}})

        self.assertFalse(result["ok"])
        self.assertEqual(result["code"], 400)
        self.assertEqual(result["error"]["message"], "max_items 无效")

    def test_nav_rejects_invalid_max_depth(self):
        handler = self.module.AppNavHandler(env=types.SimpleNamespace(uid=9))

        result = handler.handle(payload={"params": {"max_depth": 0}})

        self.assertFalse(result["ok"])
        self.assertEqual(result["code"], 400)
        self.assertEqual(result["error"]["message"], "max_depth 无效")

    def test_nav_passes_valid_limits_to_trim(self):
        handler = self.module.AppNavHandler(env=types.SimpleNamespace(uid=9))

        result = handler.handle(payload={"params": {"max_items": "3", "max_depth": "2"}})

        self.assertTrue(result["ok"])
        trim_kwargs = result["data"]["trim_kwargs"]
        self.assertEqual(trim_kwargs["max_items"], 3)
        self.assertEqual(trim_kwargs["max_depth"], 2)

    def test_open_reads_nested_app_param(self):
        handler = self.module.AppOpenHandler(env=types.SimpleNamespace(uid=9))

        result = handler.handle(payload={"params": {"app": "workspace"}})

        self.assertTrue(result["ok"])
        self.assertEqual(result["data"]["subject"], "ui.contract")
        self.assertEqual(result["data"]["scene_key"], "workspace.home")

    def test_open_workspace_has_minimum_fallback(self):
        original_scene_list = self.module._scene_list
        self.module._scene_list = lambda env: []
        try:
            handler = self.module.AppOpenHandler(env=types.SimpleNamespace(uid=9))

            result = handler.handle(payload={"params": {"app": "workspace"}})
        finally:
            self.module._scene_list = original_scene_list

        self.assertTrue(result["ok"])
        self.assertEqual(result["data"]["scene_key"], "workspace.home")
        self.assertEqual(result["data"]["route"], "/s/workspace.home")


if __name__ == "__main__":
    unittest.main()
