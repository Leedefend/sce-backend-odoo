# -*- coding: utf-8 -*-
import importlib.util
import sys
import types
import unittest
from pathlib import Path


class _BaseIntentHandler:
    def __init__(self, env=None, context=None):
        self.env = env
        self.context = context or {}


class _Service:
    calls = []

    def __init__(self, env, user):
        self.env = env
        self.user = user

    def set_company_channel(self, company_id, channel, reason, trace_id=""):
        self.calls.append((company_id, channel, reason, trace_id))
        return {"company_id": company_id, "channel": channel}

    def export_contract(self, channel, reason, trace_id=""):
        self.calls.append(("export", channel, reason, trace_id))
        return {"channel": channel}


class _Env:
    user = types.SimpleNamespace(company_id=types.SimpleNamespace(id=9))


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
    utils_mod = _install_module("odoo.addons.smart_core.utils")
    smart_core_mod.__path__ = [str(root)]
    handlers_mod.__path__ = [str(root / "handlers")]
    core_mod.__path__ = [str(root / "core")]
    utils_mod.__path__ = [str(root / "utils")]
    _install_module("odoo.addons.smart_core.core.base_handler", BaseIntentHandler=_BaseIntentHandler)
    _install_module(
        "odoo.addons.smart_core.utils.extension_hooks",
        call_extension_hook_first=lambda env, hook, *args, **kwargs: _Service,
    )

    module_name = "odoo.addons.smart_core.handlers.scene_governance"
    sys.modules.pop(module_name, None)
    spec = importlib.util.spec_from_file_location(module_name, root / "handlers" / "scene_governance.py")
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


class TestSceneGovernanceBoundaries(unittest.TestCase):
    def setUp(self):
        _Service.calls = []
        self.module = _load_handler()

    def test_invalid_company_id_returns_bad_request(self):
        handler = self.module.SceneGovernanceSetChannelHandler(env=_Env(), context={"trace_id": "trace"})

        result = handler.handle(payload={"params": {"reason": "promote", "channel": "stable", "company_id": "bad"}})

        self.assertFalse(result["ok"])
        self.assertEqual(result["code"], 400)
        self.assertEqual(result["error"]["message"], "company_id 无效")
        self.assertEqual(_Service.calls, [])

    def test_missing_company_id_uses_current_company(self):
        handler = self.module.SceneGovernanceSetChannelHandler(env=_Env(), context={"trace_id": "trace"})

        result = handler.handle(payload={"params": {"reason": "promote", "channel": "stable"}})

        self.assertTrue(result["ok"])
        self.assertEqual(_Service.calls, [(9, "stable", "promote", "trace")])

    def test_invalid_channel_returns_bad_request(self):
        handler = self.module.SceneGovernanceSetChannelHandler(env=_Env(), context={"trace_id": "trace"})

        result = handler.handle(payload={"params": {"reason": "promote", "channel": "nightly"}})

        self.assertFalse(result["ok"])
        self.assertEqual(result["code"], 400)
        self.assertEqual(result["error"]["message"], "channel 无效")
        self.assertEqual(_Service.calls, [])

    def test_non_text_channel_returns_bad_request(self):
        handler = self.module.SceneGovernanceSetChannelHandler(env=_Env(), context={"trace_id": "trace"})

        result = handler.handle(payload={"params": {"reason": "promote", "channel": ["stable"]}})

        self.assertFalse(result["ok"])
        self.assertEqual(result["code"], 400)
        self.assertEqual(result["error"]["message"], "channel 无效")
        self.assertEqual(_Service.calls, [])

    def test_missing_reason_returns_bad_request(self):
        handler = self.module.SceneGovernanceRollbackHandler(env=_Env(), context={"trace_id": "trace"})

        result = handler.handle(payload={"params": {}})

        self.assertFalse(result["ok"])
        self.assertEqual(result["code"], 400)
        self.assertEqual(result["error"]["message"], "reason 无效")
        self.assertEqual(_Service.calls, [])

    def test_export_contract_defaults_channel_to_stable(self):
        handler = self.module.SceneGovernanceExportContractHandler(env=_Env(), context={"trace_id": "trace"})

        result = handler.handle(payload={"params": {"reason": "snapshot"}})

        self.assertTrue(result["ok"])
        self.assertEqual(_Service.calls, [("export", "stable", "snapshot", "trace")])


if __name__ == "__main__":
    unittest.main()
