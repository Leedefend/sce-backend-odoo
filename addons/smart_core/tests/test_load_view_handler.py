# -*- coding: utf-8 -*-
import unittest
from unittest.mock import patch

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


if __name__ == "__main__":
    unittest.main()

