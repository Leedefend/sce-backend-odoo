# -*- coding: utf-8 -*-
import unittest
from unittest.mock import patch

from ..core.load_contract_proxy_payload import build_load_contract_proxy_payload
from ..handlers.load_view import LoadModelViewHandler


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
            "data": {"views": {"form": {"layout": []}}},
            "meta": {"etag": "abc"},
        }
        handler = self._make_handler({"model": "project.project", "view_type": "form"})
        result = handler.run()

        self.assertTrue(result.get("ok"), result)
        self.assertEqual(result.get("code"), 200)
        self.assertEqual((result.get("data") or {}).get("views"), {"form": {"layout": []}})
        self.assertEqual((result.get("data") or {}).get("layout"), [])
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
