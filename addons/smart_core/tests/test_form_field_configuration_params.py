# -*- coding: utf-8 -*-
import importlib.util
import sys
import types
import unittest
from pathlib import Path


class _BaseIntentHandler:
    def __init__(self, env=None, params=None, payload=None, context=None):
        self.env = env or {}
        self.payload = payload or {}
        self.params = params or (self.payload.get("params") if isinstance(self.payload, dict) else {}) or {}
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

    def test_optional_scope_ids_accept_false_as_empty_scope(self):
        value, invalid_field = self.module._optional_non_negative_int({"view_id": False}, "view_id", "viewId")

        self.assertEqual(value, 0)
        self.assertIsNone(invalid_field)

    def test_optional_scope_ids_still_reject_true(self):
        value, invalid_field = self.module._optional_non_negative_int({"view_id": True}, "view_id", "viewId")

        self.assertIsNone(value)
        self.assertEqual(invalid_field, "view_id")

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

    def test_custom_field_create_dry_run_prechecks_without_writing(self):
        class Company:
            id = 7

        class PartnerModel:
            _fields = {"name": object()}

        class ModelRecord:
            id = 9
            transient = False

        class ModelRegistry:
            def search(self, domain, limit=None):
                self.domain = domain
                return ModelRecord()

        class FieldRegistry:
            def __init__(self):
                self.search_count_calls = []

            def sudo(self):
                return self

            def search_count(self, domain):
                self.search_count_calls.append(domain)
                return 0

        class WizardRegistry:
            def __init__(self):
                self.created = []

            def check_access_rights(self, mode):
                self.checked = mode

            def create(self, vals):
                self.created.append(vals)
                raise AssertionError("dry_run must not create wizard")

        class Env(dict):
            company = Company()

        fields = FieldRegistry()
        wizard = WizardRegistry()
        env = Env({
            "res.partner": PartnerModel(),
            "ir.model": ModelRegistry(),
            "ir.model.fields": fields,
            "ui.form.custom.field.wizard": wizard,
        })
        handler = self.module.FormCustomFieldCreateHandler(
            env=env,
            params={
                "model": "res.partner",
                "label": "内部备注",
                "field_name": "x_internal_note",
                "ttype": "text",
                "group_title": "基础信息",
                "action_id": 11,
                "dry_run": True,
            },
        )

        result = handler.handle()

        self.assertTrue(result["ok"])
        self.assertTrue(result["data"]["dry_run"])
        self.assertTrue(result["data"]["would_create"])
        self.assertEqual(result["data"]["field_name"], "x_internal_note")
        self.assertEqual(result["data"]["ttype"], "text")
        self.assertEqual(result["data"]["group_title"], "基础信息")
        self.assertEqual(result["data"]["action_id"], 11)
        self.assertEqual(result["data"]["field_metadata_boundary"], {
            "metadata_authority": "ir.model.fields",
            "placement_authority": "ui.business.config.contract.view_orchestration",
            "compatibility_write": "ui.form.field.policy",
            "rollback_boundary": "contract_rollback_does_not_delete_model_field",
        })
        self.assertEqual(wizard.created, [])
        self.assertEqual(wizard.checked, "create")
        self.assertEqual(fields.search_count_calls, [[("model", "=", "res.partner"), ("name", "=", "x_internal_note")]])

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

    def test_policy_set_requires_formal_contract_before_legacy_policy_write(self):
        class Company:
            id = 7

        class FieldRec:
            id = 5
            name = "phone"
            field_description = "电话"
            ttype = "char"

        class IrModel:
            id = 9
            transient = False

            def search(self, domain, limit=None):
                return self

        class IrFields:
            def search(self, domain, limit=None):
                return FieldRec()

        class PolicyModel:
            def __init__(self):
                self.created = []
                self.written = []

            def check_access_rights(self, operation):
                self.checked_operation = operation

            def search(self, domain, limit=None):
                return None

            def create(self, vals):
                self.created.append(vals)
                return vals

        class Env(dict):
            company = Company()

        class PartnerModel:
            _fields = {"phone": object()}

        policy_model = PolicyModel()
        handler = self.module.FormFieldPolicySetHandler(
            env=Env({
                "res.partner": PartnerModel(),
                "ir.model": IrModel(),
                "ir.model.fields": IrFields(),
                "ui.form.field.policy": policy_model,
            }),
            params={"model": "res.partner", "field_name": "phone", "visible": False},
        )

        result = handler.handle()

        self.assertFalse(result["ok"])
        self.assertEqual(result["code"], 500)
        self.assertEqual(result["error"]["reason_code"], "WRITE_FAILED")
        self.assertEqual(policy_model.created, [])

    def test_field_order_set_blocks_legacy_policy_write_when_contract_write_fails(self):
        class Company:
            id = 7

        class FieldRec:
            def __init__(self, name):
                self.id = 5
                self.name = name
                self.field_description = name.title()

        class IrModel:
            id = 9
            transient = False

            def search(self, domain, limit=None):
                return self

        class IrFields:
            def search(self, domain, limit=None):
                return [FieldRec("name"), FieldRec("phone")]

        class PolicyModel:
            def __init__(self):
                self.created = []
                self.written = []

            def check_access_rights(self, operation):
                self.checked_operation = operation

            def search(self, domain):
                return []

            def create(self, vals):
                self.created.append(vals)
                return vals

        class ContractModel:
            def sudo(self):
                return self

            def search(self, domain, limit=None):
                return None

            def create(self, vals):
                raise RuntimeError("contract unavailable")

        class Env(dict):
            company = Company()

        class PartnerModel:
            _fields = {"name": object(), "phone": object()}

        policy_model = PolicyModel()
        handler = self.module.FormFieldOrderSetHandler(
            env=Env({
                "res.partner": PartnerModel(),
                "ir.model": IrModel(),
                "ir.model.fields": IrFields(),
                "ui.form.field.policy": policy_model,
                "ui.business.config.contract": ContractModel(),
            }),
            params={"model": "res.partner", "field_order": ["name", "phone"]},
        )

        result = handler.handle()

        self.assertFalse(result["ok"])
        self.assertEqual(result["code"], 500)
        self.assertEqual(result["error"]["reason_code"], "WRITE_FAILED")
        self.assertEqual(policy_model.created, [])

    def test_batch_config_rejects_unknown_visibility_field_before_order_write(self):
        class Model:
            _fields = {"name": object()}

        handler = self.module.FormFieldConfigBatchSetHandler(
            env={"res.partner": Model()},
            params={
                "model": "res.partner",
                "field_order": ["name"],
                "field_visibility": {"missing": False},
            },
        )

        result = handler.handle()

        self.assertFalse(result["ok"])
        self.assertEqual(result["code"], 404)
        self.assertEqual(result["error"]["reason_code"], "NOT_FOUND")
        self.assertIn("res.partner.missing", result["error"]["message"])

    def test_batch_config_accepts_visibility_only_without_rewriting_order(self):
        class Company:
            id = 7

        class User:
            id = 42

        class FieldRec:
            id = 5
            name = "phone"
            field_description = "电话"

        class RecordSet(list):
            def __bool__(self):
                return bool(len(self))

        class IrModel:
            id = 9
            transient = False

            def search(self, domain, limit=None):
                return self

        class IrFields:
            def search(self, domain, limit=None):
                return RecordSet([FieldRec()])

        class PolicyModel:
            def __init__(self):
                self.created = []

            def check_access_rights(self, operation):
                self.checked_operation = operation

            def search(self, domain, limit=None):
                self.last_domain = domain
                return None

            def create(self, vals):
                self.created.append(vals)
                return vals

        class ContractModel:
            def sudo(self):
                return self

            def search(self, domain, limit=None):
                return None

            def create(self, vals):
                self.created_vals = vals

                class Record:
                    id = 1
                    contract_json = {}

                    def write(self, write_vals):
                        self.contract_json = write_vals["contract_json"]

                    def action_publish(self):
                        self.published = True

                rec = Record()
                rec.write(vals)
                rec.action_publish()
                self.record = rec
                return rec

        class Env(dict):
            company = Company()
            user = User()

        class PartnerModel:
            _fields = {"phone": object()}

        policy_model = PolicyModel()
        contract_model = ContractModel()
        env = Env({
            "res.partner": PartnerModel(),
            "ir.model": IrModel(),
            "ir.model.fields": IrFields(),
            "ui.form.field.policy": policy_model,
            "ui.business.config.contract": contract_model,
        })
        handler = self.module.FormFieldConfigBatchSetHandler(
            env=env,
            params={
                "model": "res.partner",
                "action_id": 11,
                "field_visibility": {"phone": False},
            },
        )

        result = handler.handle()

        self.assertTrue(result["ok"])
        self.assertEqual(result["data"]["updated_count"], 0)
        self.assertEqual(result["data"]["visibility_updated_count"], 1)
        self.assertEqual(result["data"]["business_config_boundary"], {
            "formal_authority": "ui.business.config.contract.view_orchestration",
            "compatibility_write": "ui.form.field.policy",
            "user_preference_boundary": "not_user_preference",
            "runtime_scope": "current_form",
        })
        self.assertEqual(result["meta"]["low_code_config"]["formal_authority"], "ui.business.config.contract.view_orchestration")
        self.assertEqual(result["meta"]["low_code_config"]["compatibility_write"], "ui.form.field.policy")
        self.assertEqual(result["meta"]["low_code_config"]["user_preference_boundary"], "not_user_preference")
        self.assertIn("field_groups", result["meta"]["low_code_config"]["capabilities"])
        self.assertIn("form_columns", result["meta"]["low_code_config"]["capabilities"])
        self.assertEqual(len(policy_model.created), 1)
        self.assertFalse(policy_model.created[0]["visible"])
        fields = contract_model.record.contract_json["view_orchestration"]["views"]["form"]["fields"]
        self.assertEqual(fields, [{"name": "phone", "visible": False}])

    def test_batch_visibility_blocks_legacy_policy_write_when_contract_write_fails(self):
        class Company:
            id = 7

        class FieldRec:
            id = 5
            name = "phone"
            field_description = "电话"

        class IrModel:
            id = 9
            transient = False

            def search(self, domain, limit=None):
                return self

        class IrFields:
            def search(self, domain, limit=None):
                return [FieldRec()]

        class PolicyModel:
            def __init__(self):
                self.created = []

            def check_access_rights(self, operation):
                self.checked_operation = operation

            def search(self, domain, limit=None):
                return None

            def create(self, vals):
                self.created.append(vals)
                return vals

        class ContractModel:
            def sudo(self):
                return self

            def search(self, domain, limit=None):
                return None

            def create(self, vals):
                raise RuntimeError("contract unavailable")

        class Env(dict):
            company = Company()

        class PartnerModel:
            _fields = {"phone": object()}

        policy_model = PolicyModel()
        handler = self.module.FormFieldConfigBatchSetHandler(
            env=Env({
                "res.partner": PartnerModel(),
                "ir.model": IrModel(),
                "ir.model.fields": IrFields(),
                "ui.form.field.policy": policy_model,
                "ui.business.config.contract": ContractModel(),
            }),
            params={"model": "res.partner", "field_visibility": {"phone": False}},
        )

        result = handler.handle()

        self.assertFalse(result["ok"])
        self.assertEqual(result["code"], 500)
        self.assertEqual(result["error"]["reason_code"], "WRITE_FAILED")
        self.assertEqual(policy_model.created, [])

    def test_batch_group_blocks_legacy_policy_write_when_contract_write_fails(self):
        class Company:
            id = 7

        class FieldRec:
            id = 5
            name = "phone"
            field_description = "电话"

        class IrModel:
            id = 9
            transient = False

            def search(self, domain, limit=None):
                return self

        class IrFields:
            def search(self, domain, limit=None):
                return [FieldRec()]

        class PolicyModel:
            def __init__(self):
                self.created = []

            def check_access_rights(self, operation):
                self.checked_operation = operation

            def search(self, domain, limit=None):
                return None

            def create(self, vals):
                self.created.append(vals)
                return vals

        class ContractModel:
            def sudo(self):
                return self

            def search(self, domain, limit=None):
                return None

            def create(self, vals):
                raise RuntimeError("contract unavailable")

        class Env(dict):
            company = Company()

        class PartnerModel:
            _fields = {"phone": object()}

        policy_model = PolicyModel()
        handler = self.module.FormFieldConfigBatchSetHandler(
            env=Env({
                "res.partner": PartnerModel(),
                "ir.model": IrModel(),
                "ir.model.fields": IrFields(),
                "ui.form.field.policy": policy_model,
                "ui.business.config.contract": ContractModel(),
            }),
            params={"model": "res.partner", "field_groups": {"phone": "基础信息"}},
        )

        result = handler.handle()

        self.assertFalse(result["ok"])
        self.assertEqual(result["code"], 500)
        self.assertEqual(result["error"]["reason_code"], "WRITE_FAILED")
        self.assertEqual(policy_model.created, [])

    def test_batch_config_mirrors_form_layout_capabilities_to_business_contract(self):
        class Company:
            id = 7

        class User:
            id = 42

        class FieldRec:
            def __init__(self, name, label):
                self.id = 5
                self.name = name
                self.field_description = label

        class RecordSet(list):
            def __bool__(self):
                return bool(len(self))

        class IrModel:
            id = 9
            transient = False

            def search(self, domain, limit=None):
                return self

        class IrFields:
            def search(self, domain, limit=None):
                return RecordSet([FieldRec("name", "客户名称"), FieldRec("email", "邮箱")])

        class PolicyModel:
            def check_access_rights(self, operation):
                self.checked_operation = operation

        class ContractModel:
            def sudo(self):
                return self

            def search(self, domain, limit=None):
                return None

            def create(self, vals):
                class Record:
                    id = 1
                    contract_json = {}

                    def write(self, write_vals):
                        self.contract_json = write_vals["contract_json"]
                        self.status = write_vals["status"]

                    def action_publish(self):
                        self.published = True

                rec = Record()
                rec.write(vals)
                rec.action_publish()
                self.record = rec
                return rec

        class Env(dict):
            company = Company()
            user = User()

        class PartnerModel:
            _fields = {"name": object(), "email": object()}

        contract_model = ContractModel()
        env = Env({
            "res.partner": PartnerModel(),
            "ir.model": IrModel(),
            "ir.model.fields": IrFields(),
            "ui.form.field.policy": PolicyModel(),
            "ui.business.config.contract": contract_model,
        })
        handler = self.module.FormFieldConfigBatchSetHandler(
            env=env,
            params={
                "model": "res.partner",
                "action_id": 11,
                "field_sizes": {"name": "wide", "email": "compact"},
                "field_widths": {"name": "span-2"},
                "form_columns": 3,
                "group_columns": {"基础信息": 2},
                "group_visibility": {"基础信息": True},
            },
        )

        result = handler.handle()

        self.assertTrue(result["ok"])
        self.assertEqual(result["data"]["field_layout_updated_count"], 2)
        self.assertEqual(result["data"]["business_config_layout_mirrored_count"], 2)
        self.assertIn("field_size", result["meta"]["low_code_config"]["capabilities"])
        self.assertIn("group_visibility", result["meta"]["low_code_config"]["capabilities"])
        form_spec = contract_model.record.contract_json["view_orchestration"]["views"]["form"]
        self.assertEqual(form_spec["columns"], 3)
        fields = {row["name"]: row for row in form_spec["fields"]}
        self.assertEqual(fields["name"]["field_size"], "wide")
        self.assertEqual(fields["name"]["width"], "span-2")
        self.assertEqual(fields["email"]["field_size"], "compact")

    def test_batch_config_mirrors_layout_only_without_field_rows(self):
        class Company:
            id = 7

        class User:
            id = 42

        class IrModel:
            id = 9
            transient = False

            def search(self, domain, limit=None):
                return self

        class PolicyModel:
            def check_access_rights(self, operation):
                self.checked_operation = operation

        class ContractModel:
            def sudo(self):
                return self

            def search(self, domain, limit=None):
                return None

            def create(self, vals):
                class Record:
                    id = 1
                    contract_json = {}

                    def write(self, write_vals):
                        self.contract_json = write_vals["contract_json"]
                        self.status = write_vals["status"]

                    def action_publish(self):
                        self.published = True

                rec = Record()
                rec.write(vals)
                rec.action_publish()
                self.record = rec
                return rec

        class Env(dict):
            company = Company()
            user = User()

        class PartnerModel:
            _fields = {"name": object()}

        contract_model = ContractModel()
        env = Env({
            "res.partner": PartnerModel(),
            "ir.model": IrModel(),
            "ir.model.fields": object(),
            "ui.form.field.policy": PolicyModel(),
            "ui.business.config.contract": contract_model,
        })
        handler = self.module.FormFieldConfigBatchSetHandler(
            env=env,
            params={
                "model": "res.partner",
                "form_columns": 4,
                "group_columns": {"基础信息": 2},
                "group_visibility": {"基础信息": False},
            },
        )

        result = handler.handle()

        self.assertTrue(result["ok"])
        self.assertEqual(result["data"]["field_layout_updated_count"], 0)
        self.assertEqual(result["data"]["business_config_layout_mirrored_count"], 1)
        form_spec = contract_model.record.contract_json["view_orchestration"]["views"]["form"]
        self.assertEqual(form_spec["columns"], 4)
        self.assertEqual(form_spec["fields"], [])
        self.assertEqual(form_spec["sections"], [{
            "name": "business_config_section_1",
            "title": "基础信息",
            "visible": False,
            "columns": 2,
            "sequence": 10,
            "fields": [],
        }])

    def test_batch_layout_returns_write_failed_when_contract_write_fails(self):
        class Company:
            id = 7

        class IrModel:
            id = 9
            transient = False

            def search(self, domain, limit=None):
                return self

        class ContractModel:
            def sudo(self):
                return self

            def search(self, domain, limit=None):
                return None

            def create(self, vals):
                raise RuntimeError("contract unavailable")

        class Env(dict):
            company = Company()

        class PartnerModel:
            _fields = {"name": object()}

        handler = self.module.FormFieldConfigBatchSetHandler(
            env=Env({
                "res.partner": PartnerModel(),
                "ir.model": IrModel(),
                "ir.model.fields": object(),
                "ui.form.field.policy": object(),
                "ui.business.config.contract": ContractModel(),
            }),
            params={"model": "res.partner", "form_columns": 3},
        )

        result = handler.handle()

        self.assertFalse(result["ok"])
        self.assertEqual(result["code"], 500)
        self.assertEqual(result["error"]["reason_code"], "WRITE_FAILED")

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

    def test_business_config_contract_precheck_accepts_view_orchestration_without_legacy_objects(self):
        handler = self.module.BusinessConfigContractSaveHandler(env={}, params={})

        result = handler._precheck_contract_payload({
            "view_orchestration": {
                "views": {
                    "form": {
                        "fields": [{"name": "name", "visible": True, "sequence": 10}],
                    },
                },
            },
        })

        self.assertEqual(result["errors"], [])
        self.assertNotIn("objects 为空，契约不会产生业务对象配置。", result["warnings"])

    def test_business_config_contract_precheck_requires_view_orchestration(self):
        handler = self.module.BusinessConfigContractSaveHandler(env={}, params={})

        result = handler._precheck_contract_payload({
            "objects": [{"name": "res.partner", "fields": []}],
        })

        self.assertIn("contract_json 必须包含 view_orchestration。", result["errors"])

    def test_business_config_contract_precheck_rejects_empty_view_orchestration_views(self):
        handler = self.module.BusinessConfigContractSaveHandler(env={}, params={})

        result = handler._precheck_contract_payload({
            "view_orchestration": {
                "views": {},
            },
        })

        self.assertIn("view_orchestration.views 必须至少包含一个非空视图配置。", result["errors"])

    def test_business_config_contract_precheck_rejects_empty_view_specs(self):
        handler = self.module.BusinessConfigContractSaveHandler(env={}, params={})

        result = handler._precheck_contract_payload({
            "view_orchestration": {
                "views": {
                    "form": {},
                    "tree": {"columns": []},
                },
            },
        })

        self.assertIn("view_orchestration.views 必须至少包含一个非空视图配置。", result["errors"])

    def test_business_config_contract_precheck_accepts_layout_only_view_config(self):
        handler = self.module.BusinessConfigContractSaveHandler(env={}, params={})

        result = handler._precheck_contract_payload({
            "view_orchestration": {
                "views": {
                    "form": {
                        "form_columns": 3,
                    },
                },
            },
        })

        self.assertEqual(result["errors"], [])

    def test_business_config_contract_save_rejects_legacy_lowcode_draft(self):
        handler = self.module.BusinessConfigContractSaveHandler(
            env={},
            params={
                "name": "demo",
                "model": "res.partner",
                "view_type": "form",
                "contract_json": {
                    "view_orchestration": {"views": {"form": {"fields": [{"name": "name"}]}}},
                    "legacy_lowcode_draft": {"objects": []},
                },
            },
        )

        result = handler.handle()

        self.assertFalse(result["ok"])
        self.assertEqual(result["code"], 400)
        self.assertEqual(result["error"]["reason_code"], "USER_ERROR")
        self.assertIn("legacy_lowcode_draft", result["error"]["message"])

    def test_business_config_contract_precheck_accepts_form_layout_schema(self):
        handler = self.module.BusinessConfigContractSaveHandler(env={}, params={})

        result = handler._precheck_contract_payload({
            "view_orchestration": {
                "views": {
                    "form": {
                        "fields": [{"name": "name", "visible": True, "sequence": 10}],
                        "layout": [
                            {
                                "type": "group",
                                "children": [
                                    {"type": "field", "name": "name"},
                                ],
                            }
                        ],
                    },
                },
            },
        })

        self.assertEqual(result["errors"], [])

    def test_business_config_contract_precheck_rejects_invalid_form_layout_schema(self):
        handler = self.module.BusinessConfigContractSaveHandler(env={}, params={})

        result = handler._precheck_contract_payload({
            "view_orchestration": {
                "views": {
                    "form": {
                        "fields": [{"name": "name", "visible": True, "sequence": 10}],
                        "layout": [
                            {"type": "field"},
                            {"type": "group", "children": {"type": "field", "name": "name"}},
                        ],
                    },
                },
            },
        })

        self.assertIn("view_orchestration.views.form.layout[0] 字段节点缺少 name。", result["errors"])
        self.assertIn("view_orchestration.views.form.layout[1].children 必须是数组。", result["errors"])

    def test_business_config_contract_save_uses_full_scope_domain(self):
        class Company:
            id = 7

        class Record:
            id = 3
            name = "demo"
            model = "res.partner"
            view_type = "form"
            status = "draft"
            version_no = 1
            role_key = "sales"

            class Ref:
                id = 0

            action_id = Ref()
            view_id = Ref()

            def write(self, vals):
                self.vals = vals

        class ContractModel:
            def __init__(self):
                self.record = Record()

            def search(self, domain, limit=None):
                self.domain = domain
                self.limit = limit
                return self.record

            def create(self, vals):
                raise AssertionError("expected existing scoped contract")

        class Env(dict):
            company = Company()

        contract_model = ContractModel()
        handler = self.module.BusinessConfigContractSaveHandler(
            env=Env({"ui.business.config.contract": contract_model}),
            params={
                "name": "demo",
                "model": "res.partner",
                "view_type": "form",
                "action_id": 11,
                "view_id": 22,
                "role_key": "sales",
                "contract_json": {"view_orchestration": {"views": {"form": {"fields": [{"name": "name"}]}}}},
            },
        )

        result = handler.handle()

        self.assertTrue(result["ok"])
        self.assertIn(("view_type", "=", "form"), contract_model.domain)
        self.assertIn(("action_id", "=", 11), contract_model.domain)
        self.assertIn(("view_id", "=", 22), contract_model.domain)
        self.assertIn(("role_key", "=", "sales"), contract_model.domain)

    def test_business_config_contract_save_normalizes_empty_role_scope(self):
        class Company:
            id = 7

        class ContractModel:
            def search(self, domain, limit=None):
                self.domain = domain
                return None

            def create(self, vals):
                self.vals = vals

                class Record:
                    id = 4
                    name = vals["name"]
                    model = vals["model"]
                    view_type = vals.get("view_type") or ""
                    status = vals.get("status") or "draft"
                    version_no = 1
                    role_key = vals.get("role_key") or ""

                    class Ref:
                        id = 0

                    action_id = Ref()
                    view_id = Ref()

                return Record()

        class Env(dict):
            company = Company()

        contract_model = ContractModel()
        handler = self.module.BusinessConfigContractSaveHandler(
            env=Env({"ui.business.config.contract": contract_model}),
            params={
                "name": "demo",
                "model": "res.partner",
                "view_type": "form",
                "contract_json": {"view_orchestration": {"views": {"form": {"fields": [{"name": "name"}]}}}},
            },
        )

        result = handler.handle()

        self.assertTrue(result["ok"])
        self.assertIn(("role_key", "=", False), contract_model.domain)
        self.assertFalse(contract_model.vals["role_key"])

    def test_business_config_contract_save_rejects_legacy_role_group_scope(self):
        handler = self.module.BusinessConfigContractSaveHandler(
            env={},
            params={
                "name": "demo",
                "model": "res.partner",
                "view_type": "form",
                "role_group_ids": [1, 2],
                "contract_json": {"view_orchestration": {"views": {"form": {"fields": [{"name": "name"}]}}}},
            },
        )

        result = handler.handle()

        self.assertFalse(result["ok"])
        self.assertEqual(result["code"], 400)
        self.assertEqual(result["error"]["reason_code"], "USER_ERROR")
        self.assertIn("role_key", result["error"]["message"])

    def test_business_config_contract_save_returns_write_failed_on_system_write_error(self):
        class Company:
            id = 7

        class ContractModel:
            def search(self, domain, limit=None):
                return None

            def create(self, vals):
                raise RuntimeError("database unavailable")

        class Env(dict):
            company = Company()

        handler = self.module.BusinessConfigContractSaveHandler(
            env=Env({"ui.business.config.contract": ContractModel()}),
            params={
                "name": "demo",
                "model": "res.partner",
                "view_type": "form",
                "contract_json": {"view_orchestration": {"views": {"form": {"fields": [{"name": "name"}]}}}},
            },
        )

        result = handler.handle()

        self.assertFalse(result["ok"])
        self.assertEqual(result["code"], 500)
        self.assertEqual(result["error"]["reason_code"], "WRITE_FAILED")

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

    def test_business_config_contract_publish_returns_write_failed_on_system_publish_error(self):
        class Company:
            id = 7

        class Contract:
            id = 3
            name = "contract"
            model = "res.partner"
            status = "draft"
            version_no = 1

            def action_publish(self):
                raise RuntimeError("publish failed")

        class ContractModel:
            def search(self, domain, limit=None):
                return Contract()

        class Env(dict):
            company = Company()

        handler = self.module.BusinessConfigContractPublishHandler(
            env=Env({"ui.business.config.contract": ContractModel()}),
            params={"model": "res.partner"},
        )

        result = handler.handle()

        self.assertFalse(result["ok"])
        self.assertEqual(result["code"], 500)
        self.assertEqual(result["error"]["reason_code"], "WRITE_FAILED")

    def test_business_config_contract_rollback_requires_name_or_model(self):
        handler = self.module.BusinessConfigContractRollbackHandler(
            env={},
            params={},
        )

        result = handler.handle()

        self.assertFalse(result["ok"])
        self.assertEqual(result["code"], 400)
        self.assertEqual(result["error"]["reason_code"], "MISSING_PARAMS")

    def test_business_config_contract_rollback_rejects_invalid_version_no(self):
        class Company:
            id = 7

        class Env(dict):
            company = Company()

        handler = self.module.BusinessConfigContractRollbackHandler(
            env=Env({"_": True}),
            params={"model": "res.partner", "version_no": "abc"},
        )

        result = handler.handle()

        self.assertFalse(result["ok"])
        self.assertEqual(result["code"], 400)
        self.assertEqual(result["error"]["reason_code"], "USER_ERROR")
        self.assertIn("version_no", result["error"]["message"])

    def test_business_config_contract_rollback_to_specific_version(self):
        class Company:
            id = 7

        class Ref:
            id = 0

        class Contract:
            id = 3
            name = "contract"
            model = "res.partner"
            view_type = "form"
            role_key = ""
            status = "published"
            version_no = 4
            action_id = Ref()
            view_id = Ref()

            def write(self, vals):
                self.written = vals
                self.contract_json = vals["contract_json"]
                self.status = vals["status"]
                self.version_no = vals["version_no"]

            def action_publish(self):
                self.status = "published"

        class Version:
            id = 8
            version_no = 2
            snapshot_json = {"view_orchestration": {"views": {"form": {"fields": [{"name": "name"}]}}}}

        class ContractModel:
            def search(self, domain, limit=None):
                self.domain = domain
                self.limit = limit
                return Contract()

        class VersionModel:
            def search(self, domain, order=None, limit=None):
                self.domain = domain
                self.order = order
                self.limit = limit
                return [Version()]

        class Env(dict):
            company = Company()

        contract_model = ContractModel()
        version_model = VersionModel()
        handler = self.module.BusinessConfigContractRollbackHandler(
            env=Env({
                "ui.business.config.contract": contract_model,
                "ui.business.config.contract.version": version_model,
            }),
            params={"model": "res.partner", "view_type": "form", "version_no": 2},
        )

        result = handler.handle()

        self.assertTrue(result["ok"])
        self.assertIn(("model", "=", "res.partner"), contract_model.domain)
        self.assertIn(("view_type", "in", [False, "form"]), contract_model.domain)
        self.assertEqual(version_model.domain, [("contract_id", "=", 3), ("version_no", "=", 2)])
        self.assertEqual(version_model.limit, 1)
        self.assertEqual(result["data"]["rolled_back_to_version"], 2)
        self.assertEqual(result["data"]["status"], "published")

    def test_business_config_contract_rollback_returns_write_failed_on_system_write_error(self):
        class Company:
            id = 7

        class Contract:
            id = 3
            name = "contract"
            model = "res.partner"
            version_no = 4

            def write(self, vals):
                raise RuntimeError("rollback write failed")

        class Version:
            version_no = 2
            snapshot_json = {"view_orchestration": {"views": {"form": {"fields": [{"name": "name"}]}}}}

        class ContractModel:
            def search(self, domain, limit=None):
                return Contract()

        class VersionModel:
            def search(self, domain, order=None, limit=None):
                return [Version()]

        class Env(dict):
            company = Company()

        handler = self.module.BusinessConfigContractRollbackHandler(
            env=Env({
                "ui.business.config.contract": ContractModel(),
                "ui.business.config.contract.version": VersionModel(),
            }),
            params={"model": "res.partner", "version_no": 2},
        )

        result = handler.handle()

        self.assertFalse(result["ok"])
        self.assertEqual(result["code"], 500)
        self.assertEqual(result["error"]["reason_code"], "WRITE_FAILED")

    def test_business_config_contract_rollback_specific_version_not_found(self):
        class Company:
            id = 7

        class Contract:
            id = 3

        class ContractModel:
            def search(self, domain, limit=None):
                return Contract()

        class VersionModel:
            def search(self, domain, order=None, limit=None):
                self.domain = domain
                return []

        class Env(dict):
            company = Company()

        version_model = VersionModel()
        handler = self.module.BusinessConfigContractRollbackHandler(
            env=Env({
                "ui.business.config.contract": ContractModel(),
                "ui.business.config.contract.version": version_model,
            }),
            params={"model": "res.partner", "version_no": 99},
        )

        result = handler.handle()

        self.assertFalse(result["ok"])
        self.assertEqual(result["code"], 404)
        self.assertEqual(result["error"]["reason_code"], "NOT_FOUND")
        self.assertEqual(version_model.domain, [("contract_id", "=", 3), ("version_no", "=", 99)])

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

    def test_low_code_field_rows_update_existing_business_config_contract(self):
        class Company:
            id = 7

        class Record:
            id = 1

            def __init__(self):
                self.contract_json = {
                    "view_orchestration": {
                        "views": {
                            "form": {
                                "fields": [
                                    {"name": "email", "label": "Old", "sequence": 100},
                                ],
                            }
                        }
                    }
                }

            def write(self, vals):
                self.contract_json = vals["contract_json"]
                self.written = vals

            def action_publish(self):
                self.published = True

        class ContractModel:
            def __init__(self):
                self.record = Record()

            def sudo(self):
                return self

            def search(self, domain, limit=None):
                return self.record

            def create(self, vals):
                raise AssertionError("existing contract should be updated")

        class Env(dict):
            company = Company()

        contract_model = ContractModel()
        env = Env({"ui.business.config.contract": contract_model})

        count = self.module._upsert_view_orchestration_field_rows(
            env,
            model="res.partner",
            view_type="form",
            rows=[
                {"name": "email", "label": "New", "visible": False, "sequence": 10},
                {"name": "phone", "label": "Phone", "sequence": 20},
            ],
        )

        self.assertEqual(count, 2)
        fields = contract_model.record.contract_json["view_orchestration"]["views"]["form"]["fields"]
        self.assertEqual([row["name"] for row in fields], ["email", "phone"])
        self.assertEqual(fields[0]["label"], "New")
        self.assertFalse(fields[0]["visible"])
        self.assertEqual(fields[0]["sequence"], 10)
        self.assertEqual(
            contract_model.record.contract_json["view_orchestration"]["context"]["source"],
            "smart_core.lowcode.form_field_policy",
        )
        self.assertTrue(contract_model.record.published)

    def test_low_code_field_group_update_rebuilds_form_layout(self):
        class Company:
            id = 7

        class Record:
            id = 1

            def __init__(self):
                self.contract_json = {
                    "view_orchestration": {
                        "views": {
                            "form": {
                                "fields": [
                                    {"name": "name", "label": "Name", "sequence": 10, "group_title": "基础信息"},
                                    {"name": "phone", "label": "Phone", "sequence": 20, "group_title": "联系信息"},
                                ],
                                "layout": [
                                    {"type": "group", "string": "基础信息", "children": [{"type": "field", "name": "name"}]},
                                    {"type": "group", "string": "联系信息", "children": [{"type": "field", "name": "phone"}]},
                                ],
                            }
                        }
                    }
                }

            def write(self, vals):
                self.contract_json = vals["contract_json"]

            def action_publish(self):
                self.published = True

        class ContractModel:
            def __init__(self):
                self.record = Record()

            def sudo(self):
                return self

            def search(self, domain, limit=None):
                return self.record

            def create(self, vals):
                raise AssertionError("existing contract should be updated")

        class Env(dict):
            company = Company()

        contract_model = ContractModel()
        env = Env({"ui.business.config.contract": contract_model})

        self.module._upsert_view_orchestration_field_rows(
            env,
            model="res.partner",
            view_type="form",
            rows=[
                {"name": "phone", "label": "Phone", "sequence": 15, "group_title": "基础信息"},
            ],
        )

        form_spec = contract_model.record.contract_json["view_orchestration"]["views"]["form"]
        fields = form_spec["fields"]
        self.assertEqual(fields[1]["name"], "phone")
        self.assertEqual(fields[1]["group_title"], "基础信息")
        self.assertEqual([group["string"] for group in form_spec["layout"]], ["基础信息"])
        self.assertEqual(
            [child["name"] for child in form_spec["layout"][0]["children"]],
            ["name", "phone"],
        )
        self.assertTrue(contract_model.record.published)

    def test_low_code_write_intents_declare_business_config_authority(self):
        for handler_class in (
            self.module.FormFieldPolicySetHandler,
            self.module.FormCustomFieldCreateHandler,
            self.module.FormFieldOrderSetHandler,
        ):
            contract = handler_class(env={}, params={})._source_authority_contract()
            self.assertIn("ui.business.config.contract", contract["authorities"])
            self.assertIn("ui.business.config.contract.version", contract["authorities"])
            self.assertIn("ui.form.field.policy", contract["authorities"])
            self.assertEqual(contract["lowcode_boundary"], "form_config")
            self.assertEqual(contract["contract_source"], "smart_core.lowcode.form_field_policy")

    def test_business_config_contract_list_uses_full_view_scope_domain(self):
        class Company:
            id = 7

        class ContractModel:
            def search(self, domain, limit=None, order=None):
                self.domain = domain
                self.limit = limit
                self.order = order
                return []

        class Env(dict):
            company = Company()

        contract_model = ContractModel()
        env = Env({"ui.business.config.contract": contract_model})
        handler = self.module.BusinessConfigContractListHandler(
            env=env,
            params={
                "model": "res.partner",
                "view_type": "list",
                "action_id": 11,
                "view_id": 22,
                "role_key": "sales",
                "status": "published",
            },
        )

        result = handler.handle()

        self.assertTrue(result["ok"])
        self.assertIn(("view_type", "in", [False, "tree"]), contract_model.domain)
        self.assertIn(("action_id", "=", 11), contract_model.domain)
        self.assertIn(("view_id", "=", 22), contract_model.domain)
        self.assertIn(("role_key", "=", "sales"), contract_model.domain)
        self.assertIn(("status", "=", "published"), contract_model.domain)

    def test_business_config_contract_versions_reports_scoped_version_summaries(self):
        class Company:
            id = 7

        class Ref:
            id = 0

        class User:
            display_name = "Admin"

        class Contract:
            id = 3
            name = "view_orchestration:res.partner:form:action:11:view:22"
            model = "res.partner"
            view_type = "form"
            action_id = Ref()
            view_id = Ref()
            role_key = "sales"
            status = "published"
            version_no = 3
            contract_json = {
                "view_orchestration": {
                    "views": {
                        "form": {
                            "fields": [
                                {"name": "name", "label": "客户名称"},
                                {"name": "email", "label": "联系邮箱"},
                            ]
                        },
                        "tree": {"columns": [{"name": "name"}]},
                        "search": {"filters": [{"field": "state"}], "group_by": [{"field": "partner_id"}]},
                        "pivot": {
                            "measures": [{"name": "amount_total"}],
                            "dimensions": [{"name": "company_id"}],
                        },
                        "graph": {"measure": "amount_total", "dimension": "company_id", "type": "bar"},
                        "calendar": {"date_slots": {"start": "start_date"}},
                        "dashboard": {
                            "metric_slots": {"primary": ["amount_total"]},
                            "chart_slots": {"trend": {"type": "line"}},
                            "navigation_slots": {"next": "project.dashboard.enter"},
                        },
                    }
                }
            }

        class Version:
            def __init__(self, ident, version_no, payload):
                self.id = ident
                self.version_no = version_no
                self.status = "published"
                self.snapshot_json = payload
                self.created_by = User()

        class ContractModel:
            def search(self, domain, limit=None, order=None):
                self.domain = domain
                self.limit = limit
                self.order = order
                return [Contract()]

        class VersionModel:
            def search(self, domain, order=None, limit=None):
                self.domain = domain
                self.order = order
                self.limit = limit
                return [
                    Version(20, 3, Contract.contract_json),
                    Version(19, 2, {
                        "view_orchestration": {
                            "views": {
                                "form": {"fields": [{"name": "name", "label": "旧客户名称"}]}
                            }
                        }
                    }),
                ]

        class Env(dict):
            company = Company()

        contract_model = ContractModel()
        version_model = VersionModel()
        handler = self.module.BusinessConfigContractVersionsHandler(
            env=Env({
                "ui.business.config.contract": contract_model,
                "ui.business.config.contract.version": version_model,
            }),
            params={
                "model": "res.partner",
                "view_type": "form",
                "action_id": 11,
                "view_id": 22,
                "role_key": "sales",
            },
        )

        result = handler.handle()

        self.assertTrue(result["ok"])
        self.assertIn(("view_type", "in", [False, "form"]), contract_model.domain)
        self.assertIn(("action_id", "=", 11), contract_model.domain)
        self.assertIn(("view_id", "=", 22), contract_model.domain)
        self.assertIn(("role_key", "=", "sales"), contract_model.domain)
        self.assertEqual(version_model.domain, [("contract_id", "=", 3)])
        self.assertEqual(version_model.order, "version_no desc, id desc")
        self.assertEqual(version_model.limit, 20)
        data = result["data"]
        self.assertEqual(data["contract_count"], 1)
        self.assertEqual(data["version_count"], 2)
        contract = data["contracts"][0]
        self.assertEqual(contract["summary"]["form_field_count"], 2)
        self.assertEqual(contract["summary"]["form_field_labels"], ["name:客户名称", "email:联系邮箱"])
        self.assertEqual(contract["summary"]["list_column_count"], 1)
        self.assertEqual(contract["summary"]["search_filter_count"], 1)
        self.assertEqual(contract["summary"]["search_group_by_count"], 1)
        self.assertEqual(contract["summary"]["analysis_item_count"], 9)
        self.assertEqual(contract["summary"]["analysis_items"], [
            "calendar.date_slots.start.start_date",
            "dashboard.chart_slots.trend.line",
            "dashboard.metric_slots.primary.amount_total",
            "dashboard.navigation_slots.next.project.dashboard.enter",
            "graph.dimension.company_id",
            "graph.measure.amount_total",
            "graph.type.bar",
            "pivot.dimensions.company_id",
            "pivot.measures.amount_total",
        ])
        self.assertEqual(contract["versions"][1]["summary"]["form_field_count"], 1)
        self.assertEqual(contract["versions"][1]["summary"]["form_field_labels"], ["name:旧客户名称"])
        self.assertEqual(contract["versions"][1]["summary"]["analysis_item_count"], 0)

    def test_business_config_contract_versions_rejects_legacy_role_group_scope(self):
        class Company:
            id = 7

        class Env(dict):
            company = Company()

        handler = self.module.BusinessConfigContractVersionsHandler(
            env=Env({"_": object()}),
            params={"model": "res.partner", "view_type": "form", "role_group_ids": [1]},
        )

        result = handler.handle()

        self.assertFalse(result["ok"])
        self.assertEqual(result["code"], 400)
        self.assertEqual(result["error"]["reason_code"], "USER_ERROR")
        self.assertIn("role_group_ids", result["error"]["message"])

    def test_business_config_form_audit_reports_contract_policy_overlap(self):
        class Company:
            id = 7

        class User:
            groups_id = []

        class PartnerModel:
            _fields = {"name": object(), "email": object(), "phone": object()}

        class Contract:
            id = 3
            name = "contract"
            version_no = 2
            contract_json = {
                "view_orchestration": {
                    "views": {
                        "form": {
                            "fields": [
                                {"name": "email", "sequence": 10},
                                {"name": "name", "sequence": 20},
                            ],
                            "layout": [
                                {"type": "group", "children": [
                                    {"type": "field", "name": "email"},
                                    {"type": "field", "name": "name"},
                                ]},
                            ],
                        }
                    }
                }
            }

        class ContractModel:
            def _effective_view_orchestration_contracts(self, model, **kwargs):
                self.model = model
                self.kwargs = kwargs
                return [Contract()]

        class Groups:
            ids = []

        class Policy:
            def __init__(self, ident, field_name):
                self.id = ident
                self.field_name = field_name
                self.visible = True
                self.label = field_name.title()
                self.sequence = 100
                self.role_group_ids = Groups()

        class PolicyModel:
            def _effective_policies(self, model, **kwargs):
                self.model = model
                self.kwargs = kwargs
                return [Policy(9, "email"), Policy(10, "phone")]

        class Env(dict):
            company = Company()
            user = User()

        env = Env({
            "res.partner": PartnerModel(),
            "ui.business.config.contract": ContractModel(),
            "ui.form.field.policy": PolicyModel(),
        })
        handler = self.module.BusinessConfigFormAuditHandler(
            env=env,
            params={"model": "res.partner", "action_id": 11, "view_id": 22, "role_key": "sales"},
        )

        result = handler.handle()

        self.assertTrue(result["ok"])
        data = result["data"]
        self.assertEqual(data["runtime_source"], "ui.business.config.contract.view_orchestration")
        self.assertTrue(data["contract_authoritative"])
        self.assertFalse(data["legacy_policy_runtime_enabled"])
        self.assertEqual(data["business_config_form_fields"], ["email", "name"])
        self.assertEqual(data["business_config_form_layout_fields"], ["email", "name"])
        self.assertEqual(data["business_config_form_layout_field_count"], 2)
        self.assertTrue(data["has_business_config_form_layout"])
        self.assertTrue(data["layout_matches_fields"])
        self.assertEqual(data["layout_mismatch_contracts"], [])
        self.assertTrue(data["business_config_contracts"][0]["has_layout"])
        self.assertTrue(data["business_config_contracts"][0]["layout_matches_fields"])
        self.assertEqual(data["legacy_policy_fields"], ["email", "phone"])
        self.assertEqual(data["skipped_legacy_policy_fields"], ["email"])
        self.assertEqual(data["legacy_only_policy_fields"], ["phone"])
        self.assertEqual(data["suppressed_legacy_policy_fields"], ["email", "phone"])
        self.assertEqual(data["active_legacy_policy_fields"], [])
        self.assertTrue(data["has_conflict"])

    def test_business_config_form_audit_uses_legacy_policy_only_without_contract(self):
        class Company:
            id = 7

        class User:
            groups_id = []

        class PartnerModel:
            _fields = {"name": object(), "phone": object()}

        class ContractModel:
            def _effective_view_orchestration_contracts(self, model, **kwargs):
                return []

        class Groups:
            ids = []

        class Policy:
            id = 9
            field_name = "phone"
            visible = True
            label = "Phone"
            sequence = 100
            role_group_ids = Groups()

        class PolicyModel:
            def _effective_policies(self, model, **kwargs):
                return [Policy()]

        class Env(dict):
            company = Company()
            user = User()

        handler = self.module.BusinessConfigFormAuditHandler(
            env=Env({
                "res.partner": PartnerModel(),
                "ui.business.config.contract": ContractModel(),
                "ui.form.field.policy": PolicyModel(),
            }),
            params={"model": "res.partner"},
        )

        result = handler.handle()

        self.assertTrue(result["ok"])
        data = result["data"]
        self.assertEqual(data["runtime_source"], "ui.form.field.policy")
        self.assertFalse(data["contract_authoritative"])
        self.assertTrue(data["legacy_policy_runtime_enabled"])
        self.assertEqual(data["active_legacy_policy_fields"], ["phone"])
        self.assertEqual(data["suppressed_legacy_policy_fields"], [])

    def test_business_config_list_search_audit_reports_contract_and_preference_boundary(self):
        class Company:
            id = 7

        class User:
            groups_id = []

        class PartnerModel:
            _fields = {
                "name": object(),
                "email": object(),
                "state": object(),
                "partner_id": object(),
                "activity_state": object(),
                "alias_name": object(),
                "message_ids": object(),
                "access_token": object(),
            }

        class Contract:
            def __init__(self, ident, name, payload):
                self.id = ident
                self.name = name
                self.version_no = 2
                self.contract_json = payload

        class ContractModel:
            def _effective_view_orchestration_contracts(self, model, **kwargs):
                self.model = model
                view_type = kwargs.get("view_type")
                if view_type == "tree":
                    return [
                        Contract(3, "list", {
                            "view_orchestration": {
                                "views": {
                                    "tree": {
                                        "columns": [
                                            {"name": "name", "label": "客户名称"},
                                            {"name": "stage_id", "label": "CODEX_STAGE_HIDDEN", "visible": False},
                                            {"name": "email", "label": "邮箱"},
                                        ]
                                    }
                                }
                            }
                        })
                    ]
                if view_type == "search":
                    return [
                        Contract(4, "search", {
                            "view_orchestration": {
                                "views": {
                                    "search": {
                                        "filters": [{"field": "state"}],
                                        "group_by": [{"field": "partner_id"}],
                                    }
                                }
                            }
                        })
                    ]
                return []

        class PreferenceModel:
            def sudo(self):
                return self

            def search_count(self, domain):
                self.domain = domain
                return 2

            def search(self, domain, order=None, limit=None):
                self.search_domain = domain
                self.search_order = order
                self.search_limit = limit
                return [
                    type("Preference", (), {
                        "id": 31,
                        "user_id": type("UserRef", (), {"id": 9, "name": "配置员"})(),
                        "scope_key": "ui:list_columns:list:action:11",
                        "action_id": type("ActionRef", (), {"id": 11})(),
                        "model_name": "res.partner",
                        "view_type": "list",
                        "preference_key": "list_columns",
                        "value_json": {"columns": ["name", "email"]},
                    })(),
                ]

        class Env(dict):
            company = Company()
            user = User()

        env = Env({
            "res.partner": PartnerModel(),
            "ui.business.config.contract": ContractModel(),
            "sc.user.view.preference": PreferenceModel(),
        })
        handler = self.module.BusinessConfigListSearchAuditHandler(
            env=env,
            params={"model": "res.partner", "action_id": 11, "view_id": 22, "role_key": "sales"},
        )
        handler._action_tree_view_labels = lambda **kwargs: {"name": "Odoo名称", "email": "Odoo邮箱"}

        result = handler.handle()

        self.assertTrue(result["ok"])
        data = result["data"]
        self.assertEqual(data["runtime_source"], "ui.business.config.contract.view_orchestration")
        self.assertTrue(data["contract_authoritative"])
        self.assertFalse(data["suggested_defaults_only"])
        self.assertEqual(data["business_config_list_columns"], ["name", "email"])
        self.assertEqual(data["business_config_list_column_labels"], {"name": "客户名称", "email": "邮箱"})
        self.assertEqual(data["business_config_list_contracts"][0]["column_labels"], {"name": "客户名称", "email": "邮箱"})
        self.assertEqual(data["business_config_search_filters"], ["state"])
        self.assertEqual(data["business_config_search_group_by"], ["partner_id"])
        self.assertEqual(
            [item["name"] for item in data["available_model_fields"]],
            ["email", "name", "partner_id", "state"],
        )
        self.assertEqual(data["user_preference_count"], 2)
        self.assertEqual(data["user_preferences"], [{
            "id": 31,
            "user_id": 9,
            "user_name": "配置员",
            "scope_key": "ui:list_columns:list:action:11",
            "action_id": 11,
            "model": "res.partner",
            "view_type": "list",
            "preference_key": "list_columns",
            "column_count": 2,
        }])
        self.assertEqual(data["user_preference_boundary"], "ui_only")
        self.assertTrue(data["has_business_list_config"])
        self.assertTrue(data["has_business_search_config"])

    def test_business_config_list_search_audit_suggests_runtime_view_defaults(self):
        class Company:
            id = 7

        class User:
            groups_id = []

        class PartnerModel:
            _fields = {
                "name": object(),
                "email": object(),
                "state": object(),
                "partner_id": object(),
                "manager_id": object(),
                "user_id": object(),
                "legacy_source_created_by": object(),
                "access_token": object(),
                "activity_state": object(),
            }

            def fields_get(self):
                return {
                    "name": {"string": "名称", "type": "char"},
                    "email": {"string": "邮箱", "type": "char"},
                    "state": {"string": "状态", "type": "selection"},
                    "partner_id": {"string": "往来单位", "type": "many2one"},
                    "manager_id": {"string": "项目经理", "type": "many2one"},
                    "user_id": {"string": "Project Manager", "type": "many2one"},
                    "legacy_source_created_by": {"string": "原始录入人", "type": "char"},
                    "access_token": {"string": "Security Token", "type": "char"},
                    "activity_state": {"string": "Activity State", "type": "selection"},
                }

        class ContractModel:
            def _effective_view_orchestration_contracts(self, model, **kwargs):
                return []

            def search(self, domain, order=None, limit=None):
                return []

        class RuntimeViewContract:
            def __init__(self, view_type):
                self.view_type = view_type

            def with_user(self, user):
                return self

            def sudo(self):
                return self

            def with_context(self, **context):
                self.context = context
                return self

            def get_contract_api(self, filter_runtime=True, check_model_acl=False):
                if self.view_type == "tree":
                    return {
                        "columns": [
                            "name",
                            {"name": "email"},
                            "manager_id",
                            "user_id",
                            "legacy_source_created_by",
                            "access_token",
                            "missing_field",
                        ],
                    }
                return {
                    "search": {
                        "filters": [{"field": "state"}, {"field": "activity_state"}],
                        "group_by": [{"field": "partner_id"}, {"field": "missing_group"}],
                    }
                }

        class ViewConfigModel:
            def with_context(self, **context):
                self.context = context
                return self

            def _generate_from_fields_view_get(self, model, view_type):
                return RuntimeViewContract(view_type)

        class Env(dict):
            company = Company()
            user = User()

        env = Env({
            "res.partner": PartnerModel(),
            "ui.business.config.contract": ContractModel(),
            "app.view.config": ViewConfigModel(),
        })
        handler = self.module.BusinessConfigListSearchAuditHandler(
            env=env,
            params={"model": "res.partner", "action_id": 11},
        )

        result = handler.handle()

        self.assertTrue(result["ok"])
        data = result["data"]
        self.assertEqual(data["runtime_source"], "runtime_backend_view_contract")
        self.assertFalse(data["contract_authoritative"])
        self.assertTrue(data["suggested_defaults_only"])
        self.assertEqual(data["business_config_list_columns"], [])
        self.assertEqual(data["business_config_search_filters"], [])
        self.assertEqual(data["business_config_search_group_by"], [])
        self.assertEqual(data["suggested_list_columns"], ["name", "email", "manager_id"])
        self.assertEqual(data["suggested_search_filters"], ["state"])
        self.assertEqual(data["suggested_search_group_by"], ["partner_id"])
        self.assertFalse(data["has_business_list_config"])
        self.assertFalse(data["has_business_search_config"])

    def test_business_config_list_search_audit_preserves_explicit_empty_contracts(self):
        class Company:
            id = 7

        class User:
            groups_id = []

        class PartnerModel:
            _fields = {"name": object(), "company_id": object()}

            def fields_get(self):
                return {
                    "name": {"string": "名称", "type": "char"},
                    "company_id": {"string": "公司", "type": "many2one"},
                }

        class Contract:
            def __init__(self, ident, view_type, spec):
                self.id = ident
                self.name = "empty.%s" % view_type
                self.version_no = 3
                self.contract_json = {"view_orchestration": {"views": {view_type: spec}}}

        class ContractModel:
            def __init__(self, search_spec):
                self.records = {
                    "tree": [Contract(1, "tree", {"columns": []})],
                    "search": [Contract(2, "search", search_spec)],
                }

            def sudo(self):
                return self

            def _effective_view_orchestration_contracts(self, model, **kwargs):
                return self.records.get(kwargs.get("view_type"), [])

            def search(self, domain, order=None, limit=None):
                raise AssertionError("published fallback must not run when an effective contract exists")

        class Env(dict):
            company = Company()
            user = User()

        cases = (
            ({"filters": [], "group_by": [{"field": "company_id"}]}, [], ["company_id"]),
            ({"filters": [{"field": "name"}], "group_by": []}, ["name"], []),
            ({"filters": [], "group_by": []}, [], []),
        )
        for search_spec, expected_filters, expected_groups in cases:
            with self.subTest(search_spec=search_spec):
                env = Env({
                    "res.partner": PartnerModel(),
                    "ui.business.config.contract": ContractModel(search_spec),
                })
                handler = self.module.BusinessConfigListSearchAuditHandler(
                    env=env,
                    params={"model": "res.partner", "action_id": 11, "view_id": 22, "role_key": "config_admin"},
                )
                handler._suggested_columns = lambda **kwargs: self.fail("empty list contract must suppress suggestions")
                handler._suggested_search = lambda **kwargs: self.fail("empty search contract must suppress suggestions")

                data = handler.handle()["data"]

                self.assertTrue(data["contract_authoritative"])
                self.assertTrue(data["has_business_list_config"])
                self.assertTrue(data["has_business_search_config"])
                self.assertEqual(data["business_config_list_columns"], [])
                self.assertEqual(data["business_config_search_filters"], expected_filters)
                self.assertEqual(data["business_config_search_group_by"], expected_groups)
                self.assertEqual(data["suggested_list_columns"], [])
                self.assertEqual(data["suggested_search_filters"], [])
                self.assertEqual(data["suggested_search_group_by"], [])

    def test_business_config_list_search_set_writes_contracts_not_preferences(self):
        class Company:
            id = 7

        class User:
            id = 42

        class PartnerModel:
            _fields = {"name": object(), "email": object(), "state": object(), "partner_id": object()}

        class EmptyRef:
            id = 0

        class Contract:
            def __init__(self, ident, vals):
                self.id = ident
                self.version_no = 1
                self.action_id = EmptyRef()
                self.view_id = EmptyRef()
                self.write(vals)

            def write(self, vals):
                for key, value in vals.items():
                    if key == "action_id":
                        self.action_id = type("Ref", (), {"id": int(value or 0)})()
                    elif key == "view_id":
                        self.view_id = type("Ref", (), {"id": int(value or 0)})()
                    else:
                        setattr(self, key, value)
                return True

            def action_publish(self):
                self.status = "published"
                self.version_no += 1

        class ContractModel(list):
            def sudo(self):
                return self

            def search(self, domain, limit=None, order=None):
                name = next((value for field, op, value in domain if field == "name" and op == "="), "")
                rows = [row for row in self if row.name == name]
                if limit == 1:
                    return rows[0] if rows else None
                return rows

            def create(self, vals):
                rec = Contract(len(self) + 1, vals)
                self.append(rec)
                return rec

        class PreferenceModel:
            touched = False

            def search(self, *args, **kwargs):
                self.touched = True
                return []

        class Env(dict):
            company = Company()
            user = User()

        contracts = ContractModel()
        preferences = PreferenceModel()
        env = Env({
            "res.partner": PartnerModel(),
            "ui.business.config.contract": contracts,
            "sc.user.view.preference": preferences,
        })
        handler = self.module.BusinessConfigListSearchSetHandler(
            env=env,
            params={
                "model": "res.partner",
                "action_id": 11,
                "list_columns": ["name", "email"],
                "search_filters": ["state"],
                "search_group_by": ["partner_id"],
            },
        )

        result = handler.handle()

        self.assertTrue(result["ok"])
        self.assertEqual(result["data"]["saved_count"], 2)
        self.assertEqual(len(contracts), 2)
        tree_contract = next(row for row in contracts if row.view_type == "tree")
        search_contract = next(row for row in contracts if row.view_type == "search")
        self.assertEqual(
            [row["name"] for row in tree_contract.contract_json["view_orchestration"]["views"]["tree"]["columns"]],
            ["name", "email"],
        )
        self.assertEqual(
            [row["field"] for row in search_contract.contract_json["view_orchestration"]["views"]["search"]["filters"]],
            ["state"],
        )
        self.assertEqual(
            [row["field"] for row in search_contract.contract_json["view_orchestration"]["views"]["search"]["group_by"]],
            ["partner_id"],
        )
        self.assertFalse(preferences.touched)

    def test_business_config_list_search_set_rejects_unknown_fields(self):
        class Company:
            id = 7

        class PartnerModel:
            _fields = {"name": object()}

        class ContractModel(list):
            def sudo(self):
                return self

            def search(self, *args, **kwargs):
                return None

            def create(self, vals):
                self.append(vals)
                return vals

        class Env(dict):
            company = Company()

        contracts = ContractModel()
        env = Env({
            "res.partner": PartnerModel(),
            "ui.business.config.contract": contracts,
        })
        handler = self.module.BusinessConfigListSearchSetHandler(
            env=env,
            params={
                "model": "res.partner",
                "action_id": 11,
                "list_columns": ["name", "missing_field"],
            },
        )

        result = handler.handle()

        self.assertFalse(result["ok"])
        self.assertEqual(result["code"], 400)
        self.assertIn("missing_field", result["error"]["message"])
        self.assertEqual(len(contracts), 0)

    def test_business_config_list_search_set_returns_write_failed_when_contract_write_fails(self):
        class Company:
            id = 7

        class PartnerModel:
            _fields = {"name": object()}

        class ContractModel:
            def sudo(self):
                return self

            def search(self, domain, limit=None):
                return None

            def create(self, vals):
                raise RuntimeError("contract unavailable")

        class PreferenceModel:
            touched = False

            def search(self, *args, **kwargs):
                self.touched = True
                return []

        class Env(dict):
            company = Company()

        preferences = PreferenceModel()
        handler = self.module.BusinessConfigListSearchSetHandler(
            env=Env({
                "res.partner": PartnerModel(),
                "ui.business.config.contract": ContractModel(),
                "sc.user.view.preference": preferences,
            }),
            params={"model": "res.partner", "list_columns": ["name"]},
        )

        result = handler.handle()

        self.assertFalse(result["ok"])
        self.assertEqual(result["code"], 500)
        self.assertEqual(result["error"]["reason_code"], "WRITE_FAILED")
        self.assertFalse(preferences.touched)

    def test_business_config_analysis_set_writes_contracts_not_preferences(self):
        class Company:
            id = 7

        class PartnerModel:
            _fields = {"amount_total": object(), "company_id": object(), "state": object()}

        class EmptyRef:
            id = 0

        class Contract:
            def __init__(self, ident, vals):
                self.id = ident
                self.version_no = 1
                self.action_id = EmptyRef()
                self.view_id = EmptyRef()
                self.write(vals)

            def write(self, vals):
                for key, value in vals.items():
                    if key == "action_id":
                        self.action_id = type("Ref", (), {"id": int(value or 0)})()
                    elif key == "view_id":
                        self.view_id = type("Ref", (), {"id": int(value or 0)})()
                    else:
                        setattr(self, key, value)
                return True

            def action_publish(self):
                self.status = "published"
                self.version_no += 1

        class ContractModel(list):
            def sudo(self):
                return self

            def search(self, domain, limit=None, order=None):
                name = next((value for field, op, value in domain if field == "name" and op == "="), "")
                rows = [row for row in self if row.name == name]
                if limit == 1:
                    return rows[0] if rows else None
                return rows

            def create(self, vals):
                rec = Contract(len(self) + 1, vals)
                self.append(rec)
                return rec

        class PreferenceModel:
            touched = False

            def search(self, *args, **kwargs):
                self.touched = True
                return []

        class Env(dict):
            company = Company()

        preferences = PreferenceModel()
        contracts = ContractModel()
        env = Env({
            "res.partner": PartnerModel(),
            "ui.business.config.contract": contracts,
            "sc.user.view.preference": preferences,
        })
        handler = self.module.BusinessConfigAnalysisSetHandler(
            env=env,
            params={
                "model": "res.partner",
                "action_id": 11,
                "pivot_measures": ["amount_total"],
                "pivot_dimensions": ["company_id"],
                "graph_measures": ["amount_total"],
                "graph_dimensions": ["state"],
                "graph_type": "line",
            },
        )

        result = handler.handle()

        self.assertTrue(result["ok"])
        self.assertEqual(result["data"]["saved_count"], 2)
        self.assertEqual(result["data"]["business_config_boundary"], "business_contract")
        self.assertEqual(result["data"]["user_preference_boundary"], "not_a_source")
        self.assertEqual(len(contracts), 2)
        pivot_contract = next(row for row in contracts if row.view_type == "pivot")
        graph_contract = next(row for row in contracts if row.view_type == "graph")
        self.assertEqual(
            [row["name"] for row in pivot_contract.contract_json["view_orchestration"]["views"]["pivot"]["measures"]],
            ["amount_total"],
        )
        self.assertEqual(
            [row["name"] for row in pivot_contract.contract_json["view_orchestration"]["views"]["pivot"]["dimensions"]],
            ["company_id"],
        )
        self.assertEqual(graph_contract.contract_json["view_orchestration"]["views"]["graph"]["type"], "line")
        self.assertEqual(graph_contract.contract_json["view_orchestration"]["views"]["graph"]["dimension"], "state")
        self.assertFalse(preferences.touched)

    def test_business_config_analysis_set_rejects_unknown_fields(self):
        class Company:
            id = 7

        class PartnerModel:
            _fields = {"amount_total": object()}

        class ContractModel(list):
            def sudo(self):
                return self

            def search(self, *args, **kwargs):
                return None

            def create(self, vals):
                self.append(vals)
                return vals

        class Env(dict):
            company = Company()

        contracts = ContractModel()
        env = Env({
            "res.partner": PartnerModel(),
            "ui.business.config.contract": contracts,
        })
        handler = self.module.BusinessConfigAnalysisSetHandler(
            env=env,
            params={
                "model": "res.partner",
                "action_id": 11,
                "pivot_measures": ["amount_total"],
                "pivot_dimensions": ["missing_field"],
            },
        )

        result = handler.handle()

        self.assertFalse(result["ok"])
        self.assertEqual(result["code"], 400)
        self.assertIn("missing_field", result["error"]["message"])
        self.assertEqual(len(contracts), 0)

    def test_business_config_analysis_set_returns_write_failed_when_contract_write_fails(self):
        class Company:
            id = 7

        class PartnerModel:
            _fields = {"amount_total": object()}

        class ContractModel:
            def sudo(self):
                return self

            def search(self, domain, limit=None):
                return None

            def create(self, vals):
                raise RuntimeError("contract unavailable")

        class Env(dict):
            company = Company()

        handler = self.module.BusinessConfigAnalysisSetHandler(
            env=Env({
                "res.partner": PartnerModel(),
                "ui.business.config.contract": ContractModel(),
            }),
            params={"model": "res.partner", "pivot_measures": ["amount_total"]},
        )

        result = handler.handle()

        self.assertFalse(result["ok"])
        self.assertEqual(result["code"], 500)
        self.assertEqual(result["error"]["reason_code"], "WRITE_FAILED")

    def test_business_config_analysis_set_rejects_internal_lowcode_fields(self):
        class Company:
            id = 7

        class PartnerModel:
            _fields = {
                "amount_total": object(),
                "message_ids": object(),
                "legacy_source_created_by": object(),
            }

            def fields_get(self):
                return {
                    "amount_total": {"string": "金额", "type": "float"},
                    "message_ids": {"string": "Messages", "type": "one2many"},
                    "legacy_source_created_by": {"string": "原始录入人", "type": "char"},
                }

        class ContractModel(list):
            def sudo(self):
                return self

            def search(self, *args, **kwargs):
                return None

            def create(self, vals):
                self.append(vals)
                return vals

        class Env(dict):
            company = Company()

        contracts = ContractModel()
        env = Env({
            "res.partner": PartnerModel(),
            "ui.business.config.contract": contracts,
        })
        handler = self.module.BusinessConfigAnalysisSetHandler(
            env=env,
            params={
                "model": "res.partner",
                "action_id": 11,
                "pivot_measures": ["amount_total"],
                "pivot_dimensions": ["legacy_source_created_by"],
            },
        )

        result = handler.handle()

        self.assertFalse(result["ok"])
        self.assertEqual(result["code"], 400)
        self.assertIn("legacy_source_created_by", result["error"]["message"])
        self.assertEqual(len(contracts), 0)

    def test_business_config_analysis_audit_suggests_runtime_view_defaults(self):
        class Company:
            id = 7

        class User:
            groups_id = []

        class PartnerModel:
            _fields = {
                "amount_total": object(),
                "company_id": object(),
                "state": object(),
                "message_ids": object(),
                "legacy_source_created_by": object(),
            }

            def fields_get(self):
                return {
                    "amount_total": {"string": "金额", "type": "float"},
                    "company_id": {"string": "公司", "type": "many2one"},
                    "state": {"string": "状态", "type": "selection"},
                    "message_ids": {"string": "Messages", "type": "one2many"},
                    "legacy_source_created_by": {"string": "原始录入人", "type": "char"},
                }

        class ContractModel:
            def sudo(self):
                return self

            def _effective_view_orchestration_contracts(self, model, **kwargs):
                return []

            def search(self, domain, order=None, limit=None):
                return []

        class RuntimeViewContract:
            def __init__(self, view_type):
                self.view_type = view_type

            def with_user(self, user):
                return self

            def sudo(self):
                return self

            def with_context(self, **context):
                return self

            def get_contract_api(self, filter_runtime=True, check_model_acl=False):
                if self.view_type == "pivot":
                    return {
                        "pivot": {
                            "measures": [{"name": "amount_total"}, {"name": "missing_measure"}],
                            "dimensions": [{"name": "company_id"}, {"name": "legacy_source_created_by"}],
                        }
                    }
                return {
                    "graph": {
                        "type_default": "line",
                        "measures": [{"name": "amount_total"}],
                        "dimensions": [{"name": "state"}, {"name": "message_ids"}],
                    }
                }

        class ViewConfigModel:
            def with_context(self, **context):
                return self

            def _generate_from_fields_view_get(self, model, view_type):
                return RuntimeViewContract(view_type)

        class Env(dict):
            company = Company()
            user = User()

        env = Env({
            "res.partner": PartnerModel(),
            "ui.business.config.contract": ContractModel(),
            "app.view.config": ViewConfigModel(),
        })
        handler = self.module.BusinessConfigAnalysisAuditHandler(
            env=env,
            params={"model": "res.partner", "action_id": 11},
        )

        result = handler.handle()

        self.assertTrue(result["ok"])
        data = result["data"]
        self.assertEqual(data["pivot_measures"], [])
        self.assertEqual(data["pivot_dimensions"], [])
        self.assertEqual(data["graph_measures"], [])
        self.assertEqual(data["graph_dimensions"], [])
        self.assertEqual(data["suggested_pivot_measures"], ["amount_total"])
        self.assertEqual(data["suggested_pivot_dimensions"], ["company_id"])
        self.assertEqual(data["suggested_graph_measures"], ["amount_total"])
        self.assertEqual(data["suggested_graph_dimensions"], ["state"])
        self.assertEqual(data["suggested_graph_type"], "line")
        self.assertFalse(data["has_business_pivot_config"])
        self.assertFalse(data["has_business_graph_config"])
        self.assertFalse(data["has_business_analysis_config"])

    def test_business_config_analysis_audit_preserves_explicit_empty_contracts(self):
        class Company:
            id = 7

        class User:
            groups_id = []

        class PartnerModel:
            _fields = {"amount_total": object(), "company_id": object()}

            def fields_get(self):
                return {
                    "amount_total": {"string": "金额", "type": "float"},
                    "company_id": {"string": "公司", "type": "many2one"},
                }

        class Contract:
            def __init__(self, ident, view_type):
                self.id = ident
                self.name = "empty.%s" % view_type
                self.version_no = 4
                self.contract_json = {"view_orchestration": {"views": {
                    view_type: {"measures": [], "dimensions": [], "type": "bar"},
                }}}

        class ContractModel:
            def __init__(self):
                self.records = {"pivot": [Contract(1, "pivot")], "graph": [Contract(2, "graph")]}

            def sudo(self):
                return self

            def _effective_view_orchestration_contracts(self, model, **kwargs):
                return self.records.get(kwargs.get("view_type"), [])

            def search(self, domain, order=None, limit=None):
                raise AssertionError("published fallback must not run when an effective contract exists")

        class Env(dict):
            company = Company()
            user = User()

        env = Env({
            "res.partner": PartnerModel(),
            "ui.business.config.contract": ContractModel(),
        })
        handler = self.module.BusinessConfigAnalysisAuditHandler(
            env=env,
            params={"model": "res.partner", "action_id": 11, "view_id": 22, "role_key": "config_admin"},
        )
        handler._suggested_analysis = lambda **kwargs: self.fail("empty analysis contract must suppress suggestions")

        data = handler.handle()["data"]

        self.assertTrue(data["has_business_pivot_config"])
        self.assertTrue(data["has_business_graph_config"])
        self.assertTrue(data["has_business_analysis_config"])
        self.assertEqual(data["pivot_measures"], [])
        self.assertEqual(data["pivot_dimensions"], [])
        self.assertEqual(data["graph_measures"], [])
        self.assertEqual(data["graph_dimensions"], [])
        self.assertEqual(data["suggested_pivot_measures"], [])
        self.assertEqual(data["suggested_pivot_dimensions"], [])
        self.assertEqual(data["suggested_graph_measures"], [])
        self.assertEqual(data["suggested_graph_dimensions"], [])

    def test_business_config_analysis_bootstrap_derives_from_runtime_view_contracts(self):
        class Company:
            id = 7

        class User:
            id = 42

        class PartnerModel:
            _fields = {"amount_total": object(), "company_id": object(), "state": object()}

        class EmptyRef:
            id = 0

        class Contract:
            def __init__(self, ident, vals):
                self.id = ident
                self.version_no = 1
                self.action_id = EmptyRef()
                self.view_id = EmptyRef()
                self.write(vals)

            def write(self, vals):
                for key, value in vals.items():
                    if key == "action_id":
                        self.action_id = type("Ref", (), {"id": int(value or 0)})()
                    elif key == "view_id":
                        self.view_id = type("Ref", (), {"id": int(value or 0)})()
                    else:
                        setattr(self, key, value)
                return True

            def action_publish(self):
                self.status = "published"
                self.version_no += 1

        class ContractModel(list):
            def sudo(self):
                return self

            def search(self, domain, limit=None, order=None):
                name = next((value for field, op, value in domain if field == "name" and op == "="), "")
                rows = [row for row in self if row.name == name]
                if limit == 1:
                    return rows[0] if rows else None
                return rows

            def create(self, vals):
                rec = Contract(len(self) + 1, vals)
                self.append(rec)
                return rec

        class RuntimeViewContract:
            def __init__(self, view_type):
                self.view_type = view_type

            def with_user(self, user):
                return self

            def sudo(self):
                return self

            def with_context(self, **context):
                return self

            def get_contract_api(self, filter_runtime=True, check_model_acl=False):
                if self.view_type == "pivot":
                    return {
                        "pivot": {
                            "measures": [{"name": "amount_total"}, {"name": "missing_measure"}],
                            "dimensions": [{"name": "company_id"}],
                        }
                    }
                return {
                    "graph": {
                        "type_default": "line",
                        "measures": [{"name": "amount_total"}],
                        "dimensions": [{"name": "state"}, {"name": "missing_dimension"}],
                    }
                }

        class ViewConfigModel:
            def with_context(self, **context):
                return self

            def _generate_from_fields_view_get(self, model, view_type):
                self.last_model = model
                return RuntimeViewContract(view_type)

        class Env(dict):
            company = Company()
            user = User()

        contracts = ContractModel()
        env = Env({
            "res.partner": PartnerModel(),
            "app.view.config": ViewConfigModel(),
            "ui.business.config.contract": contracts,
        })
        handler = self.module.BusinessConfigAnalysisBootstrapHandler(
            env=env,
            params={"model": "res.partner", "action_id": 11, "publish": True},
        )

        result = handler.handle()

        self.assertTrue(result["ok"])
        self.assertEqual(result["data"]["saved_count"], 2)
        self.assertEqual(result["data"]["personal_preference_boundary"], "not_a_source")
        self.assertEqual(result["data"]["pivot_measures"], ["amount_total"])
        self.assertEqual(result["data"]["pivot_dimensions"], ["company_id"])
        self.assertEqual(result["data"]["graph_measures"], ["amount_total"])
        self.assertEqual(result["data"]["graph_dimensions"], ["state"])
        self.assertEqual(result["data"]["graph_type"], "line")
        self.assertEqual({row.view_type for row in contracts}, {"pivot", "graph"})

    def test_business_config_analysis_bootstrap_falls_back_to_model_fields(self):
        class Company:
            id = 7

        class User:
            id = 42

        class Field:
            def __init__(self, field_type):
                self.type = field_type

        class PartnerModel:
            _fields = {
                "amount_total": Field("float"),
                "company_id": Field("many2one"),
                "state": Field("selection"),
                "name": Field("char"),
                "line_ids": Field("one2many"),
            }

        class EmptyRef:
            id = 0

        class Contract:
            def __init__(self, ident, vals):
                self.id = ident
                self.version_no = 1
                self.action_id = EmptyRef()
                self.view_id = EmptyRef()
                self.write(vals)

            def write(self, vals):
                for key, value in vals.items():
                    if key == "action_id":
                        self.action_id = type("Ref", (), {"id": int(value or 0)})()
                    elif key == "view_id":
                        self.view_id = type("Ref", (), {"id": int(value or 0)})()
                    else:
                        setattr(self, key, value)
                return True

            def action_publish(self):
                self.status = "published"
                self.version_no += 1

        class ContractModel(list):
            def sudo(self):
                return self

            def search(self, domain, limit=None, order=None):
                return None

            def create(self, vals):
                rec = Contract(len(self) + 1, vals)
                self.append(rec)
                return rec

        class RuntimeViewContract:
            def with_user(self, user):
                return self

            def sudo(self):
                return self

            def with_context(self, **context):
                return self

            def get_contract_api(self, filter_runtime=True, check_model_acl=False):
                return {}

        class ViewConfigModel:
            def with_context(self, **context):
                return self

            def _generate_from_fields_view_get(self, model, view_type):
                return RuntimeViewContract()

        class Env(dict):
            company = Company()
            user = User()

        contracts = ContractModel()
        env = Env({
            "res.partner": PartnerModel(),
            "app.view.config": ViewConfigModel(),
            "ui.business.config.contract": contracts,
        })
        handler = self.module.BusinessConfigAnalysisBootstrapHandler(
            env=env,
            params={"model": "res.partner", "action_id": 11, "view_types": ["pivot"], "publish": True},
        )

        result = handler.handle()

        self.assertTrue(result["ok"])
        self.assertEqual(result["data"]["pivot_measures"], ["amount_total"])
        self.assertEqual(result["data"]["pivot_dimensions"][:2], ["company_id", "state"])
        self.assertEqual(len(contracts), 1)

    def test_business_config_list_search_bootstrap_derives_from_runtime_view_contracts(self):
        class Company:
            id = 7

        class User:
            id = 42

        class PartnerModel:
            _fields = {
                "name": object(),
                "email": object(),
                "state": object(),
                "partner_id": object(),
                "x_technical": object(),
                "create_date": object(),
                "write_uid": object(),
            }

        class EmptyRef:
            id = 0

        class Contract:
            def __init__(self, ident, vals):
                self.id = ident
                self.version_no = 1
                self.action_id = EmptyRef()
                self.view_id = EmptyRef()
                self.write(vals)

            def write(self, vals):
                for key, value in vals.items():
                    if key == "action_id":
                        self.action_id = type("Ref", (), {"id": int(value or 0)})()
                    elif key == "view_id":
                        self.view_id = type("Ref", (), {"id": int(value or 0)})()
                    else:
                        setattr(self, key, value)
                return True

            def action_publish(self):
                self.status = "published"
                self.version_no += 1

        class ContractModel(list):
            def sudo(self):
                return self

            def search(self, domain, limit=None, order=None):
                name = next((value for field, op, value in domain if field == "name" and op == "="), "")
                rows = [row for row in self if row.name == name]
                if limit == 1:
                    return rows[0] if rows else None
                return rows

            def create(self, vals):
                rec = Contract(len(self) + 1, vals)
                self.append(rec)
                return rec

        class RuntimeViewContract:
            def __init__(self, view_type):
                self.view_type = view_type

            def with_user(self, user):
                self.user = user
                return self

            def sudo(self):
                return self

            def with_context(self, **context):
                self.context = context
                return self

            def get_contract_api(self, filter_runtime=True, check_model_acl=False):
                if self.view_type == "tree":
                    return {
                        "columns": ["name", {"name": "email"}, "create_date", "missing_field"],
                        "columns_schema": [],
                    }
                return {
                    "search": {
                        "filters": [{"field": "state"}, {"field": "write_uid"}, {"field": "missing_filter"}],
                        "group_by": [{"field": "partner_id"}, {"field": "create_date"}],
                    }
                }

        class ViewConfigModel:
            def __init__(self):
                self.contexts = []

            def with_context(self, **context):
                self.contexts.append(context)
                return self

            def _generate_from_fields_view_get(self, model, view_type):
                self.last_model = model
                return RuntimeViewContract(view_type)

        class PreferenceModel:
            touched = False

            def search(self, *args, **kwargs):
                self.touched = True
                return []

            def search_count(self, *args, **kwargs):
                self.touched = True
                return 0

        class Env(dict):
            company = Company()
            user = User()

        contracts = ContractModel()
        preferences = PreferenceModel()
        env = Env({
            "res.partner": PartnerModel(),
            "app.view.config": ViewConfigModel(),
            "ui.business.config.contract": contracts,
            "sc.user.view.preference": preferences,
        })
        handler = self.module.BusinessConfigListSearchBootstrapHandler(
            env=env,
            params={"model": "res.partner", "action_id": 11, "publish": True},
        )

        result = handler.handle()

        self.assertTrue(result["ok"])
        self.assertEqual(result["data"]["saved_count"], 2)
        self.assertEqual(result["data"]["personal_preference_boundary"], "not_a_source")
        self.assertEqual(result["data"]["list_columns"], ["name", "email"])
        self.assertEqual(result["data"]["search_filters"], ["state"])
        self.assertEqual(result["data"]["search_group_by"], ["partner_id"])
        tree_contract = next(row for row in contracts if row.view_type == "tree")
        search_contract = next(row for row in contracts if row.view_type == "search")
        self.assertEqual(
            [row["name"] for row in tree_contract.contract_json["view_orchestration"]["views"]["tree"]["columns"]],
            ["name", "email"],
        )
        self.assertEqual(
            [row["field"] for row in search_contract.contract_json["view_orchestration"]["views"]["search"]["filters"]],
            ["state"],
        )
        self.assertFalse(preferences.touched)

    def test_business_config_form_bootstrap_derives_layout_from_runtime_form_contract(self):
        class Company:
            id = 7

        class User:
            id = 42

        class PartnerModel:
            _fields = {
                "name": object(),
                "email": object(),
                "manager_id": object(),
                "user_id": object(),
                "legacy_source_created_by": object(),
                "access_token": object(),
                "missing_kept_out": object(),
            }

            def fields_get(self):
                return {
                    "name": {"string": "名称", "type": "char"},
                    "email": {"string": "邮箱", "type": "char"},
                    "manager_id": {"string": "项目经理", "type": "many2one"},
                    "user_id": {"string": "Project Manager", "type": "many2one"},
                    "legacy_source_created_by": {"string": "原始录入人", "type": "char"},
                    "access_token": {"string": "Security Token", "type": "char"},
                    "missing_kept_out": {"string": "Missing", "type": "char"},
                }

        class EmptyRef:
            id = 0

        class Contract:
            def __init__(self, ident, vals):
                self.id = ident
                self.version_no = 1
                self.action_id = EmptyRef()
                self.view_id = EmptyRef()
                self.write(vals)

            def write(self, vals):
                for key, value in vals.items():
                    if key == "action_id":
                        self.action_id = type("Ref", (), {"id": int(value or 0)})()
                    elif key == "view_id":
                        self.view_id = type("Ref", (), {"id": int(value or 0)})()
                    else:
                        setattr(self, key, value)
                return True

            def action_publish(self):
                self.status = "published"
                self.version_no += 1

        class ContractModel(list):
            def search(self, domain, limit=None):
                name = next((value for field, op, value in domain if field == "name" and op == "="), "")
                rows = [row for row in self if row.name == name]
                if limit == 1:
                    return rows[0] if rows else None
                return rows

            def create(self, vals):
                rec = Contract(len(self) + 1, vals)
                self.append(rec)
                return rec

        class RuntimeFormContract:
            def with_user(self, user):
                self.user = user
                return self

            def sudo(self):
                return self

            def with_context(self, **context):
                self.context = context
                return self

            def get_contract_api(self, filter_runtime=True, check_model_acl=False):
                return {
                    "title": "客户",
                    "layout": [
                        {
                            "type": "sheet",
                            "children": [
                                {
                                    "type": "group",
                                    "children": [
                                        {"type": "field", "name": "name"},
                                        {"type": "field", "name": "email"},
                                        {"type": "field", "name": "manager_id"},
                                        {"type": "field", "name": "user_id"},
                                        {"type": "field", "name": "legacy_source_created_by"},
                                        {"type": "field", "name": "access_token"},
                                        {"type": "field", "name": "not_a_field"},
                                    ],
                                }
                            ],
                        }
                    ],
                }

        class ViewConfigModel:
            def with_context(self, **context):
                self.context = context
                return self

            def _generate_from_fields_view_get(self, model, view_type):
                self.last = (model, view_type)
                return RuntimeFormContract()

        class Env(dict):
            company = Company()
            user = User()

        contracts = ContractModel()
        env = Env({
            "res.partner": PartnerModel(),
            "app.view.config": ViewConfigModel(),
            "ui.business.config.contract": contracts,
        })
        handler = self.module.BusinessConfigFormBootstrapHandler(
            env=env,
            payload={"params": {"model": "res.partner", "action_id": 11, "publish": True}},
        )

        result = handler.handle()

        self.assertTrue(result["ok"])
        self.assertEqual(result["data"]["field_count"], 3)
        self.assertEqual(result["data"]["form_fields"], ["name", "email", "manager_id"])
        self.assertEqual(result["data"]["bootstrapped_from"], "runtime_backend_form_view_contract")
        self.assertEqual(len(contracts), 1)
        rec = contracts[0]
        form_spec = rec.contract_json["view_orchestration"]["views"]["form"]
        self.assertEqual([row["name"] for row in form_spec["fields"]], ["name", "email", "manager_id"])
        layout_fields = self.module._collect_view_orchestration_layout_field_names(form_spec["layout"])
        self.assertEqual(layout_fields, ["name", "email", "manager_id"])
        self.assertEqual(form_spec["title"], "客户")
        self.assertEqual(rec.status, "published")
        self.assertEqual(rec.action_id.id, 11)

    def test_business_config_contract_publish_rejects_invalid_scope_id(self):
        class Company:
            id = 7

        class Env(dict):
            company = Company()

        handler = self.module.BusinessConfigContractPublishHandler(
            env=Env({"ui.business.config.contract": object()}),
            params={"model": "res.partner", "action_id": "bad"},
        )

        result = handler.handle()

        self.assertFalse(result["ok"])
        self.assertEqual(result["code"], 400)
        self.assertEqual(result["error"]["reason_code"], "USER_ERROR")
        self.assertIn("action_id", result["error"]["message"])

    def test_contract_reload_hint_normalizes_scope(self):
        hint = self.module._contract_reload_hint(
            model="res.partner",
            view_type="list",
            action_id=11,
            view_id=22,
            role_key="sales",
            version_no=5,
        )

        self.assertTrue(hint["required"])
        self.assertEqual(hint["reason"], "view_orchestration_config_changed")
        self.assertEqual(hint["view_type"], "tree")
        self.assertEqual(hint["action_id"], 11)
        self.assertEqual(hint["view_id"], 22)
        self.assertEqual(hint["role_key"], "sales")
        self.assertEqual(hint["orchestration_version"], "5")


if __name__ == "__main__":
    unittest.main()
