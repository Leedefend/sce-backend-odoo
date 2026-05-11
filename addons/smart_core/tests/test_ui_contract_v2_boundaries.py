# -*- coding: utf-8 -*-
import importlib.util
import sys
import types
import unittest
from pathlib import Path


class _BaseIntentHandler:
    def __init__(self, env=None, su_env=None, request=None, params=None, context=None, payload=None):
        self.env = env
        self.su_env = su_env
        self.request = request
        self.params = params or {}
        self.context = context or {}
        self.payload = payload or {}


def _install_module(name, **attrs):
    module = types.ModuleType(name)
    for key, value in attrs.items():
        setattr(module, key, value)
    sys.modules[name] = module
    return module


def _load_handler():
    root = Path(__file__).resolve().parents[1]
    _install_module("odoo")
    _install_module("odoo.addons")
    smart_core_mod = _install_module("odoo.addons.smart_core")
    handlers_mod = _install_module("odoo.addons.smart_core.handlers")
    core_mod = _install_module("odoo.addons.smart_core.core")
    smart_core_mod.__path__ = [str(root)]
    handlers_mod.__path__ = [str(root / "handlers")]
    core_mod.__path__ = [str(root / "core")]

    _install_module("odoo.addons.smart_core.core.base_handler", BaseIntentHandler=_BaseIntentHandler)
    _install_module(
        "odoo.addons.smart_core.core.scene_provider",
        load_scenes_from_db_or_fallback=lambda *args, **kwargs: {
            "scenes": [{"key": "workspace.home", "title": "Home"}]
        },
    )
    _install_module(
        "odoo.addons.smart_core.core.unified_page_contract_v2_assembler",
        CONTRACT_VERSION="2.0",
        assemble_unified_page_contract_v2=lambda *args, **kwargs: {"pageInfo": {}, "meta": {}},
    )
    captured = {}

    def _trim_unified_page_contract_v2(contract, **kwargs):
        captured["trim_kwargs"] = kwargs
        return {"contract": contract, "trim_kwargs": kwargs}

    _install_module(
        "odoo.addons.smart_core.core.unified_page_contract_v2_client",
        MOBILE_CLIENT_TYPES={"wx_mini", "harmony_h5"},
        resolve_client_type=lambda headers, params: "wx_mini",
        resolve_delivery_profile=lambda client_type, params=None: "mobile_compact",
        trim_unified_page_contract_v2=_trim_unified_page_contract_v2,
    )

    for module_name, rel_path in (
        ("odoo.addons.smart_core.core.intent_execution_result", "core/intent_execution_result.py"),
        ("odoo.addons.smart_core.core.request_params", "core/request_params.py"),
    ):
        sys.modules.pop(module_name, None)
        spec = importlib.util.spec_from_file_location(module_name, root / rel_path)
        module = importlib.util.module_from_spec(spec)
        sys.modules[module_name] = module
        spec.loader.exec_module(module)

    class _UiContractHandler(_BaseIntentHandler):
        def handle(self, payload=None, ctx=None):
            return {"ok": True, "data": {"model": "res.partner", "view_type": "form"}, "meta": {}}

    _install_module("odoo.addons.smart_core.handlers.ui_contract", UiContractHandler=_UiContractHandler)

    module_name = "odoo.addons.smart_core.handlers.ui_contract_v2"
    sys.modules.pop(module_name, None)
    spec = importlib.util.spec_from_file_location(module_name, root / "handlers" / "ui_contract_v2.py")
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    module._captured = captured
    return module


class TestUiContractV2Boundaries(unittest.TestCase):
    def setUp(self):
        self.module = _load_handler()

    def test_rejects_invalid_max_widgets(self):
        handler = self.module.UiContractV2Handler(env=object())

        result = handler.handle(payload={"params": {"model": "res.partner", "max_widgets": "bad"}})

        self.assertFalse(result.ok)
        self.assertEqual(result.code, 400)
        self.assertEqual(result.error["message"], "max_widgets 无效")

    def test_rejects_zero_max_actions(self):
        handler = self.module.UiContractV2Handler(env=object())

        result = handler.handle(payload={"params": {"model": "res.partner", "maxActions": 0}})

        self.assertFalse(result.ok)
        self.assertEqual(result.code, 400)
        self.assertEqual(result.error["message"], "max_actions 无效")

    def test_passes_parsed_trim_limits(self):
        handler = self.module.UiContractV2Handler(env=object())

        result = handler.handle(
            payload={
                "params": {
                    "model": "res.partner",
                    "maxWidgets": "8",
                    "max_actions": "3",
                    "maxContainers": "2",
                }
            }
        )

        self.assertTrue(result.ok)
        trim_kwargs = self.module._captured["trim_kwargs"]
        self.assertEqual(trim_kwargs["max_widgets"], 8)
        self.assertEqual(trim_kwargs["max_actions"], 3)
        self.assertEqual(trim_kwargs["max_containers"], 2)
        self.assertFalse(trim_kwargs["include_source_compat"])

    def test_allows_explicit_source_compat_opt_in(self):
        handler = self.module.UiContractV2Handler(env=object())

        result = handler.handle(
            payload={
                "params": {
                    "model": "res.partner",
                    "include_source_compat": True,
                }
            }
        )

        self.assertTrue(result.ok)
        trim_kwargs = self.module._captured["trim_kwargs"]
        self.assertTrue(trim_kwargs["include_source_compat"])

    def test_scene_contract_rejects_invalid_trim_limit(self):
        handler = self.module.UiContractV2Handler(env=object())

        result = handler.handle(
            payload={
                "params": {
                    "source_type": "scene_contract_v1",
                    "scene_key": "workspace.home",
                    "max_containers": "bad",
                }
            }
        )

        self.assertFalse(result.ok)
        self.assertEqual(result.code, 400)
        self.assertEqual(result.error["message"], "max_containers 无效")


if __name__ == "__main__":
    unittest.main()
