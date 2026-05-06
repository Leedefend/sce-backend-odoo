# -*- coding: utf-8 -*-
import importlib.util
import sys
import types
import unittest
from pathlib import Path


class _BaseIntentHandler:
    def __init__(self, env=None, params=None, context=None):
        self.env = env
        self.params = params or {}
        self.context = context or {}


class _Action:
    _name = "ir.actions.server"
    id = 7

    def __init__(self, model):
        self.model_id = types.SimpleNamespace(model=model)
        self.run_calls = 0

    def exists(self):
        return self

    def sudo(self):
        return self

    def with_context(self, context):
        return self

    def run(self):
        self.run_calls += 1
        return {}


class _ActionModel:
    def __init__(self, action):
        self.action = action

    def sudo(self):
        return self

    def browse(self, action_id):
        return self.action


class _Env(dict):
    pass


def _load_handler():
    root = Path(__file__).resolve().parents[1]
    odoo_mod = types.ModuleType("odoo")
    odoo_mod.fields = types.SimpleNamespace(Date=types.SimpleNamespace(context_today=lambda user: "2026-05-07"))
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
    project_mod.project_scope_denied_response = lambda meta: {"ok": False, "meta": meta}
    project_mod.record_in_project_scope = lambda model, record_id, project_id: (True, {"applied": False})
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

    module_name = "odoo.addons.smart_core.handlers.execute_button"
    sys.modules.pop(module_name, None)
    spec = importlib.util.spec_from_file_location(module_name, root / "handlers" / "execute_button.py")
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


class TestExecuteButtonServerActionBoundaries(unittest.TestCase):
    def test_server_action_model_must_match_active_model(self):
        module = _load_handler()
        action = _Action("other.model")
        env = _Env({"ir.actions.server": _ActionModel(action)})
        handler = module.ExecuteButtonHandler(env=env, context={})

        result = handler._run_server_action({"server_action_id": 7}, model="x.model", res_ids=[1])

        self.assertIsNone(result)
        self.assertEqual(action.run_calls, 0)

    def test_matching_server_action_can_run(self):
        module = _load_handler()
        action = _Action("x.model")
        env = _Env({"ir.actions.server": _ActionModel(action)})
        handler = module.ExecuteButtonHandler(env=env, context={})

        result = handler._run_server_action({"server_action_id": 7}, model="x.model", res_ids=[1])

        self.assertTrue(result["ok"])
        self.assertEqual(action.run_calls, 1)

    def test_invalid_record_id_returns_bad_request(self):
        module = _load_handler()
        handler = module.ExecuteButtonHandler(
            env=_Env({}),
            params={"model": "x.model", "record_id": ["bad"], "button": {"name": "action_confirm"}},
            context={"trace_id": "trace"},
        )

        result = handler.handle()

        self.assertFalse(result["ok"])
        self.assertEqual(result["code"], 400)
        self.assertEqual(result["error"]["message"], "record_id 无效")
        self.assertEqual(result["meta"]["trace_id"], "trace")


if __name__ == "__main__":
    unittest.main()
