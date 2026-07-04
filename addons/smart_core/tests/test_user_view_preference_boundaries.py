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


class _EmptyRecord:
    def __bool__(self):
        return False


class _Record:
    id = 5
    value_json = {"density": "compact"}

    def write(self, vals):
        self.value_json = vals.get("value_json", self.value_json)


class _PreferenceModel:
    def __init__(self):
        self.sudo_calls = 0
        self.search_domains = []
        self.created_vals = None

    def sudo(self):
        self.sudo_calls += 1
        return self

    def normalize_preference_key(self, value):
        key = str(value or "list_columns").strip() or "list_columns"
        return key if key == "list_columns" else "list_columns"

    def build_scope_key(self, *, preference_key, view_type, action_id, model_name):
        target = f"action:{action_id}" if action_id else f"model:{model_name or 'unknown'}"
        return f"{preference_key}:{view_type}:{target}"

    def search(self, domain, limit=None):
        self.search_domains.append(domain)
        return _EmptyRecord()

    def create(self, vals):
        self.created_vals = vals
        return _Record()


class _Env(dict):
    uid = 42
    context = {}


class _ContractService:
    def with_context(self, _ctx):
        return self

    def generate_contract(self, **_kwargs):
        return {
            "data": {
                "list_profile": {
                    "columns": ["name", "manager_id", "business_nature"],
                    "fact_columns": ["name", "business_nature"],
                    "preference_policy": {
                        "allow_visibility": True,
                        "allow_order": False,
                        "allow_width": False,
                        "locked_columns": ["name"],
                        "must_request_columns": ["business_nature"],
                    },
                }
            }
        }


def _load_handler():
    root = Path(__file__).resolve().parents[1]
    addons_mod = types.ModuleType("odoo.addons")
    smart_core_mod = types.ModuleType("odoo.addons.smart_core")
    handlers_mod = types.ModuleType("odoo.addons.smart_core.handlers")
    core_mod = types.ModuleType("odoo.addons.smart_core.core")
    smart_core_mod.__path__ = [str(root)]
    handlers_mod.__path__ = [str(root / "handlers")]
    core_mod.__path__ = [str(root / "core")]
    base_mod = types.ModuleType("odoo.addons.smart_core.core.base_handler")
    base_mod.BaseIntentHandler = _BaseIntentHandler
    sys.modules.update(
        {
            "odoo.addons": addons_mod,
            "odoo.addons.smart_core": smart_core_mod,
            "odoo.addons.smart_core.handlers": handlers_mod,
            "odoo.addons.smart_core.core": core_mod,
            "odoo.addons.smart_core.core.base_handler": base_mod,
        }
    )
    module_name = "odoo.addons.smart_core.handlers.user_view_preference"
    sys.modules.pop(module_name, None)
    spec = importlib.util.spec_from_file_location(module_name, root / "handlers" / "user_view_preference.py")
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


