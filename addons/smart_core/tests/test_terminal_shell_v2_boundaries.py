# -*- coding: utf-8 -*-
import importlib.util
import sys
import types
import unittest
from pathlib import Path


class _BaseIntentHandler:
    def __init__(self, env=None, su_env=None, request=None, params=None, context=None, payload=None):
        self.env = env
        self.su_env = su_env
        self.request = request
        self.params = params or {}
        self.context = context or {}
        self.payload = payload or {}


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
    _install_module("odoo.addons.smart_core.core.handler_registry", HANDLER_REGISTRY={})
    _install_module("odoo.addons.smart_core.core.unified_page_contract_v2_assembler", CONTRACT_VERSION="2.0")
    _install_module(
        "odoo.addons.smart_core.core.unified_page_contract_v2_client",
        resolve_client_type=lambda headers, params: "web_mobile",
        resolve_delivery_profile=lambda client_type, params=None: "mobile_compact",
    )

    for module_name, rel_path in (
        ("odoo.addons.smart_core.core.intent_execution_result", "core/intent_execution_result.py"),
        ("odoo.addons.smart_core.core.request_params", "core/request_params.py"),
    ):
        sys.modules.pop(module_name, None)
        spec = importlib.util.spec_from_file_location(module_name, root / rel_path)
        module = importlib.util.module_from_spec(spec)
        sys.modules[module_name] = module
        spec.loader.exec_module(module)

    module_name = "odoo.addons.smart_core.handlers.terminal_shell_v2"
    sys.modules.pop(module_name, None)
    spec = importlib.util.spec_from_file_location(module_name, root / "handlers" / "terminal_shell_v2.py")
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


class TestTerminalShellV2Boundaries(unittest.TestCase):
    def setUp(self):
        self.module = _load_handler()

    def test_invalid_max_items_returns_error_result(self):
        handler = self.module.TerminalShellV2Handler(env=object())

        result = handler.handle(payload={"params": {"max_items": "bad"}})

        self.assertFalse(result.ok)
        self.assertEqual(result.code, 400)
        self.assertEqual(result.error["message"], "max_items 无效")

    def test_invalid_max_depth_returns_error_result(self):
        handler = self.module.TerminalShellV2Handler(env=object())

        result = handler.handle(payload={"params": {"max_depth": 0}})

        self.assertFalse(result.ok)
        self.assertEqual(result.code, 400)
        self.assertEqual(result.error["message"], "max_depth 无效")


if __name__ == "__main__":
    unittest.main()
