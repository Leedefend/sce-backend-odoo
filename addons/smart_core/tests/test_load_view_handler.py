# -*- coding: utf-8 -*-
import importlib.util
import sys
import types
import unittest
from unittest.mock import patch
from pathlib import Path


class _BaseIntentHandler:
    def __init__(self, env=None, su_env=None, context=None, payload=None, params=None):
        self.env = env
        self.su_env = su_env
        self.context = context or {}
        self.payload = payload or {}
        self.params = params or (self.payload.get("params") if isinstance(self.payload, dict) else {}) or {}


class _LoadContractHandler(_BaseIntentHandler):
    def handle(self, payload=None, ctx=None):
        return {}


def _install_module(name, **attrs):
    module = types.ModuleType(name)
    for key, value in attrs.items():
        setattr(module, key, value)
    sys.modules[name] = module
    return module


def _load_handler():
    root = Path(__file__).resolve().parents[1]
    _install_module("addons")
    smart_core_mod = _install_module("addons.smart_core")
    handlers_mod = _install_module("addons.smart_core.handlers")
    core_mod = _install_module("addons.smart_core.core")
    smart_core_mod.__path__ = [str(root)]
    handlers_mod.__path__ = [str(root / "handlers")]
    core_mod.__path__ = [str(root / "core")]

    _install_module("addons.smart_core.core.base_handler", BaseIntentHandler=_BaseIntentHandler)
    _install_module("addons.smart_core.handlers.load_contract", LoadContractHandler=_LoadContractHandler)

    request_params_name = "addons.smart_core.core.request_params"
    sys.modules.pop(request_params_name, None)
    request_params_spec = importlib.util.spec_from_file_location(
        request_params_name, root / "core" / "request_params.py"
    )
    request_params_module = importlib.util.module_from_spec(request_params_spec)
    sys.modules[request_params_name] = request_params_module
    request_params_spec.loader.exec_module(request_params_module)

    module_name = "addons.smart_core.handlers.load_view"
    sys.modules.pop(module_name, None)
    spec = importlib.util.spec_from_file_location(module_name, root / "handlers" / "load_view.py")
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


class _DummyEnv:
    pass


class TestLoadViewHandler(unittest.TestCase):
    def setUp(self):
        self.module = _load_handler()

    def _make_handler(self, params):
        return self.module.LoadModelViewHandler(env=_DummyEnv(), su_env=_DummyEnv(), context={}, payload={"params": params})

    @patch("addons.smart_core.handlers.load_view.LoadContractHandler.handle")
    def test_load_view_proxies_to_load_contract_success(self, proxied_handle):
        proxied_handle.return_value = {
            "status": "success",
            "code": 200,
            "data": {"views": {"form": {"layout": []}}},
            "meta": {"etag": "abc"},
        }
        handler = self._make_handler({"model": "project.project", "view_type": "form"})
        result = handler.run()

        self.assertTrue(result.get("ok"), result)
        self.assertEqual(result.get("code"), 200)
        self.assertEqual((result.get("data") or {}).get("views"), {"form": {"layout": []}})
        self.assertEqual((result.get("meta") or {}).get("legacy_proxy"), "load_contract")

    @patch("addons.smart_core.handlers.load_view.LoadContractHandler.handle")
    def test_load_view_proxies_to_load_contract_error(self, proxied_handle):
        proxied_handle.return_value = {
            "status": "error",
            "code": 404,
            "message": "unknown model",
            "data": None,
        }
        handler = self._make_handler({"model": "x.unknown", "view_type": "form"})
        result = handler.run()

        self.assertFalse(result.get("ok"), result)
        self.assertEqual(result.get("code"), 404)
        self.assertEqual((result.get("meta") or {}).get("legacy_proxy"), "load_contract")

    @patch("addons.smart_core.handlers.load_view.LoadContractHandler.handle")
    def test_load_view_preserves_requested_view_id_in_context_hint(self, proxied_handle):
        proxied_handle.return_value = {
            "status": "success",
            "code": 200,
            "data": {},
            "meta": {},
        }
        handler = self._make_handler({"model": "project.project", "view_type": "form", "view_id": 88})
        handler.run()

        self.assertTrue(proxied_handle.called)
        call_payload = proxied_handle.call_args.kwargs.get("payload") or {}
        params = call_payload.get("params") or {}
        self.assertEqual((params.get("context") or {}).get("requested_view_id"), 88)

    @patch("addons.smart_core.handlers.load_view.LoadContractHandler.handle")
    def test_load_view_rejects_invalid_view_id(self, proxied_handle):
        handler = self._make_handler({"model": "project.project", "view_type": "form", "view_id": "bad"})

        result = handler.run()

        self.assertFalse(result.get("ok"), result)
        self.assertEqual(result.get("code"), 400)
        self.assertEqual((result.get("error") or {}).get("message"), "view_id 无效")
        self.assertFalse(proxied_handle.called)

    @patch("addons.smart_core.handlers.load_view.LoadContractHandler.handle")
    def test_load_view_rejects_zero_view_id(self, proxied_handle):
        handler = self._make_handler({"model": "project.project", "view_type": "form", "view_id": 0})

        result = handler.run()

        self.assertFalse(result.get("ok"), result)
        self.assertEqual(result.get("code"), 400)
        self.assertEqual((result.get("error") or {}).get("message"), "view_id 无效")
        self.assertFalse(proxied_handle.called)


if __name__ == "__main__":
    unittest.main()
