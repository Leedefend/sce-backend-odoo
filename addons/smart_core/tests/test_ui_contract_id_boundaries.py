# -*- coding: utf-8 -*-
import importlib.util
import sys
import types
import unittest
from pathlib import Path


class _BaseIntentHandler:
    def __init__(self, env=None, request=None, context=None, payload=None):
        self.env = env
        self.request = request
        self.context = context or {}
        self.payload = payload or {}
        self.params = self.payload.get("params") if isinstance(self.payload, dict) else {}
        if not isinstance(self.params, dict):
            self.params = {}


def _install_module(name, **attrs):
    module = types.ModuleType(name)
    for key, value in attrs.items():
        setattr(module, key, value)
    sys.modules[name] = module
    return module


def _load_handler():
    root = Path(__file__).resolve().parents[1]

    api_mod = types.SimpleNamespace(Environment=lambda cr, uid, ctx: None)
    _install_module("odoo", api=api_mod, SUPERUSER_ID=1)
    _install_module("odoo.tools")
    _install_module("odoo.tools.safe_eval", safe_eval=lambda value: value)

    addons_mod = _install_module("odoo.addons")
    smart_core_mod = _install_module("odoo.addons.smart_core")
    handlers_mod = _install_module("odoo.addons.smart_core.handlers")
    core_mod = _install_module("odoo.addons.smart_core.core")
    app_config_mod = _install_module("odoo.addons.smart_core.app_config_engine")
    services_mod = _install_module("odoo.addons.smart_core.app_config_engine.services")
    dispatchers_mod = _install_module("odoo.addons.smart_core.app_config_engine.services.dispatchers")
    utils_mod = _install_module("odoo.addons.smart_core.utils")

    addons_mod.__path__ = []
    smart_core_mod.__path__ = [str(root)]
    handlers_mod.__path__ = [str(root / "handlers")]
    core_mod.__path__ = [str(root / "core")]
    app_config_mod.__path__ = [str(root / "app_config_engine")]
    services_mod.__path__ = [str(root / "app_config_engine" / "services")]
    dispatchers_mod.__path__ = [str(root / "app_config_engine" / "services" / "dispatchers")]
    utils_mod.__path__ = [str(root / "utils")]

    base_mod = _install_module("odoo.addons.smart_core.core.base_handler")
    base_mod.BaseIntentHandler = _BaseIntentHandler

    result_mod = _install_module("odoo.addons.smart_core.core.intent_execution_result")
    result_mod.IntentExecutionResult = type("IntentExecutionResult", (), {})

    projection_mod = _install_module("odoo.addons.smart_core.core.native_view_contract_projection")
    projection_mod.inject_primary_view_projection = lambda data, requested_view_type=None: data

    contract_service_mod = _install_module(
        "odoo.addons.smart_core.app_config_engine.services.contract_service"
    )
    contract_service_mod.ContractService = type("ContractService", (), {})
    nav_mod = _install_module(
        "odoo.addons.smart_core.app_config_engine.services.dispatchers.nav_dispatcher"
    )
    nav_mod.NavDispatcher = type("NavDispatcher", (), {})
    menu_mod = _install_module(
        "odoo.addons.smart_core.app_config_engine.services.dispatchers.menu_dispatcher"
    )
    menu_mod.MenuDispatcher = type("MenuDispatcher", (), {})
    action_mod = _install_module(
        "odoo.addons.smart_core.app_config_engine.services.dispatchers.action_dispatcher"
    )
    action_mod.ActionDispatcher = type("ActionDispatcher", (), {})

    governance_mod = _install_module("odoo.addons.smart_core.utils.contract_governance")
    governance_mod.apply_contract_governance = lambda data, mode, inject_contract_mode=False: data
    governance_mod.resolve_contract_mode = lambda params: "user"
    governance_mod.resolve_contract_surface = lambda params, contract_mode=None: "scene"

    request_params_name = "odoo.addons.smart_core.core.request_params"
    sys.modules.pop(request_params_name, None)
    request_params_spec = importlib.util.spec_from_file_location(
        request_params_name, root / "core" / "request_params.py"
    )
    request_params_module = importlib.util.module_from_spec(request_params_spec)
    sys.modules[request_params_name] = request_params_module
    request_params_spec.loader.exec_module(request_params_module)

    module_name = "odoo.addons.smart_core.handlers.ui_contract"
    sys.modules.pop(module_name, None)
    spec = importlib.util.spec_from_file_location(module_name, root / "handlers" / "ui_contract.py")
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


class TestUiContractIdBoundaries(unittest.TestCase):
    def setUp(self):
        module = _load_handler()
        env = types.SimpleNamespace(context={}, user=types.SimpleNamespace(lang=""))
        self.handler = module.UiContractHandler(env=env, context={})

    def test_action_open_rejects_invalid_action_id(self):
        result = self.handler._op_action_open({"action_id": "bad"}, {})

        self.assertFalse(result["ok"])
        self.assertEqual(result["error"]["code"], 400)
        self.assertIn("action_id", result["error"]["message"])

    def test_action_open_rejects_invalid_record_id(self):
        result = self.handler._op_action_open({"action_id": "7", "record_id": "bad"}, {})

        self.assertFalse(result["ok"])
        self.assertEqual(result["error"]["code"], 400)
        self.assertIn("record_id", result["error"]["message"])

    def test_model_rejects_invalid_optional_ids(self):
        self.handler.env = {"x.model": object()}

        for field in ("action_id", "menu_id", "record_id"):
            with self.subTest(field=field):
                result = self.handler._op_model({"model": "x.model", field: "bad"}, {})
                self.assertFalse(result["ok"])
                self.assertEqual(result["error"]["code"], 400)
                self.assertIn(field, result["error"]["message"])

    def test_handle_rejects_invalid_company_id(self):
        result = self.handler.handle({"params": {"op": "model", "model": "x.model", "company_id": "bad"}})

        self.assertFalse(result["ok"])
        self.assertEqual(result["error"]["code"], 400)
        self.assertEqual(result["error"]["message"], "company_id 无效")


if __name__ == "__main__":
    unittest.main()
