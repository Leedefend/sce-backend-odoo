# -*- coding: utf-8 -*-
import importlib.util
import sys
import types
import unittest
from pathlib import Path


class _BaseIntentHandler:
    def __init__(self, env=None, su_env=None, params=None, context=None, payload=None):
        self.env = env
        self.su_env = su_env
        self.params = params or {}
        self.context = context or {}
        self.payload = payload or {}


class _Env(dict):
    context = {}
    user = types.SimpleNamespace(id=9, lang="")
    company = types.SimpleNamespace(id=1)
    cr = types.SimpleNamespace(dbname="test")


def _install_module(name, **attrs):
    module = types.ModuleType(name)
    for key, value in attrs.items():
        setattr(module, key, value)
    sys.modules[name] = module
    return module


def _load_handler():
    root = Path(__file__).resolve().parents[1]

    _install_module("odoo", api=types.SimpleNamespace(Environment=lambda cr, uid, ctx: None), SUPERUSER_ID=1)

    addons_mod = _install_module("odoo.addons")
    smart_core_mod = _install_module("odoo.addons.smart_core")
    handlers_mod = _install_module("odoo.addons.smart_core.handlers")
    core_mod = _install_module("odoo.addons.smart_core.core")
    utils_mod = _install_module("odoo.addons.smart_core.utils")
    addons_mod.__path__ = []
    smart_core_mod.__path__ = [str(root)]
    handlers_mod.__path__ = [str(root / "handlers")]
    core_mod.__path__ = [str(root / "core")]
    utils_mod.__path__ = [str(root / "utils")]

    base_mod = _install_module("odoo.addons.smart_core.core.base_handler")
    base_mod.BaseIntentHandler = _BaseIntentHandler
    preview_mod = _install_module("odoo.addons.smart_core.core.unified_page_contract_lite_preview")
    preview_mod.with_lite_preview_if_requested = lambda response, params, name, payload_type=None: response
    hooks_mod = _install_module("odoo.addons.smart_core.utils.extension_hooks")
    hooks_mod.call_extension_hook_first = lambda *args, **kwargs: None
    reason_mod = _install_module("odoo.addons.smart_core.utils.reason_codes")
    reason_mod.REASON_OK = "OK"
    reason_mod.REASON_PERMISSION_DENIED = "PERMISSION_DENIED"

    request_params_name = "odoo.addons.smart_core.core.request_params"
    sys.modules.pop(request_params_name, None)
    request_params_spec = importlib.util.spec_from_file_location(
        request_params_name, root / "core" / "request_params.py"
    )
    request_params_module = importlib.util.module_from_spec(request_params_spec)
    sys.modules[request_params_name] = request_params_module
    request_params_spec.loader.exec_module(request_params_module)

    module_name = "odoo.addons.smart_core.handlers.load_contract"
    sys.modules.pop(module_name, None)
    spec = importlib.util.spec_from_file_location(module_name, root / "handlers" / "load_contract.py")
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


class TestLoadContractIdBoundaries(unittest.TestCase):
    def setUp(self):
        module = _load_handler()
        self.handler = module.LoadContractHandler(env=_Env({"x.model": object()}))

    def test_invalid_menu_id_returns_bad_request_before_model_resolution(self):
        result = self.handler.handle({"params": {"menu_id": "bad"}})

        self.assertEqual(result["status"], "error")
        self.assertEqual(result["code"], 400)
        self.assertEqual(result["message"], "menu_id 无效")

    def test_invalid_action_id_returns_bad_request_before_model_resolution(self):
        result = self.handler.handle({"params": {"action_id": "bad"}})

        self.assertEqual(result["status"], "error")
        self.assertEqual(result["code"], 400)
        self.assertEqual(result["message"], "action_id 无效")

    def test_invalid_params_shape_returns_bad_request(self):
        result = self.handler.handle({"params": ["model", "x.model"]})

        self.assertEqual(result["status"], "error")
        self.assertEqual(result["code"], 400)
        self.assertEqual(result["message"], "params 无效")

    def test_invalid_model_param_returns_bad_request(self):
        result = self.handler.handle({"params": {"model": ["x.model"]}})

        self.assertEqual(result["status"], "error")
        self.assertEqual(result["code"], 400)
        self.assertEqual(result["message"], "model 无效")

    def test_invalid_model_code_param_returns_bad_request(self):
        result = self.handler.handle({"params": {"model_code": {"code": "x_model"}}})

        self.assertEqual(result["status"], "error")
        self.assertEqual(result["code"], 400)
        self.assertEqual(result["message"], "model_code 无效")

    def test_invalid_context_ids_return_bad_request(self):
        cases = [
            ("company_id", "company_id 无效"),
            ("current_project_id", "current_project_id 无效"),
        ]
        for field, message in cases:
            with self.subTest(field=field):
                result = self.handler.handle({"params": {"model": "x.model", field: "bad"}})
                self.assertEqual(result["status"], "error")
                self.assertEqual(result["code"], 400)
                self.assertEqual(result["message"], message)

    def test_invalid_cache_params_return_bad_request(self):
        cases = [
            ("version", "version 无效"),
            ("if_none_match", "if_none_match 无效"),
        ]
        for field, message in cases:
            with self.subTest(field=field):
                result = self.handler.handle({"params": {"model": "x.model", field: ["bad"]}})
                self.assertEqual(result["status"], "error")
                self.assertEqual(result["code"], 400)
                self.assertEqual(result["message"], message)


if __name__ == "__main__":
    unittest.main()
