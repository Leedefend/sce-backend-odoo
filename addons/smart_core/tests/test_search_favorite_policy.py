# -*- coding: utf-8 -*-
import importlib.util
import sys
import types
import unittest
from pathlib import Path


def _load_policy():
    root = Path(__file__).resolve().parents[1]
    addons_mod = types.ModuleType("odoo.addons")
    smart_core_mod = types.ModuleType("odoo.addons.smart_core")
    core_mod = types.ModuleType("odoo.addons.smart_core.core")
    smart_core_mod.__path__ = [str(root)]
    core_mod.__path__ = [str(root / "core")]
    sys.modules.update(
        {
            "odoo.addons": addons_mod,
            "odoo.addons.smart_core": smart_core_mod,
            "odoo.addons.smart_core.core": core_mod,
        }
    )
    module_name = "odoo.addons.smart_core.core.search_favorite_policy"
    sys.modules.pop(module_name, None)
    spec = importlib.util.spec_from_file_location(module_name, root / "core" / "search_favorite_policy.py")
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


class TestSearchFavoritePolicy(unittest.TestCase):
    def setUp(self):
        self.policy = _load_policy()

    def test_client_shared_flag_is_detectable_for_audit(self):
        self.assertTrue(self.policy.client_requested_shared_favorite({"is_shared": True}))
        self.assertFalse(self.policy.client_requested_shared_favorite({"is_shared": "true"}))

    def test_search_favorite_never_creates_shared_filter_from_client_input(self):
        self.assertFalse(self.policy.resolve_search_favorite_shared({"is_shared": True}))
        self.assertFalse(self.policy.resolve_search_favorite_shared({}))


if __name__ == "__main__":
    unittest.main()
