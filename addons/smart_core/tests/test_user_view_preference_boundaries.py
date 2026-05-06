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
        return str(value or "default").strip() or "default"

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


if __name__ == "__main__":
    unittest.main()
