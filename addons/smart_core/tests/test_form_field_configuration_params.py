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
        self.assertEqual(len(policy_model.created), 1)
        self.assertFalse(policy_model.created[0]["visible"])
        fields = contract_model.record.contract_json["view_orchestration"]["views"]["form"]["fields"]
        self.assertEqual(fields, [{"name": "phone", "visible": False}])

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
                "contract_json": {"objects": [{"name": "res.partner", "fields": []}]},
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
                "contract_json": {"objects": [{"name": "res.partner", "fields": []}]},
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
                "contract_json": {"objects": [{"name": "res.partner", "fields": []}]},
            },
        )

        result = handler.handle()

        self.assertFalse(result["ok"])
        self.assertEqual(result["code"], 400)
        self.assertEqual(result["error"]["reason_code"], "USER_ERROR")
        self.assertIn("role_key", result["error"]["message"])

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
        self.assertEqual(data["active_legacy_policy_fields"], ["phone"])
        self.assertTrue(data["has_conflict"])

    def test_business_config_list_search_audit_reports_contract_and_preference_boundary(self):
        class Company:
            id = 7

        class User:
            groups_id = []

        class PartnerModel:
            _fields = {"name": object(), "email": object(), "state": object(), "partner_id": object()}

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
                                        "columns": [{"name": "name"}, {"name": "email"}]
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

        result = handler.handle()

        self.assertTrue(result["ok"])
        data = result["data"]
        self.assertEqual(data["business_config_list_columns"], ["email", "name"])
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
                        "columns": ["name", {"name": "email"}, "missing_field"],
                        "columns_schema": [],
                    }
                return {
                    "search": {
                        "filters": [{"field": "state"}, {"field": "missing_filter"}],
                        "group_by": [{"field": "partner_id"}],
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
            _fields = {"name": object(), "email": object(), "missing_kept_out": object()}

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
        self.assertEqual(result["data"]["field_count"], 2)
        self.assertEqual(result["data"]["form_fields"], ["name", "email"])
        self.assertEqual(result["data"]["bootstrapped_from"], "runtime_backend_form_view_contract")
        self.assertEqual(len(contracts), 1)
        rec = contracts[0]
        form_spec = rec.contract_json["view_orchestration"]["views"]["form"]
        self.assertEqual([row["name"] for row in form_spec["fields"]], ["name", "email"])
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
