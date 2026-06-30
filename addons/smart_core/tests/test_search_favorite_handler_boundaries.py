# -*- coding: utf-8 -*-
import importlib.util
import json
import sys
import types
import unittest
from datetime import date
from decimal import Decimal
from pathlib import Path


class _BaseIntentHandler:
    def __init__(self, env=None, params=None, payload=None, context=None):
        self.env = env
        self.params = params or {}
        self.payload = payload or {}
        self.context = context or {}


class _Model:
    def check_access_rights(self, mode):
        self.checked_mode = mode


class _Record:
    id = 17
    name = "Favorite"

    def write(self, vals):
        self.vals = vals


class _EmptyRecord:
    def __bool__(self):
        return False


class _FilterModel:
    def __init__(self):
        self.created_vals = None
        self.search_domains = []

    def sudo(self):
        return self

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
    odoo_mod = types.ModuleType("odoo")
    exc_mod = types.ModuleType("odoo.exceptions")
    exc_mod.AccessError = type("AccessError", (Exception,), {})
    odoo_mod.exceptions = exc_mod

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
            "odoo": odoo_mod,
            "odoo.exceptions": exc_mod,
            "odoo.addons": addons_mod,
            "odoo.addons.smart_core": smart_core_mod,
            "odoo.addons.smart_core.handlers": handlers_mod,
            "odoo.addons.smart_core.core": core_mod,
            "odoo.addons.smart_core.core.base_handler": base_mod,
        }
    )

    policy_name = "odoo.addons.smart_core.core.search_favorite_policy"
    sys.modules.pop(policy_name, None)
    policy_spec = importlib.util.spec_from_file_location(policy_name, root / "core" / "search_favorite_policy.py")
    policy_module = importlib.util.module_from_spec(policy_spec)
    sys.modules[policy_name] = policy_module
    policy_spec.loader.exec_module(policy_module)

    module_name = "odoo.addons.smart_core.handlers.search_favorite_set"
    sys.modules.pop(module_name, None)
    spec = importlib.util.spec_from_file_location(module_name, root / "handlers" / "search_favorite_set.py")
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


class TestSearchFavoriteHandlerBoundaries(unittest.TestCase):
    def test_shared_request_writes_current_user_filter(self):
        module = _load_handler()
        filters = _FilterModel()
        env = _Env({"x.model": _Model(), "ir.filters": filters})
        handler = module.SearchFavoriteSetHandler(
            env=env,
            payload={"model": "x.model", "name": "Mine", "is_shared": True},
        )

        result = handler.handle()

        self.assertTrue(result["ok"])
        self.assertFalse(result["data"]["is_shared"])
        self.assertEqual(filters.created_vals["user_id"], 42)
        self.assertIn(("user_id", "=", 42), filters.search_domains[0])

    def test_invalid_action_id_returns_bad_request_before_filter_lookup(self):
        module = _load_handler()
        filters = _FilterModel()
        env = _Env({"x.model": _Model(), "ir.filters": filters})
        handler = module.SearchFavoriteSetHandler(
            env=env,
            payload={"model": "x.model", "name": "Mine", "action_id": "bad"},
        )

        result = handler.handle()

        self.assertFalse(result["ok"])
        self.assertEqual(result["error"]["message"], "action_id 无效")
        self.assertEqual(filters.search_domains, [])

    def test_serializes_projection_scalars_in_domain_and_context(self):
        module = _load_handler()
        filters = _FilterModel()
        env = _Env({"x.model": _Model(), "ir.filters": filters})
        handler = module.SearchFavoriteSetHandler(
            env=env,
            payload={
                "model": "x.model",
                "name": "Mine",
                "domain": [["date", "=", date(2026, 6, 30)]],
                "context": {"amount": Decimal("12.30")},
            },
        )

        result = handler.handle()

        self.assertTrue(result["ok"])
        self.assertEqual(json.loads(filters.created_vals["domain"]), [["date", "=", "2026-06-30"]])
        self.assertEqual(json.loads(filters.created_vals["context"]), {"amount": "12.30"})

    def test_invalid_params_shape_returns_bad_request(self):
        module = _load_handler()
        filters = _FilterModel()
        env = _Env({"x.model": _Model(), "ir.filters": filters})
        handler = module.SearchFavoriteSetHandler(env=env, payload=["model", "x.model"])

        result = handler.handle()

        self.assertFalse(result["ok"])
        self.assertEqual(result["error"]["message"], "params 无效")
        self.assertEqual(filters.search_domains, [])

    def test_invalid_name_returns_bad_request_before_filter_lookup(self):
        module = _load_handler()
        filters = _FilterModel()
        env = _Env({"x.model": _Model(), "ir.filters": filters})
        handler = module.SearchFavoriteSetHandler(env=env, payload={"model": "x.model", "name": ["Mine"]})

        result = handler.handle()

        self.assertFalse(result["ok"])
        self.assertEqual(result["error"]["message"], "name 无效")
        self.assertEqual(filters.search_domains, [])

    def test_invalid_sort_returns_bad_request_before_filter_lookup(self):
        module = _load_handler()
        filters = _FilterModel()
        env = _Env({"x.model": _Model(), "ir.filters": filters})
        handler = module.SearchFavoriteSetHandler(
            env=env,
            payload={"model": "x.model", "name": "Mine", "sort": ["name"]},
        )

        result = handler.handle()

        self.assertFalse(result["ok"])
        self.assertEqual(result["error"]["message"], "sort 无效")
        self.assertEqual(filters.search_domains, [])


if __name__ == "__main__":
    unittest.main()
