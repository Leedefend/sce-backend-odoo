# -*- coding: utf-8 -*-
import importlib.util
import sys
import types
import unittest
from pathlib import Path


class _FakeCursor:
    dbname = "test_db"


class _FakeEnv:
    def __init__(self):
        self.cr = _FakeCursor()
        self.context = {}
        self.uid = 7
        self.registry = object()

    def __call__(self, context=None, user=None):
        del user
        env = _FakeEnv()
        env.context = context or {}
        return env


class _FakeRequest:
    def __init__(self):
        self.env = _FakeEnv()
        self.uid = 7


class _TrackingCursor:
    dbname = "other_db"

    def __init__(self):
        self.commits = 0
        self.rollbacks = 0
        self.closed = 0

    def commit(self):
        self.commits += 1

    def rollback(self):
        self.rollbacks += 1

    def close(self):
        self.closed += 1


def _load_router(fake_request, handler_cls):
    root = Path(__file__).resolve().parents[1]
    module_path = root / "core" / "intent_router.py"

    odoo_mod = types.ModuleType("odoo")
    odoo_mod.SUPERUSER_ID = 1
    odoo_mod.registry = lambda db: None
    api_mod = types.SimpleNamespace(Environment=lambda cr, uid, context: types.SimpleNamespace(cr=cr, uid=uid, context=context))
    odoo_mod.api = api_mod

    http_mod = types.ModuleType("odoo.http")
    http_mod.request = fake_request

    addons_mod = types.ModuleType("odoo.addons")
    smart_core_mod = types.ModuleType("odoo.addons.smart_core")
    core_mod = types.ModuleType("odoo.addons.smart_core.core")
    smart_core_mod.__path__ = [str(root)]
    core_mod.__path__ = [str(root / "core")]

    base_handler_mod = types.ModuleType("odoo.addons.smart_core.core.base_handler")
    base_handler_mod.BaseIntentHandler = object
    registry_mod = types.ModuleType("odoo.addons.smart_core.core.handler_registry")
    registry_mod.HANDLER_REGISTRY = {"demo.intent": handler_cls}
    extension_loader_mod = types.ModuleType("odoo.addons.smart_core.core.extension_loader")
    extension_loader_mod.load_extensions = lambda env, registry: None

    sys.modules.update(
        {
            "odoo": odoo_mod,
            "odoo.http": http_mod,
            "odoo.addons": addons_mod,
            "odoo.addons.smart_core": smart_core_mod,
            "odoo.addons.smart_core.core": core_mod,
            "odoo.addons.smart_core.core.base_handler": base_handler_mod,
            "odoo.addons.smart_core.core.handler_registry": registry_mod,
            "odoo.addons.smart_core.core.extension_loader": extension_loader_mod,
        }
    )

    identity_name = "odoo.addons.smart_core.core.request_identity"
    sys.modules.pop(identity_name, None)
    identity_spec = importlib.util.spec_from_file_location(identity_name, root / "core" / "request_identity.py")
    identity_mod = importlib.util.module_from_spec(identity_spec)
    sys.modules[identity_name] = identity_mod
    identity_spec.loader.exec_module(identity_mod)

    name = "odoo.addons.smart_core.core.intent_router"
    sys.modules.pop(name, None)
    spec = importlib.util.spec_from_file_location(name, module_path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


class TestIntentRouterPayloadEnvelope(unittest.TestCase):
    def test_dispatch_keeps_handler_payload_as_canonical_envelope(self):
        seen = {}

        class Handler:
            def __init__(self, **kwargs):
                seen["init_payload"] = kwargs.get("payload")
                self.registry = None
                self.cr = None
                self.uid = None

            def run(self, payload=None, ctx=None):
                seen["run_payload"] = payload
                seen["ctx"] = ctx
                return {"ok": True}

        router = _load_router(_FakeRequest(), Handler)

        result = router._dispatch("demo.intent", {"x": 1}, {"trace": "t"})

        expected = {"intent": "demo.intent", "params": {"x": 1}, "context": {"trace": "t"}}
        self.assertEqual(result, {"ok": True})
        self.assertEqual(seen["init_payload"], expected)
        self.assertEqual(seen["run_payload"], expected)
        self.assertEqual(seen["ctx"], {"trace": "t"})

    def test_extra_cursor_rolls_back_when_handler_returns_error_result(self):
        class Handler:
            def __init__(self, **kwargs):
                self.registry = None
                self.cr = None
                self.uid = None

            def run(self, payload=None, ctx=None):
                del payload, ctx
                return {"ok": False, "code": 400, "error": {"message": "bad"}}

        router = _load_router(_FakeRequest(), Handler)
        tracking_cr = _TrackingCursor()
        env = _FakeEnv()
        env.cr = tracking_cr
        env.registry = object()
        router._build_envs = lambda params, context: (env, object(), tracking_cr)

        result = router._dispatch("demo.intent", {"x": 1}, {})

        self.assertFalse(result["ok"])
        self.assertEqual(tracking_cr.commits, 0)
        self.assertEqual(tracking_cr.rollbacks, 1)
        self.assertEqual(tracking_cr.closed, 1)

    def test_extra_cursor_rolls_back_when_handler_returns_string_false_ok(self):
        class Handler:
            def __init__(self, **kwargs):
                self.registry = None
                self.cr = None
                self.uid = None

            def run(self, payload=None, ctx=None):
                del payload, ctx
                return {"ok": "false", "code": 400, "error": {"message": "bad"}}

        router = _load_router(_FakeRequest(), Handler)
        tracking_cr = _TrackingCursor()
        env = _FakeEnv()
        env.cr = tracking_cr
        env.registry = object()
        router._build_envs = lambda params, context: (env, object(), tracking_cr)

        result = router._dispatch("demo.intent", {"x": 1}, {})

        self.assertEqual(result["ok"], "false")
        self.assertEqual(tracking_cr.commits, 0)
        self.assertEqual(tracking_cr.rollbacks, 1)
        self.assertEqual(tracking_cr.closed, 1)

    def test_extra_cursor_rolls_back_when_handler_raises(self):
        class Handler:
            def __init__(self, **kwargs):
                self.registry = None
                self.cr = None
                self.uid = None

            def run(self, payload=None, ctx=None):
                del payload, ctx
                raise RuntimeError("boom")

        router = _load_router(_FakeRequest(), Handler)
        tracking_cr = _TrackingCursor()
        env = _FakeEnv()
        env.cr = tracking_cr
        env.registry = object()
        router._build_envs = lambda params, context: (env, object(), tracking_cr)

        with self.assertRaises(RuntimeError):
            router._dispatch("demo.intent", {"x": 1}, {})

        self.assertEqual(tracking_cr.commits, 0)
        self.assertEqual(tracking_cr.rollbacks, 1)
        self.assertEqual(tracking_cr.closed, 1)

    def test_extra_cursor_commits_when_handler_returns_success_result(self):
        class Handler:
            def __init__(self, **kwargs):
                self.registry = None
                self.cr = None
                self.uid = None

            def run(self, payload=None, ctx=None):
                del payload, ctx
                return {"ok": True}

        router = _load_router(_FakeRequest(), Handler)
        tracking_cr = _TrackingCursor()
        env = _FakeEnv()
        env.cr = tracking_cr
        env.registry = object()
        router._build_envs = lambda params, context: (env, object(), tracking_cr)

        result = router._dispatch("demo.intent", {"x": 1}, {})

        self.assertTrue(result["ok"])
        self.assertEqual(tracking_cr.commits, 1)
        self.assertEqual(tracking_cr.rollbacks, 0)
        self.assertEqual(tracking_cr.closed, 1)


if __name__ == "__main__":
    unittest.main()
