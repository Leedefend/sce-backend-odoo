# -*- coding: utf-8 -*-
import importlib.util
import sys
import types
import unittest
from pathlib import Path


def _load_base_handler():
    root = Path(__file__).resolve().parents[1]
    base_path = root / "core" / "base_handler.py"
    policy_path = root / "core" / "intent_operation_policy.py"

    odoo_mod = types.ModuleType("odoo")
    api_mod = types.SimpleNamespace(Environment=lambda cr, uid, context: types.SimpleNamespace(cr=cr, uid=uid, context=context))
    odoo_mod.api = api_mod
    odoo_mod.SUPERUSER_ID = 1
    exc_mod = types.ModuleType("odoo.exceptions")
    exc_mod.AccessError = Exception

    addons_mod = types.ModuleType("odoo.addons")
    smart_core_mod = types.ModuleType("odoo.addons.smart_core")
    core_mod = types.ModuleType("odoo.addons.smart_core.core")
    smart_core_mod.__path__ = [str(root)]
    core_mod.__path__ = [str(root / "core")]

    sys.modules.update(
        {
            "odoo": odoo_mod,
            "odoo.exceptions": exc_mod,
            "odoo.addons": addons_mod,
            "odoo.addons.smart_core": smart_core_mod,
            "odoo.addons.smart_core.core": core_mod,
        }
    )

    policy_name = "odoo.addons.smart_core.core.intent_operation_policy"
    sys.modules.pop(policy_name, None)
    policy_spec = importlib.util.spec_from_file_location(policy_name, policy_path)
    policy_module = importlib.util.module_from_spec(policy_spec)
    sys.modules[policy_name] = policy_module
    policy_spec.loader.exec_module(policy_module)

    base_name = "odoo.addons.smart_core.core.base_handler"
    sys.modules.pop(base_name, None)
    base_spec = importlib.util.spec_from_file_location(base_name, base_path)
    base_module = importlib.util.module_from_spec(base_spec)
    sys.modules[base_name] = base_module
    base_spec.loader.exec_module(base_module)
    return base_module


class _FakeEnv:
    cr = object()
    uid = 5
    context = {}

    class _User:
        def has_group(self, xmlid):
            return xmlid == "allowed.group"

    user = _User()


class TestBaseHandlerTypeError(unittest.TestCase):
    def setUp(self):
        self.base = _load_base_handler()

    def test_internal_type_error_is_not_swallowed_by_signature_fallback(self):
        calls = []
        base_cls = self.base.BaseIntentHandler

        class Handler(base_cls):
            INTENT_TYPE = "read.intent"

            def handle(self, payload=None, ctx=None):
                calls.append((payload, ctx))
                raise TypeError("business type error")

        handler = Handler(env=_FakeEnv())

        with self.assertRaises(TypeError) as raised:
            handler.run(payload={"params": {"x": 1}}, ctx={"trace": "t"})

        self.assertEqual(str(raised.exception), "business type error")
        self.assertEqual(len(calls), 1)

    def test_legacy_params_context_signature_still_receives_mapped_arguments(self):
        base_cls = self.base.BaseIntentHandler

        class Handler(base_cls):
            INTENT_TYPE = "read.intent"

            def handle(self, params, context):
                return {"params": params, "context": context}

        handler = Handler(env=_FakeEnv())

        result = handler.run(payload={"params": {"x": 1}}, ctx={"trace": "t"})

        self.assertEqual(result["params"], {"x": 1})
        self.assertEqual(result["context"], {"trace": "t"})

    def test_write_detection_uses_runtime_payload_intent_alias(self):
        base_cls = self.base.BaseIntentHandler

        class Handler(base_cls):
            INTENT_TYPE = "api.data"
            REQUIRED_GROUPS = ["allowed.group"]

            def handle(self):
                return {"ok": True}

        handler = Handler(env=_FakeEnv())
        handler.run(payload={"intent": "api.data.write", "params": {"model": "x.model"}})

        self.assertTrue(handler.is_write())

    def test_required_groups_allow_any_declared_group(self):
        base_cls = self.base.BaseIntentHandler

        class Handler(base_cls):
            INTENT_TYPE = "api.data.write"
            REQUIRED_GROUPS = ["missing.group", "allowed.group"]

            def handle(self):
                return {"ok": True}

        handler = Handler(env=_FakeEnv())

        result = handler.run(payload={"intent": "api.data.write", "params": {"model": "x.model"}})

        self.assertEqual(result, {"ok": True})

    def test_var_keyword_handler_receives_runtime_mapping(self):
        base_cls = self.base.BaseIntentHandler

        class Handler(base_cls):
            INTENT_TYPE = "read.intent"

            def handle(self, **kwargs):
                return kwargs

        handler = Handler(env=_FakeEnv(), request="request-obj")

        result = handler.run(payload={"intent": "read.intent", "params": {"x": 1}}, ctx={"trace": "t"})

        self.assertEqual(result["payload"], {"intent": "read.intent", "params": {"x": 1}})
        self.assertEqual(result["params"], {"x": 1})
        self.assertEqual(result["ctx"], {"trace": "t"})
        self.assertIs(result["env"], handler.env)
        self.assertEqual(result["request"], "request-obj")


if __name__ == "__main__":
    unittest.main()
