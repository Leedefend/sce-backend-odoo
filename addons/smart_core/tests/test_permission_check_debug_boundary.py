# -*- coding: utf-8 -*-
import importlib.util
import sys
import types
import unittest
from pathlib import Path


class _BaseIntentHandler:
    def __init__(self, env=None, params=None):
        self.env = env
        self.params = params or {}


class _Env(dict):
    cr = types.SimpleNamespace(dbname="test_db")
    registry = types.SimpleNamespace(models=set())


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
    _install_module("odoo.addons.smart_core.handlers.system_init")

    params_name = "odoo.addons.smart_core.core.request_params"
    sys.modules.pop(params_name, None)
    params_spec = importlib.util.spec_from_file_location(params_name, root / "core" / "request_params.py")
    params_module = importlib.util.module_from_spec(params_spec)
    sys.modules[params_name] = params_module
    params_spec.loader.exec_module(params_module)

    module_name = "odoo.addons.smart_core.handlers.permission_check"
    sys.modules.pop(module_name, None)
    spec = importlib.util.spec_from_file_location(module_name, root / "handlers" / "permission_check.py")
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


class TestPermissionCheckDebugBoundary(unittest.TestCase):
    def test_string_false_debug_does_not_include_debug_payload(self):
        module = _load_handler()
        handler = module.PermissionCheckHandler(env=_Env(), params={"debug": "false", "required_flag": "x.flag"})

        result = handler.handle({}, {})

        self.assertTrue(result["ok"])
        self.assertNotIn("debug", result["data"])

    def test_string_true_debug_includes_debug_payload(self):
        module = _load_handler()
        handler = module.PermissionCheckHandler(env=_Env(), params={"debug": "true", "required_flag": "x.flag"})

        result = handler.handle({}, {})

        self.assertTrue(result["ok"])
        self.assertIn("debug", result["data"])


if __name__ == "__main__":
    unittest.main()
