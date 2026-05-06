# -*- coding: utf-8 -*-
import importlib.util
import sys
import types
import unittest
from pathlib import Path


class _BaseIntentHandler:
    def __init__(self, env=None, params=None, context=None):
        self.env = env or {}
        self.params = params or {}
        self.context = context or {}


class _Env(dict):
    context = {}


def _install_base_modules(root):
    odoo_mod = types.ModuleType("odoo")
    http_mod = types.ModuleType("odoo.http")
    http_mod.request = types.SimpleNamespace(httprequest=types.SimpleNamespace(headers={}))
    odoo_mod.http = http_mod

    addons_mod = types.ModuleType("odoo.addons")
    smart_core_mod = types.ModuleType("odoo.addons.smart_core")
    handlers_mod = types.ModuleType("odoo.addons.smart_core.handlers")
    core_mod = types.ModuleType("odoo.addons.smart_core.core")
    smart_core_mod.__path__ = [str(root)]
    handlers_mod.__path__ = [str(root / "handlers")]
    core_mod.__path__ = [str(root / "core")]

    base_mod = types.ModuleType("odoo.addons.smart_core.core.base_handler")
    base_mod.BaseIntentHandler = _BaseIntentHandler
    sys.modules.update(
        {
            "odoo": odoo_mod,
            "odoo.http": http_mod,
            "odoo.addons": addons_mod,
            "odoo.addons.smart_core": smart_core_mod,
            "odoo.addons.smart_core.handlers": handlers_mod,
            "odoo.addons.smart_core.core": core_mod,
            "odoo.addons.smart_core.core.base_handler": base_mod,
        }
    )


def _load_module(filename):
    root = Path(__file__).resolve().parents[1]
    _install_base_modules(root)
    module_name = f"odoo.addons.smart_core.handlers.{filename[:-3]}"
    sys.modules.pop(module_name, None)
    spec = importlib.util.spec_from_file_location(module_name, root / "handlers" / filename)
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


class TestMetadataHandlerBoundaries(unittest.TestCase):
    def test_load_metadata_missing_model_returns_structured_error(self):
        module = _load_module("load_metadata.py")
        handler = module.LoadMetadataHandler(env=_Env(), params={})

        result = handler.handle()

        self.assertFalse(result["ok"])
        self.assertEqual(result["code"], 400)
        self.assertEqual(result["error"]["message"], "缺少 model 参数")

    def test_load_metadata_unknown_model_returns_not_found(self):
        module = _load_module("load_metadata.py")
        handler = module.LoadMetadataHandler(env=_Env(), params={"model": "missing.model"})

        result = handler.handle()

        self.assertFalse(result["ok"])
        self.assertEqual(result["code"], 404)

    def test_meta_describe_missing_model_includes_top_level_status(self):
        module = _load_module("meta_describe.py")
        handler = module.MetaDescribeHandler(env=_Env(), params={})

        result = handler.run()

        self.assertFalse(result["ok"])
        self.assertEqual(result["code"], 400)

    def test_meta_describe_unknown_model_returns_not_found(self):
        module = _load_module("meta_describe.py")
        handler = module.MetaDescribeHandler(env=_Env(), params={"model": "missing.model"})

        result = handler.run()

        self.assertFalse(result["ok"])
        self.assertEqual(result["code"], 404)


if __name__ == "__main__":
    unittest.main()
