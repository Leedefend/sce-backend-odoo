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


class _Model:
    _fields = {"name": object(), "project_id": object()}

    def with_context(self, context):
        return self

    def browse(self, record_id):
        return _Record(record_id)

    def check_access_rights(self, mode):
        return True


class _Record:
    write_calls = []

    def __init__(self, record_id):
        self.id = record_id

    def exists(self):
        return self

    def write(self, vals):
        self.write_calls.append(vals)

    def check_access_rule(self, mode):
        return True


class _FakeRecordSet(list):
    search_domains = []

    def sudo(self):
        return self

    def search(self, domain):
        self.search_domains.append(domain)
        return self


class _FakePolicy:
    def __init__(self, model, field_name):
        self.model = model
        self.field_name = field_name


class _FakeField:
    def __init__(self, model, name, *, state="manual", ttype="char", readonly=False):
        self.model = model
        self.name = name
        self.state = state
        self.ttype = ttype
        self.readonly = readonly


class _FakeEnv:
    def __init__(self, policies=None, fields=None):
        self._models = {
            "ui.form.field.policy": _FakeRecordSet(policies or []),
            "ir.model.fields": _FakeRecordSet(fields or []),
        }

    def __contains__(self, model):
        return model in self._models

    def __getitem__(self, model):
        return self._models[model]


def _install_module(name, **attrs):
    module = types.ModuleType(name)
    for key, value in attrs.items():
        setattr(module, key, value)
    sys.modules[name] = module
    return module


def _load_handler():
    root = Path(__file__).resolve().parents[1]
    exc_mod = _install_module("odoo.exceptions", AccessError=type("AccessError", (Exception,), {}))
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
    _install_module(
        "odoo.addons.smart_core.core.project_context",
        apply_business_scope_domain=lambda env_model, domain, params=None, context=None: (domain, {"applied": False}),
        apply_project_scope_domain=lambda env_model, domain, project_id: (domain, {"applied": False}),
        record_scope_denied_response=lambda meta, message="": {"ok": False, "meta": meta, "message": message},
        project_scope_denied_response=lambda meta: {"ok": False, "meta": meta},
        record_in_business_scope=lambda env_model, record_id, params=None, context=None: (True, {"applied": False}),
        record_in_project_scope=lambda env_model, record_id, project_id: (True, {"applied": False}),
        selected_record_context_id_from_context=lambda params, context: None,
        selected_project_id_from_context=lambda params, context: None,
    )
    _install_module(
        "odoo.addons.smart_core.utils.idempotency",
        apply_idempotency_identity=lambda data, **kwargs: {**data, **kwargs},
        build_idempotency_conflict_response=lambda **kwargs: {"ok": False},
        build_idempotency_fingerprint=lambda payload, normalize_id_keys=None: "fp",
        find_recent_audit_entry=lambda *args, **kwargs: None,
        normalize_request_id=lambda value, prefix: value or f"{prefix}_1",
        replay_window_seconds=lambda default, env_key=None: default,
    )
    _install_module("odoo.addons.smart_core.utils.extension_hooks", call_extension_hook_first=lambda *args, **kwargs: None)

    reason_name = "odoo.addons.smart_core.utils.reason_codes"
    sys.modules.pop(reason_name, None)
    reason_spec = importlib.util.spec_from_file_location(reason_name, root / "utils" / "reason_codes.py")
    reason_module = importlib.util.module_from_spec(reason_spec)
    sys.modules[reason_name] = reason_module
    reason_spec.loader.exec_module(reason_module)

    module_name = "odoo.addons.smart_core.handlers.api_data_write"
    sys.modules.pop(module_name, None)
    spec = importlib.util.spec_from_file_location(module_name, root / "handlers" / "api_data_write.py")
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


