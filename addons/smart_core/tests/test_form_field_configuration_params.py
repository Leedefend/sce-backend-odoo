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

    def test_field_order_set_rejects_invalid_field_order_payload(self):
        handler = self.module.FormFieldOrderSetHandler(
            env={},
            params={"model": "x.model", "field_order": "name,code"},
        )

        result = handler.handle()

        self.assertFalse(result["ok"])
        self.assertEqual(result["code"], 400)
        self.assertEqual(result["error"]["reason_code"], "USER_ERROR")
        self.assertIn("field_order", result["error"]["message"])

    def test_business_config_contract_save_rejects_invalid_contract_json(self):
        handler = self.module.BusinessConfigContractSaveHandler(
            env={},
            params={"name": "demo", "model": "x.model", "contract_json": "invalid"},
        )

        result = handler.handle()

        self.assertFalse(result["ok"])
        self.assertEqual(result["code"], 400)
        self.assertEqual(result["error"]["reason_code"], "USER_ERROR")
        self.assertIn("contract_json", result["error"]["message"])

    def test_business_config_contract_get_requires_name_or_model(self):
        handler = self.module.BusinessConfigContractGetHandler(
            env={},
            params={},
        )

        result = handler.handle()

        self.assertFalse(result["ok"])
        self.assertEqual(result["code"], 400)
        self.assertEqual(result["error"]["reason_code"], "MISSING_PARAMS")

    def test_business_config_contract_publish_requires_name_or_model(self):
        handler = self.module.BusinessConfigContractPublishHandler(
            env={},
            params={},
        )

        result = handler.handle()

        self.assertFalse(result["ok"])
        self.assertEqual(result["code"], 400)
        self.assertEqual(result["error"]["reason_code"], "MISSING_PARAMS")

    def test_business_config_contract_rollback_requires_name_or_model(self):
        handler = self.module.BusinessConfigContractRollbackHandler(
            env={},
            params={},
        )

        result = handler.handle()

        self.assertFalse(result["ok"])
        self.assertEqual(result["code"], 400)
        self.assertEqual(result["error"]["reason_code"], "MISSING_PARAMS")

    def test_low_code_field_rows_mirror_into_business_config_contract(self):
        class Company:
            id = 7

        class Record:
            id = 1
            contract_json = {}

            def write(self, vals):
                self.contract_json = vals["contract_json"]
                self.written = vals

            def action_publish(self):
                self.published = True

        class ContractModel:
            def __init__(self):
                self.record = None
                self.created_vals = None

            def sudo(self):
                return self

            def search(self, domain, limit=None):
                return self.record

            def create(self, vals):
                self.created_vals = vals
                self.record = Record()
                self.record.write(vals)
                return self.record

        class Env(dict):
            company = Company()

        contract_model = ContractModel()
        env = Env({"ui.business.config.contract": contract_model})

        count = self.module._upsert_view_orchestration_field_rows(
            env,
            model="res.partner",
            view_type="form",
            action_id=11,
            view_id=22,
            rows=[
                {"name": "email", "label": "Email Alias", "sequence": 10},
                {"name": "phone", "visible": False, "sequence": 20},
            ],
        )

        self.assertEqual(count, 2)
        payload = contract_model.record.contract_json
        fields = payload["view_orchestration"]["views"]["form"]["fields"]
        self.assertEqual([row["name"] for row in fields], ["email", "phone"])
        self.assertEqual(fields[0]["label"], "Email Alias")
        self.assertFalse(fields[1]["visible"])
        self.assertEqual(contract_model.created_vals["action_id"], 11)
        self.assertEqual(contract_model.created_vals["view_id"], 22)
        self.assertTrue(contract_model.record.published)


if __name__ == "__main__":
    unittest.main()
