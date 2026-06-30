# -*- coding: utf-8 -*-
import importlib.util
import json
import sys
import types
import unittest
from datetime import date
from pathlib import Path


SMART_CORE_DIR = Path(__file__).resolve().parents[1]


class _FakeResponse:
    def __init__(self, data=None, status=200):
        self.data = data
        self.status = status
        self.headers = {}


def _load_response_builder():
    http_mod = types.ModuleType("odoo.http")
    http_mod.request = types.SimpleNamespace(
        make_response=lambda data=None, status=200, **kwargs: _FakeResponse(data=data, status=status)
    )
    sys.modules["odoo.http"] = http_mod
    sys.modules["odoo"] = types.SimpleNamespace(http=http_mod)

    module_name = "smart_core_response_builder_under_test"
    sys.modules.pop(module_name, None)
    spec = importlib.util.spec_from_file_location(
        module_name,
        SMART_CORE_DIR / "utils" / "response_builder.py",
    )
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


class TestResponseBuilderBoundaries(unittest.TestCase):
    def setUp(self):
        self.module = _load_response_builder()

    def test_make_response_uses_stable_json_content_type_and_default_serializer(self):
        response = self.module.make_response(data={"day": date(2026, 6, 30)}, headers={"X-Trace-Id": "trace_1"})
        payload = json.loads(response.data)

        self.assertEqual(response.status, 200)
        self.assertEqual(response.headers["Content-Type"], "application/json; charset=utf-8")
        self.assertEqual(response.headers["X-Trace-Id"], "trace_1")
        self.assertEqual(payload["status"], "success")
        self.assertEqual(payload["data"]["day"], "2026-06-30")

    def test_make_response_overwrites_duplicate_headers_instead_of_appending(self):
        response = self.module.make_response(error="Denied", code=403, headers=[("Content-Type", "text/plain")])
        payload = json.loads(response.data)

        self.assertEqual(response.status, 403)
        self.assertEqual(response.headers["Content-Type"], "text/plain")
        self.assertEqual(payload["status"], "error")
        self.assertEqual(payload["message"], "Denied")


if __name__ == "__main__":
    unittest.main()
