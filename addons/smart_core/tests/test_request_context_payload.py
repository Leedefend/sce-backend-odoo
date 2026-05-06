# -*- coding: utf-8 -*-
import importlib.util
import sys
import types
import unittest
from pathlib import Path


class _FakeUser:
    id = 42


class _FakeEnv:
    def __init__(self):
        self.uid = None

    def __call__(self, user=None):
        self.uid = getattr(user, "id", user)
        return self


class _FakeHttpRequest:
    headers = {"X-Trace-Id": "trace-1"}

    def get_json(self, force=False, silent=False):
        return {"intent": "raw.intent", "params": {"model": "raw.model"}}


class _FakeRequest:
    def __init__(self):
        self.env = _FakeEnv()
        self.httprequest = _FakeHttpRequest()
        self.params = {}


def _load_context(fake_request, auth_calls, user_provider=None):
    root = Path(__file__).resolve().parents[1]
    module_path = root / "core" / "context.py"

    odoo_mod = types.ModuleType("odoo")
    http_mod = types.ModuleType("odoo.http")
    http_mod.request = fake_request
    exc_mod = types.ModuleType("odoo.exceptions")
    exc_mod.AccessDenied = Exception

    addons_mod = types.ModuleType("odoo.addons")
    smart_core_mod = types.ModuleType("odoo.addons.smart_core")
    core_mod = types.ModuleType("odoo.addons.smart_core.core")
    security_mod = types.ModuleType("odoo.addons.smart_core.security")
    auth_mod = types.ModuleType("odoo.addons.smart_core.security.auth")
    trace_mod = types.ModuleType("odoo.addons.smart_core.core.trace")

    def _get_user_from_token():
        auth_calls.append("called")
        if user_provider:
            return user_provider()
        return _FakeUser()

    auth_mod.get_user_from_token = _get_user_from_token
    trace_mod.get_trace_id = lambda headers: headers.get("X-Trace-Id")

    smart_core_mod.__path__ = [str(root)]
    core_mod.__path__ = [str(root / "core")]
    security_mod.__path__ = [str(root / "security")]
    addons_mod.__path__ = [str(root.parents[1])]

    sys.modules.update(
        {
            "odoo": odoo_mod,
            "odoo.http": http_mod,
            "odoo.exceptions": exc_mod,
            "odoo.addons": addons_mod,
            "odoo.addons.smart_core": smart_core_mod,
            "odoo.addons.smart_core.core": core_mod,
            "odoo.addons.smart_core.security": security_mod,
            "odoo.addons.smart_core.security.auth": auth_mod,
            "odoo.addons.smart_core.core.trace": trace_mod,
        }
    )

    name = "odoo.addons.smart_core.core.context"
    sys.modules.pop(name, None)
    spec = importlib.util.spec_from_file_location(name, module_path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


class TestRequestContextPayload(unittest.TestCase):
    def test_from_payload_uses_canonical_payload_instead_of_raw_body(self):
        auth_calls = []
        fake_request = _FakeRequest()
        context_mod = _load_context(fake_request, auth_calls)
        payload = {"intent": "api.data.write", "params": {"model": "x.model", "id": 7, "db": "effective"}}

        ctx = context_mod.RequestContext.from_payload(payload)

        self.assertIs(ctx.params, payload)
        self.assertEqual(ctx.params["intent"], "api.data.write")
        self.assertEqual(ctx.params["params"]["db"], "effective")
        self.assertEqual(ctx.uid, 42)
        self.assertEqual(fake_request.env.uid, 42)
        self.assertEqual(auth_calls, ["called"])
        self.assertEqual(ctx.trace_id, "trace-1")

    def test_from_payload_does_not_authenticate_public_bootstrap(self):
        auth_calls = []
        fake_request = _FakeRequest()
        context_mod = _load_context(fake_request, auth_calls)

        ctx = context_mod.RequestContext.from_payload({"intent": "session.bootstrap", "params": {}})

        self.assertIsNone(ctx.user)
        self.assertIsNone(ctx.uid)
        self.assertEqual(auth_calls, [])

    def test_from_payload_does_not_authenticate_permission_check(self):
        auth_calls = []
        fake_request = _FakeRequest()
        context_mod = _load_context(fake_request, auth_calls)

        ctx = context_mod.RequestContext.from_payload({"intent": "permission.check", "params": {"capability_key": "x"}})

        self.assertIsNone(ctx.user)
        self.assertIsNone(ctx.uid)
        self.assertEqual(auth_calls, [])

    def test_from_http_request_delegates_to_payload_constructor(self):
        auth_calls = []
        fake_request = _FakeRequest()
        context_mod = _load_context(fake_request, auth_calls)

        ctx = context_mod.RequestContext.from_http_request()

        self.assertEqual(ctx.params["intent"], "raw.intent")
        self.assertEqual(ctx.uid, 42)

    def test_from_payload_rejects_missing_user_identity(self):
        auth_calls = []
        fake_request = _FakeRequest()
        context_mod = _load_context(fake_request, auth_calls, user_provider=lambda: None)

        with self.assertRaises(Exception):
            context_mod.RequestContext.from_payload({"intent": "api.data", "params": {"model": "x.model"}})

        self.assertEqual(auth_calls, ["called"])


if __name__ == "__main__":
    unittest.main()
