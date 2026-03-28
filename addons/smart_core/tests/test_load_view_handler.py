# -*- coding: utf-8 -*-
import importlib.util
import sys
import types
import unittest
from pathlib import Path
from unittest.mock import patch


SMART_CORE_DIR = Path(__file__).resolve().parents[1]
CORE_DIR = SMART_CORE_DIR / "core"
HANDLERS_DIR = SMART_CORE_DIR / "handlers"


def _load_module(module_name: str, path: Path):
    spec = importlib.util.spec_from_file_location(module_name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


addons_pkg = sys.modules.setdefault("addons", types.ModuleType("addons"))
addons_pkg.__path__ = [str(SMART_CORE_DIR.parents[1])]
smart_core_pkg = sys.modules.setdefault("addons.smart_core", types.ModuleType("addons.smart_core"))
smart_core_pkg.__path__ = [str(SMART_CORE_DIR)]
core_pkg = sys.modules.setdefault("addons.smart_core.core", types.ModuleType("addons.smart_core.core"))
core_pkg.__path__ = [str(CORE_DIR)]
handlers_pkg = sys.modules.setdefault("addons.smart_core.handlers", types.ModuleType("addons.smart_core.handlers"))
handlers_pkg.__path__ = [str(HANDLERS_DIR)]
addons_pkg.smart_core = smart_core_pkg
smart_core_pkg.core = core_pkg
smart_core_pkg.handlers = handlers_pkg


base_handler_module = types.ModuleType("addons.smart_core.core.base_handler")


class BaseIntentHandler:
    def __init__(self, env, su_env=None, request=None, context=None, payload=None):
        self.env = env
        self.su_env = su_env or env
        self.request = request
        self.context = dict(context or {})
        self.payload = payload or {}
        if isinstance(self.payload, dict) and "params" in self.payload:
            self.params = self.payload.get("params") or {}
        else:
            self.params = self.payload or {}

    def run(self, payload=None, ctx=None):
        if payload is not None:
            self.payload = payload
            if isinstance(payload, dict) and "params" in payload:
                self.params = payload.get("params") or {}
            else:
                self.params = payload or {}
        return self.handle(payload=payload, ctx=ctx)


base_handler_module.BaseIntentHandler = BaseIntentHandler
sys.modules["addons.smart_core.core.base_handler"] = base_handler_module


load_contract_proxy_payload_module = _load_module(
    "addons.smart_core.core.load_contract_proxy_payload",
    CORE_DIR / "load_contract_proxy_payload.py",
)


load_contract_module = types.ModuleType("addons.smart_core.handlers.load_contract")


class LoadContractHandler:
    def __init__(self, env=None, su_env=None, context=None, payload=None):
        self.env = env
        self.su_env = su_env
        self.context = context
        self.payload = payload

    def handle(self, payload=None, ctx=None):
        return {"status": "success", "code": 200, "data": {}, "meta": {}}


load_contract_module.LoadContractHandler = LoadContractHandler
sys.modules["addons.smart_core.handlers.load_contract"] = load_contract_module


load_view_module = _load_module(
    "addons.smart_core.handlers.load_view",
    HANDLERS_DIR / "load_view.py",
)
handlers_pkg.load_view = load_view_module

build_load_contract_proxy_payload = load_contract_proxy_payload_module.build_load_contract_proxy_payload
LoadModelViewHandler = load_view_module.LoadModelViewHandler


class _DummyEnv:
    pass


class TestLoadViewHandler(unittest.TestCase):
    def _make_handler(self, params):
        return LoadModelViewHandler(env=_DummyEnv(), su_env=_DummyEnv(), context={}, payload={"params": params})

    @patch("addons.smart_core.handlers.load_view.LoadContractHandler.handle")
    def test_load_view_proxies_to_load_contract_success(self, proxied_handle):
        proxied_handle.return_value = {
            "status": "success",
            "code": 200,
            "data": {
                "views": {
                    "form": {
                        "layout": [],
                        "parser_contract": {"view_type": "form", "layout": {"kind": "form"}},
                        "view_semantics": {"source_view": "form", "capability_flags": {"has_title": True}},
                    }
                },
                "native_view": {"views": {"form": {"layout": []}}},
            },
            "meta": {"etag": "abc"},
        }
        handler = self._make_handler({"model": "project.project", "view_type": "form"})
        result = handler.run()

        self.assertTrue(result.get("ok"), result)
        self.assertEqual(result.get("code"), 200)
        self.assertEqual(
            (result.get("data") or {}).get("views"),
            {
                "form": {
                    "layout": [],
                    "parser_contract": {"view_type": "form", "layout": {"kind": "form"}},
                    "view_semantics": {"source_view": "form", "capability_flags": {"has_title": True}},
                }
            },
        )
        self.assertEqual((result.get("data") or {}).get("layout"), [])
        self.assertEqual(((result.get("data") or {}).get("parser_contract") or {}).get("view_type"), "form")
        self.assertEqual(
            (((result.get("data") or {}).get("view_semantics") or {}).get("capability_flags") or {}).get("has_title"),
            True,
        )
        self.assertIn("native_view", (result.get("data") or {}))
        self.assertEqual((result.get("meta") or {}).get("legacy_proxy"), "load_contract")
        self.assertEqual((result.get("meta") or {}).get("canonical_intent"), "load_contract")

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

    def test_proxy_payload_builder_preserves_existing_context(self):
        payload = build_load_contract_proxy_payload(
            {
                "model": "project.project",
                "view_id": 88,
                "context": {"lang": "zh_CN", "from_frontend": True},
            }
        )

        params = payload.get("params") or {}
        self.assertEqual(params.get("model"), "project.project")
        self.assertEqual((params.get("context") or {}).get("requested_view_id"), 88)
        self.assertEqual((params.get("context") or {}).get("lang"), "zh_CN")
        self.assertTrue((params.get("context") or {}).get("from_frontend"))


if __name__ == "__main__":
    unittest.main()
