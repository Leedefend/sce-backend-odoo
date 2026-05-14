# -*- coding: utf-8 -*-
import importlib.util
import sys
import types
import unittest
from pathlib import Path


class _BaseIntentHandler:
    def __init__(self, env=None, params=None, payload=None, context=None):
        self.env = env or {}
        self.params = params or {}
        self.payload = payload or {}
        self.context = context or {}


def _install_module(name, **attrs):
    module = types.ModuleType(name)
    for key, value in attrs.items():
        setattr(module, key, value)
    sys.modules[name] = module
    return module


def _load_handler():
    root = Path(__file__).resolve().parents[1]
    exc_mod = _install_module("odoo.exceptions", ValidationError=type("ValidationError", (Exception,), {}))
    _install_module("odoo", exceptions=exc_mod)
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

    for module_name in (
        "odoo.addons.smart_core.core.request_params",
        "odoo.addons.smart_core.utils.reason_codes",
        "odoo.addons.smart_core.handlers.form_field_configuration",
    ):
        sys.modules.pop(module_name, None)
    spec = importlib.util.spec_from_file_location(
        "odoo.addons.smart_core.handlers.form_field_configuration",
        root / "handlers" / "form_field_configuration.py",
    )
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


class TestFormFieldConfigurationParams(unittest.TestCase):
    def setUp(self):
        self.module = _load_handler()

    def test_policy_set_rejects_invalid_action_id_without_value_error(self):
        handler = self.module.FormFieldPolicySetHandler(
            env={},
            params={"model": "missing.model", "field_name": "name", "action_id": "abc"},
        )

        result = handler.handle()

        self.assertFalse(result["ok"])
        self.assertEqual(result["code"], 400)
        self.assertEqual(result["error"]["reason_code"], "USER_ERROR")
        self.assertIn("action_id", result["error"]["message"])

    def test_custom_field_create_rejects_invalid_numeric_params(self):
        handler = self.module.FormCustomFieldCreateHandler(
            env={},
            params={"model": "missing.model", "label": "备注", "view_id": "abc"},
        )

        result = handler.handle()

        self.assertFalse(result["ok"])
        self.assertEqual(result["code"], 400)
        self.assertEqual(result["error"]["reason_code"], "USER_ERROR")
        self.assertIn("view_id", result["error"]["message"])


if __name__ == "__main__":
    unittest.main()
