# -*- coding: utf-8 -*-
import importlib.util
import sys
import types
import unittest
from pathlib import Path


class _BaseIntentHandler:
    def __init__(self, env=None, su_env=None, request=None, context=None, payload=None):
        self.env = env
        self.su_env = su_env
        self.request = request
        self.context = context or {}
        self.payload = payload or {}


class _SystemInitHandler:
    def __init__(self, *args, **kwargs):
        pass

    def handle(self, payload=None, ctx=None):
        return {"ok": True, "data": {"system": "ready"}}


def _install_module(name, **attrs):
    module = types.ModuleType(name)
    for key, value in attrs.items():
        setattr(module, key, value)
    sys.modules[name] = module
    return module


def _load_handler():
    root = Path(__file__).resolve().parents[1]
    _install_module("odoo.addons")
    smart_core_mod = _install_module("odoo.addons.smart_core")
    handlers_mod = _install_module("odoo.addons.smart_core.handlers")
    core_mod = _install_module("odoo.addons.smart_core.core")
    governance_mod = _install_module("odoo.addons.smart_core.governance")
    smart_core_mod.__path__ = [str(root)]
    handlers_mod.__path__ = [str(root / "handlers")]
    core_mod.__path__ = [str(root / "core")]
    governance_mod.__path__ = [str(root / "governance")]
    _install_module("odoo.addons.smart_core.core.base_handler", BaseIntentHandler=_BaseIntentHandler)
    _install_module("odoo.addons.smart_core.handlers.system_init", SystemInitHandler=_SystemInitHandler)
    _install_module(
        "odoo.addons.smart_core.governance.scene_drift_engine",
        build_scene_health_payload=lambda init_data, trace_id="", company_id=None: {
            "summary": {"ok": True},
            "details": {"resolve_errors": [{"id": 1}], "drift": [], "debt": []},
            "trace_id": trace_id,
            "company_id": company_id,
        },
    )

    params_name = "odoo.addons.smart_core.core.request_params"
    sys.modules.pop(params_name, None)
    params_spec = importlib.util.spec_from_file_location(params_name, root / "core" / "request_params.py")
    params_module = importlib.util.module_from_spec(params_spec)
    sys.modules[params_name] = params_module
    params_spec.loader.exec_module(params_module)

    module_name = "odoo.addons.smart_core.handlers.scene_health"
    sys.modules.pop(module_name, None)
    spec = importlib.util.spec_from_file_location(module_name, root / "handlers" / "scene_health.py")
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


class TestSceneHealthParams(unittest.TestCase):
    def test_string_false_with_details_removes_details(self):
        module = _load_handler()
        handler = module.SceneHealthHandler(context={"trace_id": "trace"})

        result = handler.handle(payload={"params": {"mode": "full", "with_details": "false"}})

        self.assertTrue(result["ok"])
        self.assertNotIn("details", result["data"])

    def test_string_true_with_details_keeps_details_in_full_mode(self):
        module = _load_handler()
        handler = module.SceneHealthHandler(context={"trace_id": "trace"})

        result = handler.handle(payload={"params": {"mode": "full", "with_details": "true"}})

        self.assertTrue(result["ok"])
        self.assertIn("details", result["data"])

    def test_invalid_company_id_returns_bad_request(self):
        module = _load_handler()
        handler = module.SceneHealthHandler(context={"trace_id": "trace"})

        result = handler.handle(payload={"params": {"company_id": "bad"}})

        self.assertFalse(result["ok"])
        self.assertEqual(result["code"], 400)
        self.assertEqual(result["error"]["message"], "company_id 无效")

    def test_invalid_limit_returns_bad_request(self):
        module = _load_handler()
        handler = module.SceneHealthHandler(context={"trace_id": "trace"})

        result = handler.handle(payload={"params": {"limit": "bad"}})

        self.assertFalse(result["ok"])
        self.assertEqual(result["code"], 400)
        self.assertEqual(result["error"]["message"], "limit 无效")

    def test_negative_offset_returns_bad_request(self):
        module = _load_handler()
        handler = module.SceneHealthHandler(context={"trace_id": "trace"})

        result = handler.handle(payload={"params": {"offset": -1}})

        self.assertFalse(result["ok"])
        self.assertEqual(result["code"], 400)
        self.assertEqual(result["error"]["message"], "offset 无效")


if __name__ == "__main__":
    unittest.main()
