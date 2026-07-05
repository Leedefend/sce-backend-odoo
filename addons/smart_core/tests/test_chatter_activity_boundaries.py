# -*- coding: utf-8 -*-
import importlib.util
import sys
import types
import unittest
from pathlib import Path


class _BaseIntentHandler:
    def __init__(self, env=None, params=None, context=None):
        self.env = env or {}
        self.params = params or {}
        self.context = context or {}


class _Env(dict):
    user = types.SimpleNamespace(id=9)


def _load_handler(handler_name="chatter_activity_schedule"):
    root = Path(__file__).resolve().parents[1]
    odoo_mod = types.ModuleType("odoo")
    fields_mod = types.SimpleNamespace(Date=types.SimpleNamespace(context_today=lambda user: "2026-05-07"))
    odoo_mod.fields = fields_mod
    exc_mod = types.ModuleType("odoo.exceptions")
    exc_mod.AccessError = type("AccessError", (Exception,), {})
    exc_mod.UserError = type("UserError", (Exception,), {})
    odoo_mod.exceptions = exc_mod

    addons_mod = types.ModuleType("odoo.addons")
    smart_core_mod = types.ModuleType("odoo.addons.smart_core")
    handlers_mod = types.ModuleType("odoo.addons.smart_core.handlers")
    core_mod = types.ModuleType("odoo.addons.smart_core.core")
    utils_mod = types.ModuleType("odoo.addons.smart_core.utils")
    smart_core_mod.__path__ = [str(root)]
    handlers_mod.__path__ = [str(root / "handlers")]
    core_mod.__path__ = [str(root / "core")]
    utils_mod.__path__ = [str(root / "utils")]

    base_mod = types.ModuleType("odoo.addons.smart_core.core.base_handler")
    base_mod.BaseIntentHandler = _BaseIntentHandler
    project_mod = types.ModuleType("odoo.addons.smart_core.core.project_context")
    project_mod.record_scope_denied_response = lambda meta, message="": {"ok": False, "meta": meta, "message": message}
    project_mod.project_scope_denied_response = lambda meta: {"ok": False, "meta": meta}
    project_mod.record_in_business_scope = lambda model, record_id, params=None, context=None: (True, {"applied": False})
    project_mod.record_in_project_scope = lambda model, record_id, project_id: (True, {"applied": False})
    project_mod.selected_record_context_id_from_context = lambda params, context: None
    project_mod.selected_project_id_from_context = lambda params, context: None

    sys.modules.update(
        {
            "odoo": odoo_mod,
            "odoo.exceptions": exc_mod,
            "odoo.addons": addons_mod,
            "odoo.addons.smart_core": smart_core_mod,
            "odoo.addons.smart_core.handlers": handlers_mod,
            "odoo.addons.smart_core.core": core_mod,
            "odoo.addons.smart_core.utils": utils_mod,
            "odoo.addons.smart_core.core.base_handler": base_mod,
            "odoo.addons.smart_core.core.project_context": project_mod,
        }
    )

    reason_name = "odoo.addons.smart_core.utils.reason_codes"
    sys.modules.pop(reason_name, None)
    reason_spec = importlib.util.spec_from_file_location(reason_name, root / "utils" / "reason_codes.py")
    reason_module = importlib.util.module_from_spec(reason_spec)
    sys.modules[reason_name] = reason_module
    reason_spec.loader.exec_module(reason_module)

    module_name = f"odoo.addons.smart_core.handlers.{handler_name}"
    sys.modules.pop(module_name, None)
    spec = importlib.util.spec_from_file_location(module_name, root / "handlers" / f"{handler_name}.py")
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


class TestChatterActivityBoundaries(unittest.TestCase):
    def test_invalid_res_id_returns_user_error(self):
        module = _load_handler()
        handler = module.ChatterActivityScheduleHandler(
            env=_Env({"x.model": object()}),
            params={"model": "x.model", "res_id": "bad", "summary": "Follow up"},
        )

        result = handler.handle()

        self.assertFalse(result["ok"])
        self.assertEqual(result["code"], 400)
        self.assertEqual(result["error"]["reason_code"], "USER_ERROR")
        self.assertEqual(result["error"]["message"], "res_id 无效")

    def test_non_positive_res_id_returns_user_error(self):
        module = _load_handler()
        handler = module.ChatterActivityScheduleHandler(
            env=_Env({"x.model": object()}),
            params={"model": "x.model", "res_id": 0, "summary": "Follow up"},
        )

        result = handler.handle()

        self.assertFalse(result["ok"])
        self.assertEqual(result["code"], 400)
        self.assertEqual(result["error"]["reason_code"], "USER_ERROR")
        self.assertEqual(result["error"]["message"], "res_id 无效")

    def test_invalid_user_id_returns_user_error(self):
        module = _load_handler()
        handler = module.ChatterActivityScheduleHandler(
            env=_Env({"x.model": object()}),
            params={"model": "x.model", "res_id": 3, "summary": "Follow up", "user_id": "bad"},
        )

        result = handler.handle()

        self.assertFalse(result["ok"])
        self.assertEqual(result["code"], 400)
        self.assertEqual(result["error"]["reason_code"], "USER_ERROR")
        self.assertEqual(result["error"]["message"], "user_id 无效")

    def test_update_invalid_activity_id_returns_user_error(self):
        module = _load_handler("chatter_activity_update")
        handler = module.ChatterActivityUpdateHandler(
            env=_Env({"x.model": object()}),
            params={"model": "x.model", "res_id": 3, "activity_id": "bad", "action": "done"},
        )

        result = handler.handle()

        self.assertFalse(result["ok"])
        self.assertEqual(result["code"], 400)
        self.assertEqual(result["error"]["reason_code"], "USER_ERROR")
        self.assertEqual(result["error"]["message"], "activity_id 无效")


if __name__ == "__main__":
    unittest.main()
