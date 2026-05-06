# -*- coding: utf-8 -*-
import importlib.util
import sys
import types
import unittest
from pathlib import Path


class _BaseIntentHandler:
    def __init__(self, env=None, params=None, payload=None, context=None):
        self.env = env
        self.params = params or {}
        self.payload = payload or {}
        self.context = context or {}


class _Model:
    _fields = {}

    def with_context(self, context):
        return self

    def check_access_rights(self, mode):
        return True


class _Field:
    def __init__(self, field_type="", comodel_name=""):
        self.type = field_type
        self.comodel_name = comodel_name


class _OnchangeModel(_Model):
    _fields = {"line_ids": _Field("one2many", "x.line")}
    _onchange_methods = {"line_ids": True}

    def onchange(self, values, changed_fields, field_onchange):
        return {
            "line_patches": [
                {
                    "field": "line_ids",
                    "row_id": "bad",
                    "patch": {"name": "A"},
                }
            ]
        }


class _LineModel(_Model):
    _fields = {"name": _Field("char")}


class _Env(dict):
    pass


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

    addons_mod = _install_module("odoo.addons")
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
        project_scope_denied_response=lambda meta: {"ok": False, "meta": meta},
        record_in_project_scope=lambda model, record_id, project_id: (True, {"applied": False}),
        selected_project_id_from_context=lambda params, context: None,
    )
    _install_module(
        "odoo.addons.smart_core.core.unified_page_contract_v2_assembler",
        assemble_unified_page_patch_v2=lambda data, action_id, request_id: {"meta": {"contractVersion": "2.0"}},
    )
    _install_module(
        "odoo.addons.smart_core.core.unified_page_contract_lite_preview",
        with_lite_preview_if_requested=lambda response, params, key: response,
    )
    reason_name = "odoo.addons.smart_core.utils.reason_codes"
    sys.modules.pop(reason_name, None)
    reason_spec = importlib.util.spec_from_file_location(reason_name, root / "utils" / "reason_codes.py")
    reason_module = importlib.util.module_from_spec(reason_spec)
    sys.modules[reason_name] = reason_module
    reason_spec.loader.exec_module(reason_module)

    module_name = "odoo.addons.smart_core.handlers.api_onchange"
    sys.modules.pop(module_name, None)
    spec = importlib.util.spec_from_file_location(module_name, root / "handlers" / "api_onchange.py")
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


class TestApiOnchangeRecordIdBoundaries(unittest.TestCase):
    def setUp(self):
        self.module = _load_handler()

    def test_invalid_record_id_returns_bad_request(self):
        handler = self.module.ApiOnchangeHandler(env=_Env({"x.model": _Model()}), params={"model": "x.model", "id": "bad"})

        result = handler.handle()

        self.assertFalse(result["ok"])
        self.assertEqual(result["code"], 400)
        self.assertEqual(result["error"]["message"], "id invalid")

    def test_missing_record_id_still_allows_new_record_onchange(self):
        handler = self.module.ApiOnchangeHandler(env=_Env({"x.model": _Model()}), params={"model": "x.model"})

        result = handler.handle()

        self.assertTrue(result["ok"])
        self.assertEqual(result["data"]["applied_fields"], [])

    def test_string_false_include_v2_patch_does_not_generate_v2_patch(self):
        handler = self.module.ApiOnchangeHandler(
            env=_Env({"x.model": _Model()}),
            params={"model": "x.model", "include_v2_patch": "false"},
        )

        result = handler.handle()

        self.assertTrue(result["ok"])
        self.assertNotIn("unified_page_patch_v2", result)

    def test_invalid_backend_line_row_id_does_not_break_normalization(self):
        env = _Env({"x.model": _OnchangeModel(), "x.line": _LineModel()})
        handler = self.module.ApiOnchangeHandler(
            env=env,
            params={"model": "x.model", "changed_fields": ["line_ids"]},
        )

        result = handler.handle()

        self.assertTrue(result["ok"])
        line_patch = result["data"]["line_patches"][0]
        self.assertEqual(line_patch["row_id"], 0)
        self.assertEqual(line_patch["row_state"], "create")
        self.assertEqual(line_patch["command_hint"], [0])


if __name__ == "__main__":
    unittest.main()
