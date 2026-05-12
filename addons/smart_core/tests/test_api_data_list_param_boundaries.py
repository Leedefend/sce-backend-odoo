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

    _install_module("odoo")
    _install_module("odoo.tools")
    _install_module("odoo.tools.safe_eval", safe_eval=lambda value, *args, **kwargs: value)
    _install_module("odoo.exceptions", AccessError=type("AccessError", (Exception,), {}))
    _install_module("odoo.http", request=None)

    smart_core_mod = _install_module("odoo.addons.smart_core")
    handlers_mod = _install_module("odoo.addons.smart_core.handlers")
    core_mod = _install_module("odoo.addons.smart_core.core")
    utils_mod = _install_module("odoo.addons.smart_core.utils")
    _install_module("odoo.addons")
    smart_core_mod.__path__ = [str(root)]
    handlers_mod.__path__ = [str(root / "handlers")]
    core_mod.__path__ = [str(root / "core")]
    utils_mod.__path__ = [str(root / "utils")]

    _install_module("odoo.addons.smart_core.core.base_handler", BaseIntentHandler=_BaseIntentHandler)
    _install_module(
        "odoo.addons.smart_core.core.api_data_execution_policy",
        client_requested_sudo=lambda params: False,
        resolve_api_data_sudo=lambda params: False,
    )
    _install_module(
        "odoo.addons.smart_core.core.project_context",
        apply_project_scope_domain=lambda env_model, domain, project_id: (domain, {"applied": False}),
        selected_project_id_from_context=lambda params, context: None,
    )
    _install_module(
        "odoo.addons.smart_core.utils.extension_hooks",
        call_extension_hook_first=lambda *args, **kwargs: None,
    )
    reason_mod = _install_module("odoo.addons.smart_core.utils.reason_codes")
    reason_mod.REASON_OK = "OK"
    reason_mod.REASON_PROJECT_SCOPE_DENIED = "PROJECT_SCOPE_DENIED"
    reason_mod.REASON_READONLY_PROJECTION_MUTATION_DENIED = "READONLY_PROJECTION_MUTATION_DENIED"
    reason_mod.REASON_RECORD_VERSION_CONFLICT = "RECORD_VERSION_CONFLICT"
    reason_mod.failure_meta_for_reason = lambda reason: {"reason_code": reason}

    request_params_name = "odoo.addons.smart_core.core.request_params"
    sys.modules.pop(request_params_name, None)
    request_params_spec = importlib.util.spec_from_file_location(
        request_params_name, root / "core" / "request_params.py"
    )
    request_params_module = importlib.util.module_from_spec(request_params_spec)
    sys.modules[request_params_name] = request_params_module
    request_params_spec.loader.exec_module(request_params_module)

    module_name = "odoo.addons.smart_core.handlers.api_data"
    sys.modules.pop(module_name, None)
    spec = importlib.util.spec_from_file_location(module_name, root / "handlers" / "api_data.py")
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


