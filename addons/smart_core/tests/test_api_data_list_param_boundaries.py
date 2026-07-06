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
        apply_business_scope_domain=lambda env_model, domain, params=None, context=None: (domain, {"applied": False}),
        apply_project_scope_domain=lambda env_model, domain, project_id: (domain, {"applied": False}),
        selected_record_context_id_from_context=lambda params, context: None,
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

    def test_search_term_param_accepts_legacy_aliases(self):
        self.assertEqual(self.handler._read_search_term_param({"searchTerm": " 绵阳 "}), "绵阳")
        self.assertEqual(self.handler._read_search_term_param({"search": " 项目 "}), "项目")
        self.assertEqual(self.handler._read_search_term_param({"keyword": " 保证金 "}), "保证金")
        self.assertEqual(self.handler._read_search_term_param({"q": " 收款 "}), "收款")
        self.assertEqual(
            self.handler._read_search_term_param({"search_term": "正式", "search": "通用参数", "searchTerm": "旧参数"}),
            "正式",
        )

    def test_list_applies_search_term_alias_to_domain(self):
        field = lambda field_type, store=True, groups="": types.SimpleNamespace(
            type=field_type,
            store=store,
            groups=groups,
        )

        class _Recordset:
            def read(self, fields):
                return [{"id": 1, "name": "绵阳项目"}]

        class _Model:
            _name = "x.model"
            _rec_name = "name"

            def __init__(self):
                self.env = None
                self._fields = {
                    "id": field("integer"),
                    "name": field("char"),
                }
                self.search_domains = []

            def with_context(self, ctx):
                self.context = ctx
                return self

            def search(self, domain, order=None, limit=None, offset=0):
                self.search_domains.append(list(domain or []))
                return _Recordset()

            def search_count(self, domain):
                return 1

            def read_group(self, domain, fields, groupby, **kwargs):
                return []

        class _Env(dict):
            pass

        user = types.SimpleNamespace(has_group=lambda group: True)
        env = _Env()
        env.user = user
        env.context = {}
        model = _Model()
        model.env = env
        env["x.model"] = model
        handler = _load_handler().ApiDataHandler(env=env)

        result = handler._op_list("x.model", {"searchTerm": "绵阳", "need_total": True}, {}, False)

        self.assertIsInstance(result, tuple)
        self.assertIn(("name", "ilike", "绵阳"), model.search_domains[0])

    def test_count_applies_search_term_alias_to_domain(self):
        field = lambda field_type, store=True, groups="": types.SimpleNamespace(
            type=field_type,
            store=store,
            groups=groups,
        )

        class _Model:
            _name = "x.model"
            _rec_name = "name"

            def __init__(self):
                self.env = None
                self._fields = {"id": field("integer"), "name": field("char")}
                self.count_domains = []

            def with_context(self, ctx):
                self.context = ctx
                return self

            def search_count(self, domain):
                self.count_domains.append(list(domain or []))
                return 7

        class _Env(dict):
            pass

        user = types.SimpleNamespace(has_group=lambda group: True)
        env = _Env()
        env.user = user
        env.context = {}
        model = _Model()
        model.env = env
        env["x.model"] = model
        handler = _load_handler().ApiDataHandler(env=env)

        data, meta = handler._op_count("x.model", {"keyword": "绵阳"}, {}, False)

        self.assertEqual(data["total"], 7)
        self.assertTrue(meta["search_term_applied"])
        self.assertIn(("name", "ilike", "绵阳"), model.count_domains[0])

    def test_export_csv_applies_search_term_alias_to_domain(self):
        field = lambda field_type, store=True, groups="": types.SimpleNamespace(
            type=field_type,
            store=store,
            groups=groups,
        )

        class _Recordset:
            def read(self, fields):
                return [{"id": 1, "name": "绵阳项目"}]

        class _Model:
            _name = "x.model"
            _rec_name = "name"

            def __init__(self):
                self.env = None
                self._fields = {"id": field("integer"), "name": field("char")}
                self.search_domains = []

            def with_context(self, ctx):
                self.context = ctx
                return self

            def search(self, domain, order=None, limit=None):
                self.search_domains.append(list(domain or []))
                return _Recordset()

        class _Env(dict):
            pass

        user = types.SimpleNamespace(has_group=lambda group: True)
        env = _Env()
        env.user = user
        env.context = {}
        model = _Model()
        model.env = env
        env["x.model"] = model
        handler = _load_handler().ApiDataHandler(env=env)

        data, meta = handler._op_export_csv("x.model", {"q": "绵阳", "fields": ["id", "name"]}, {}, False)

        self.assertEqual(data["count"], 1)
        self.assertEqual(meta["count"], 1)
        self.assertIn(("name", "ilike", "绵阳"), model.search_domains[0])

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

    def test_search_term_domain_includes_search_view_fields_for_projection_lists(self):
        field = lambda field_type, store=True, search=None, groups="": types.SimpleNamespace(
            type=field_type,
            store=store,
            search=search,
            groups=groups,
        )
        user = types.SimpleNamespace(has_group=lambda group: group == "allowed.group")
        env_model = types.SimpleNamespace(
            _name="x.receipt",
            _rec_name="name",
            env=types.SimpleNamespace(user=user),
            _fields={
                "name": field("char"),
                "p1_visible_project": field("char", store=False),
                "legacy_project_name": field("char"),
                "project_id": field("many2one"),
                "restricted_note": field("char", groups="blocked.group"),
            },
        )
        self.handler._search_view_field_names = lambda model: [
            "legacy_project_name",
            "project_id",
            "restricted_note",
        ]

        domain = self.handler._build_search_term_domain(
            env_model,
            "绵阳",
            ["p1_visible_project"],
        )

        self.assertIn(("legacy_project_name", "ilike", "绵阳"), domain)
        self.assertIn(("project_id", "ilike", "绵阳"), domain)
        self.assertNotIn(("p1_visible_project", "ilike", "绵阳"), domain)
        self.assertNotIn(("restricted_note", "ilike", "绵阳"), domain)

    def test_search_term_domain_includes_extension_projection_source_fields(self):
        field = lambda field_type, store=True, search=None, groups="": types.SimpleNamespace(
            type=field_type,
            store=store,
            search=search,
            groups=groups,
        )
        user = types.SimpleNamespace(has_group=lambda group: True)
        env_model = types.SimpleNamespace(
            _name="x.guarantee",
            _rec_name="",
            env=types.SimpleNamespace(user=user),
            _fields={
                "p1_visible_remark": field("char", store=False),
                "remark": field("char"),
                "amount": field("monetary"),
            },
        )
        self.handler._extension_search_field_names = lambda model: ["remark", "amount"]

        domain = self.handler._build_search_term_domain(
            env_model,
            "保证金",
            ["p1_visible_remark"],
        )

        self.assertIn(("remark", "ilike", "保证金"), domain)
        self.assertNotIn(("p1_visible_remark", "ilike", "保证金"), domain)
        self.assertNotIn(("amount", "ilike", "保证金"), domain)

    def test_search_term_domain_falls_back_to_model_text_fields_when_projection_has_no_source(self):
        field = lambda field_type, store=True, search=None, groups="": types.SimpleNamespace(
            type=field_type,
            store=store,
            search=search,
            groups=groups,
        )
        user = types.SimpleNamespace(has_group=lambda group: group == "allowed.group")
        env_model = types.SimpleNamespace(
            _name="x.receipt",
            _rec_name="",
            env=types.SimpleNamespace(user=user),
            _fields={
                "id": field("integer"),
                "p1_visible_project": field("char", store=False),
                "project_name": field("char"),
                "remark": field("text"),
                "restricted_note": field("char", groups="blocked.group"),
                "amount": field("monetary"),
            },
        )
        self.handler._search_view_field_names = lambda model: []
        self.handler._extension_search_field_names = lambda model: []

        domain = self.handler._build_search_term_domain(
            env_model,
            "绵阳",
            ["p1_visible_project"],
        )

        self.assertIn(("project_name", "ilike", "绵阳"), domain)
        self.assertIn(("remark", "ilike", "绵阳"), domain)
        self.assertNotIn(("p1_visible_project", "ilike", "绵阳"), domain)
        self.assertNotIn(("restricted_note", "ilike", "绵阳"), domain)
        self.assertNotIn(("amount", "ilike", "绵阳"), domain)
        self.assertNotEqual(domain, [("id", "=", 0)])

    def test_search_term_domain_includes_many2one_display_source_fields(self):
        field = lambda field_type, store=True, search=None, groups="", comodel_name="": types.SimpleNamespace(
            type=field_type,
            store=store,
            search=search,
            groups=groups,
            comodel_name=comodel_name,
        )
        user = types.SimpleNamespace(has_group=lambda group: True)
        contract_model = types.SimpleNamespace(
            _rec_name="name",
            _fields={
                "name": field("char"),
                "legacy_visible_title": field("char"),
                "amount_total": field("float"),
            },
        )

        class Env(dict):
            pass

        env = Env({"construction.contract": contract_model})
        env.user = user
        env_model = types.SimpleNamespace(
            _name="payment.request",
            _rec_name="name",
            env=env,
            _fields={
                "name": field("char"),
                "contract_id": field("many2one", comodel_name="construction.contract"),
            },
        )

        domain = self.handler._build_search_term_domain(
            env_model,
            "场外墙",
            ["contract_id"],
        )

        self.assertIn(("contract_id", "ilike", "场外墙"), domain)
        self.assertIn(("contract_id.name", "ilike", "场外墙"), domain)
        self.assertIn(("contract_id.legacy_visible_title", "ilike", "场外墙"), domain)
        self.assertNotIn(("contract_id.amount_total", "ilike", "场外墙"), domain)

    def test_python_order_sorts_date_text_chronologically(self):
        rows = [
            {"apply_date": "2024-10-01"},
            {"apply_date": "2024-2-01"},
            {"apply_date": ""},
            {"apply_date": "2023年12月31日"},
        ]

        asc = self.handler._sort_rows_by_python_clause(rows, "apply_date", "asc")
        desc = self.handler._sort_rows_by_python_clause(rows, "apply_date", "desc")

        self.assertEqual([row["apply_date"] for row in asc], ["2023年12月31日", "2024-2-01", "2024-10-01", ""])
        self.assertEqual([row["apply_date"] for row in desc], ["2024-10-01", "2024-2-01", "2023年12月31日", ""])

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