class TestUserViewPreferenceBoundaries(unittest.TestCase):
    def test_get_uses_current_user_model_without_sudo(self):
        module = _load_handler()
        Preference = _PreferenceModel()
        env = _Env({"sc.user.view.preference": Preference})
        handler = module.UserViewPreferenceGetHandler(env=env, payload={"model": "x.model"})

        result = handler.handle()

        self.assertTrue(result["ok"])
        self.assertEqual(Preference.sudo_calls, 0)
        self.assertIn(("user_id", "=", 42), Preference.search_domains[0])

    def test_set_uses_current_user_model_without_sudo(self):
        module = _load_handler()
        Preference = _PreferenceModel()
        env = _Env({"sc.user.view.preference": Preference})
        handler = module.UserViewPreferenceSetHandler(
            env=env,
            payload={"model": "x.model", "preference": {"density": "compact"}},
        )

        result = handler.handle()

        self.assertTrue(result["ok"])
        self.assertEqual(Preference.sudo_calls, 0)
        self.assertEqual(Preference.created_vals["user_id"], 42)
        self.assertEqual(
            Preference.created_vals["value_json"],
            {"visible_columns": [], "hidden_columns": [], "column_order": [], "column_widths": {}},
        )

    def test_get_rejects_invalid_action_id(self):
        module = _load_handler()
        Preference = _PreferenceModel()
        env = _Env({"sc.user.view.preference": Preference})
        handler = module.UserViewPreferenceGetHandler(env=env, payload={"action_id": "bad"})

        result = handler.handle()

        self.assertFalse(result["ok"])
        self.assertEqual(result["code"], 400)
        self.assertEqual(result["error"]["message"], "action_id 无效")
        self.assertEqual(Preference.search_domains, [])

    def test_set_rejects_invalid_action_id(self):
        module = _load_handler()
        Preference = _PreferenceModel()
        env = _Env({"sc.user.view.preference": Preference})
        handler = module.UserViewPreferenceSetHandler(env=env, payload={"action_id": "bad", "preference": {}})

        result = handler.handle()

        self.assertFalse(result["ok"])
        self.assertEqual(result["code"], 400)
        self.assertEqual(result["error"]["message"], "action_id 无效")
        self.assertIsNone(Preference.created_vals)

    def test_get_rejects_invalid_params_shape(self):
        module = _load_handler()
        Preference = _PreferenceModel()
        env = _Env({"sc.user.view.preference": Preference})
        handler = module.UserViewPreferenceGetHandler(env=env, payload=["model", "x.model"])

        result = handler.handle()

        self.assertFalse(result["ok"])
        self.assertEqual(result["code"], 400)
        self.assertEqual(result["error"]["message"], "params 无效")
        self.assertEqual(Preference.search_domains, [])

    def test_get_rejects_invalid_view_type(self):
        module = _load_handler()
        Preference = _PreferenceModel()
        env = _Env({"sc.user.view.preference": Preference})
        handler = module.UserViewPreferenceGetHandler(env=env, payload={"model": "x.model", "view_type": ["list"]})

        result = handler.handle()

        self.assertFalse(result["ok"])
        self.assertEqual(result["code"], 400)
        self.assertEqual(result["error"]["message"], "view_type 无效")
        self.assertEqual(Preference.search_domains, [])

    def test_set_rejects_invalid_model(self):
        module = _load_handler()
        Preference = _PreferenceModel()
        env = _Env({"sc.user.view.preference": Preference})
        handler = module.UserViewPreferenceSetHandler(env=env, payload={"model": ["x.model"], "preference": {}})

        result = handler.handle()

        self.assertFalse(result["ok"])
        self.assertEqual(result["code"], 400)
        self.assertEqual(result["error"]["message"], "model 无效")
        self.assertIsNone(Preference.created_vals)

    def test_set_sanitizes_list_column_payload(self):
        module = _load_handler()
        Preference = _PreferenceModel()
        env = _Env({"sc.user.view.preference": Preference})
        handler = module.UserViewPreferenceSetHandler(
            env=env,
            payload={
                "model": "x.model",
                "preference_key": "list_columns",
                "preference": {
                    "visible_columns": ["name", "name", "  ", None, "manager_id"],
                    "hidden_columns": ["manager_id", "business_nature", "", "business_nature"],
                    "column_order": ["business_nature", "unknown", "name"],
                    "column_widths": {"name": 20, "manager_id": 900, "unknown": 300, "business_nature": "320"},
                    "random_noise": True,
                },
            },
        )

        result = handler.handle()

        self.assertTrue(result["ok"])
        self.assertEqual(
            Preference.created_vals["value_json"],
            {
                "visible_columns": ["name", "manager_id"],
                "hidden_columns": ["business_nature"],
                "column_order": ["business_nature", "name"],
                "column_widths": {"name": 80, "manager_id": 640, "business_nature": 320},
            },
        )

    def test_set_enforces_contract_preference_policy(self):
        module = _load_handler()
        Preference = _PreferenceModel()
        env = _Env({"sc.user.view.preference": Preference, "app.contract.service": _ContractService()})
        handler = module.UserViewPreferenceSetHandler(
            env=env,
            payload={
                "model": "project.project",
                "action_id": 99999,
                "preference_key": "list_columns",
                "preference": {
                    "visible_columns": ["name"],
                    "hidden_columns": ["name", "business_nature", "manager_id"],
                    "column_order": ["manager_id", "name"],
                    "column_widths": {"name": 160, "manager_id": 220},
                },
            },
        )

        result = handler.handle()

        self.assertTrue(result["ok"])
        self.assertEqual(
            Preference.created_vals["value_json"],
            {
                "visible_columns": ["name"],
                "hidden_columns": ["business_nature", "manager_id"],
                "column_order": [],
                "column_widths": {},
            },
        )

    def test_formal_list_allows_user_display_preference(self):
        module = _load_handler()
        Preference = _PreferenceModel()
        env = _Env({"sc.user.view.preference": Preference, "app.contract.service": _ContractService()})
        handler = module.UserViewPreferenceSetHandler(
            env=env,
            payload={
                "model": "project.project",
                "action_id": 506,
                "preference_key": "list_columns",
                "preference": {
                    "visible_columns": ["name"],
                    "hidden_columns": ["business_nature", "manager_id"],
                    "column_order": ["manager_id", "name"],
                    "column_widths": {"name": 160, "manager_id": 220},
                },
            },
        )

        result = handler.handle()

        self.assertTrue(result["ok"])
        self.assertEqual(
            Preference.created_vals["value_json"],
            {
                "visible_columns": ["name"],
                "hidden_columns": ["business_nature", "manager_id"],
                "column_order": [],
                "column_widths": {},
            },
        )


if __name__ == "__main__":
    unittest.main()