class TestApiDataListParamBoundaries(unittest.TestCase):
    def setUp(self):
        module = _load_handler()
        self.handler = module.ApiDataHandler(env={})

    def test_invalid_limit_returns_bad_request(self):
        result = self.handler._op_list("x.model", {"limit": "bad"}, {}, False)

        self.assertFalse(result["ok"])
        self.assertEqual(result["error"]["code"], 400)
        self.assertEqual(result["error"]["message"], "limit 无效")

    def test_negative_offset_returns_bad_request(self):
        result = self.handler._op_list("x.model", {"offset": -1}, {}, False)

        self.assertFalse(result["ok"])
        self.assertEqual(result["error"]["code"], 400)
        self.assertEqual(result["error"]["message"], "offset 无效")

    def test_invalid_group_paging_returns_bad_request(self):
        cases = [
            ("group_offset", -1),
            ("group_page_size", "bad"),
            ("group_limit", 0),
            ("group_sample_limit", "bad"),
        ]
        for field, value in cases:
            with self.subTest(field=field):
                result = self.handler._op_list("x.model", {field: value}, {}, False)
                self.assertFalse(result["ok"])
                self.assertEqual(result["error"]["code"], 400)
                self.assertEqual(result["error"]["message"], f"{field} 无效")

    def test_invalid_group_page_offsets_returns_bad_request(self):
        cases = [
            {"group:1": "bad"},
            {"": 0},
            "group%3A1:bad",
            "malformed",
            ["group:1", 0],
        ]
        for value in cases:
            with self.subTest(value=value):
                result = self.handler._op_list("x.model", {"group_page_offsets": value}, {}, False)
                self.assertFalse(result["ok"])
                self.assertEqual(result["error"]["code"], 400)
                self.assertEqual(result["error"]["message"], "group_page_offsets 无效")

    def test_read_rejects_invalid_ids(self):
        cases = [
            "bad",
            "[1, 'bad']",
            [1, "bad"],
            [0],
        ]
        for value in cases:
            with self.subTest(value=value):
                result = self.handler._op_read("x.model", {"ids": value}, {}, False)
                self.assertFalse(result["ok"])
                self.assertEqual(result["error"]["code"], 400)
                self.assertEqual(result["error"]["message"], "ids 无效")

    def test_write_rejects_invalid_ids(self):
        result = self.handler._op_write("x.model", {"ids": [1, "bad"], "vals": {"name": "A"}}, {}, False)

        self.assertFalse(result["ok"])
        self.assertEqual(result["error"]["code"], 400)
        self.assertEqual(result["error"]["message"], "ids 无效")

    def test_export_rejects_invalid_limit(self):
        result = self.handler._op_export_csv("x.model", {"limit": "bad"}, {}, False)

        self.assertFalse(result["ok"])
        self.assertEqual(result["error"]["code"], 400)
        self.assertEqual(result["error"]["message"], "limit 无效")

    def test_export_rejects_invalid_ids(self):
        result = self.handler._op_export_csv("x.model", {"ids": [1, "bad"]}, {}, False)

        self.assertFalse(result["ok"])
        self.assertEqual(result["error"]["code"], 400)
        self.assertEqual(result["error"]["message"], "ids 无效")

    def test_list_rejects_invalid_domain_raw(self):
        result = self.handler._op_list("x.model", {"domain_raw": "bad expression"}, {}, False)

        self.assertFalse(result["ok"])
        self.assertEqual(result["error"]["code"], 400)
        self.assertEqual(result["error"]["message"], "domain_raw 无效")

    def test_list_rejects_invalid_context_raw(self):
        result = self.handler._op_list("x.model", {"context_raw": "bad expression"}, {}, False)

        self.assertFalse(result["ok"])
        self.assertEqual(result["error"]["code"], 400)
        self.assertEqual(result["error"]["message"], "context_raw 无效")

    def test_safe_eval_runtime_supports_allowed_company_ids(self):
        module = _load_handler()

        def fake_safe_eval(value, runtime_env):
            if value == "[('company_id', '=', allowed_company_ids[0])]":
                return [("company_id", "=", runtime_env["allowed_company_ids"][0])]
            if value == "{'default_company_id': allowed_company_ids[0]}":
                return {"default_company_id": runtime_env["allowed_company_ids"][0]}
            if value == "{'search_default_project_id': context.get('default_project_id')}":
                return {"search_default_project_id": runtime_env["context"].get("default_project_id")}
            return value

        module.safe_eval = fake_safe_eval
        env = types.SimpleNamespace(uid=7, context={"allowed_company_ids": [42, 43], "default_project_id": 99}, user=None)
        handler = module.ApiDataHandler(env=env)

        self.assertEqual(
            handler._safe_eval_with_runtime("[('company_id', '=', allowed_company_ids[0])]"),
            [("company_id", "=", 42)],
        )
        self.assertEqual(
            handler._safe_eval_with_runtime("{'default_company_id': allowed_company_ids[0]}"),
            {"default_company_id": 42},
        )
        self.assertEqual(
            handler._safe_eval_with_runtime("{'search_default_project_id': context.get('default_project_id')}"),
            {"search_default_project_id": 99},
        )

    def test_request_context_preserves_env_lang_when_client_context_is_sparse(self):
        module = _load_handler()
        env = types.SimpleNamespace(uid=7, context={"lang": "zh_CN", "tz": "Asia/Shanghai"}, user=None)
        handler = module.ApiDataHandler(env=env)

        context = handler._request_context({"context": {"active_test": True}})

        self.assertEqual(context["lang"], "zh_CN")
        self.assertEqual(context["tz"], "Asia/Shanghai")
        self.assertIs(context["active_test"], True)

    def test_request_context_allows_explicit_client_lang_override(self):
        module = _load_handler()
        env = types.SimpleNamespace(uid=7, context={"lang": "zh_CN", "tz": "Asia/Shanghai"}, user=None)
        handler = module.ApiDataHandler(env=env)

        context = handler._request_context({"context": {"lang": "en_US", "active_test": False}})

        self.assertEqual(context["lang"], "en_US")
        self.assertEqual(context["tz"], "Asia/Shanghai")
        self.assertIs(context["active_test"], False)

    def test_list_rejects_invalid_fields_domain_and_group_by(self):
        cases = [
            ({"fields": 7}, "fields 无效"),
            ({"fields": "['name'"}, "fields 无效"),
            ({"domain": "bad"}, "domain 无效"),
            ({"domain": "{'bad': True}"}, "domain 无效"),
            ({"group_by": {"field": "state"}}, "group_by 无效"),
        ]
        for params, message in cases:
            with self.subTest(params=params):
                result = self.handler._op_list("x.model", params, {}, False)
                self.assertFalse(result["ok"])
                self.assertEqual(result["error"]["code"], 400)
                self.assertEqual(result["error"]["message"], message)

    def test_search_term_domain_skips_non_searchable_computed_fields(self):
        field = lambda field_type, store=True, search=None: types.SimpleNamespace(
            type=field_type,
            store=store,
            search=search,
        )
        env_model = types.SimpleNamespace(
            _rec_name="name",
            _fields={
                "name": field("char"),
                "computed_label": field("char", store=False),
                "computed_searchable": field("char", store=False, search=lambda *args: []),
                "partner_id": field("many2one"),
                "amount": field("float"),
            },
        )

        domain = self.handler._build_search_term_domain(
            env_model,
            "ABC",
            ["computed_label", "computed_searchable", "partner_id", "amount"],
        )

        self.assertIn(("name", "ilike", "ABC"), domain)
        self.assertIn(("computed_searchable", "ilike", "ABC"), domain)
        self.assertIn(("partner_id", "ilike", "ABC"), domain)
        self.assertNotIn(("computed_label", "ilike", "ABC"), domain)
        self.assertNotIn(("amount", "ilike", "ABC"), domain)

    def test_read_rejects_invalid_fields(self):
        result = self.handler._op_read("x.model", {"ids": [1], "fields": 7}, {}, False)

        self.assertFalse(result["ok"])
        self.assertEqual(result["error"]["code"], 400)
        self.assertEqual(result["error"]["message"], "fields 无效")

    def test_count_rejects_invalid_domain(self):
        result = self.handler._op_count("x.model", {"domain": "bad"}, {}, False)

        self.assertFalse(result["ok"])
        self.assertEqual(result["error"]["code"], 400)
        self.assertEqual(result["error"]["message"], "domain 无效")

    def test_export_rejects_invalid_fields_and_domain(self):
        cases = [
            ({"fields": 7}, "fields 无效"),
            ({"domain": "bad"}, "domain 无效"),
        ]
        for params, message in cases:
            with self.subTest(params=params):
                result = self.handler._op_export_csv("x.model", params, {}, False)
                self.assertFalse(result["ok"])
                self.assertEqual(result["error"]["code"], 400)
                self.assertEqual(result["error"]["message"], message)


if __name__ == "__main__":
    unittest.main()
