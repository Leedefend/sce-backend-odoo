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