class TestApiDataWriteIdBoundaries(unittest.TestCase):
    def setUp(self):
        self.module = _load_handler()

    def test_invalid_record_id_returns_invalid_id(self):
        handler = self.module.ApiDataWriteHandler(
            env={"res.partner": _Model()},
            params={"model": "res.partner", "id": "bad", "vals": {"name": "A"}},
        )

        result = handler.handle(payload={"intent": "api.data.write"})

        self.assertFalse(result["ok"])
        self.assertEqual(result["code"], 400)
        self.assertEqual(result["error"]["reason_code"], "INVALID_ID")

    def test_non_positive_record_id_returns_invalid_id(self):
        handler = self.module.ApiDataWriteHandler(
            env={"res.partner": _Model()},
            params={"model": "res.partner", "ids": [0], "vals": {"name": "A"}},
        )

        result = handler.handle(payload={"intent": "api.data.write"})

        self.assertFalse(result["ok"])
        self.assertEqual(result["code"], 400)
        self.assertEqual(result["error"]["reason_code"], "INVALID_ID")

    def test_string_false_dry_run_still_writes(self):
        _Record.write_calls = []
        handler = self.module.ApiDataWriteHandler(
            env={"res.partner": _Model()},
            params={"model": "res.partner", "id": 9, "vals": {"name": "A"}, "dry_run": "false"},
        )

        result = handler.handle(payload={"intent": "api.data.write"})

        self.assertTrue(result["ok"])
        self.assertFalse(result["data"]["dry_run"])
        self.assertEqual(_Record.write_calls, [{"name": "A"}])

    def test_write_rejects_invalid_project_id(self):
        self.module.selected_record_context_id_from_context = lambda params, context: 3
        self.module.ApiDataWriteHandler.ALLOWED_MODELS = {"res.partner": {"name", "project_id"}}
        handler = self.module.ApiDataWriteHandler(
            env={"res.partner": _Model()},
            params={"model": "res.partner", "id": 9, "vals": {"project_id": "bad"}},
        )

        result = handler.handle(payload={"intent": "api.data.write"})

        self.assertFalse(result["ok"])
        self.assertEqual(result["code"], 400)
        self.assertEqual(result["error"]["reason_code"], "USER_ERROR")
        self.assertEqual(result["error"]["message"], "project_id 无效")

    def test_create_rejects_invalid_project_id(self):
        self.module.selected_record_context_id_from_context = lambda params, context: 3
        self.module.apply_business_scope_domain = lambda env_model, domain, params=None, context=None: (
            domain,
            {"applied": True, "project_id": 3},
        )
        self.module.ApiDataWriteHandler.ALLOWED_MODELS = {"res.partner": {"name", "project_id"}}
        handler = self.module.ApiDataWriteHandler(
            env={"res.partner": _Model()},
            params={"model": "res.partner", "vals": {"name": "A", "project_id": "bad"}},
        )

        result = handler.handle(payload={"intent": "api.data.create"})

        self.assertFalse(result["ok"])
        self.assertEqual(result["code"], 400)
        self.assertEqual(result["error"]["reason_code"], "USER_ERROR")
        self.assertEqual(result["error"]["message"], "project_id 无效")

    def test_allowed_models_merges_only_safe_manual_custom_policy_fields(self):
        _FakeRecordSet.search_domains = []
        self.module.ApiDataWriteHandler.ALLOWED_MODELS = {"res.partner": {"name"}}
        env = _FakeEnv(
            policies=[
                _FakePolicy("res.partner", "x_safe_note"),
                _FakePolicy("res.partner", "x_not_manual"),
                _FakePolicy("res.partner", "x_many_tags"),
                _FakePolicy("res.partner", "phone"),
            ],
            fields=[
                _FakeField("res.partner", "x_safe_note"),
                _FakeField("res.partner", "x_not_manual", state="base"),
                _FakeField("res.partner", "x_many_tags", ttype="many2many"),
                _FakeField("res.partner", "phone"),
            ],
        )
        handler = self.module.ApiDataWriteHandler(env=env)

        allowed = handler._allowed_models()

        self.assertEqual(allowed["res.partner"], {"name", "x_safe_note"})

    def test_custom_field_policy_search_is_scoped_to_active_company(self):
        company = types.SimpleNamespace(id=17)
        other_company = types.SimpleNamespace(id=23)
        env = _FakeEnv(
            policies=[_FakePolicy("res.partner", "x_safe_note")],
            fields=[_FakeField("res.partner", "x_safe_note")],
        )
        env.company = company
        env.companies = [company, other_company]
        policy_rows = env["ui.form.field.policy"]
        policy_rows.search_domains = []
        handler = self.module.ApiDataWriteHandler(env=env)

        handler._allowed_models()

        self.assertIn(("company_id", "=", False), policy_rows.search_domains[0])
        self.assertIn(("company_id", "=", 17), policy_rows.search_domains[0])
        self.assertNotIn(("company_id", "in", [17, 23]), policy_rows.search_domains[0])

    def test_runtime_config_models_cannot_use_generic_write_proxy(self):
        self.module.ApiDataWriteHandler.ALLOWED_MODELS = {"ui.form.field.policy": {"field_name"}}
        handler = self.module.ApiDataWriteHandler(
            env={"ui.form.field.policy": _Model()},
            params={"model": "ui.form.field.policy", "id": 9, "vals": {"field_name": "x_bad"}},
        )

        result = handler.handle(payload={"intent": "api.data.write"})

        self.assertFalse(result["ok"])
        self.assertEqual(result["code"], 403)
        self.assertEqual(result["error"]["reason_code"], "UNSUPPORTED_SOURCE")
        self.assertIn("专用配置入口", result["error"]["message"])

    def test_approval_policy_cannot_use_generic_create_proxy(self):
        self.module.ApiDataWriteHandler.ALLOWED_MODELS = {"sc.approval.policy": {"name"}}
        handler = self.module.ApiDataWriteHandler(
            env={"sc.approval.policy": _Model()},
            params={"model": "sc.approval.policy", "vals": {"name": "Bad Policy"}},
        )

        result = handler.handle(payload={"intent": "api.data.create"})

        self.assertFalse(result["ok"])
        self.assertEqual(result["code"], 403)
        self.assertEqual(result["error"]["reason_code"], "UNSUPPORTED_SOURCE")
        self.assertIn("专用配置入口", result["error"]["message"])


if __name__ == "__main__":
    unittest.main()
