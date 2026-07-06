# -*- coding: utf-8 -*-
from __future__ import annotations

import importlib.util
import sys
import types
import unittest
from pathlib import Path


SMART_CORE_DIR = Path(__file__).resolve().parents[1]


def _load_delivery_menu_defaults():
    sys.modules.setdefault("odoo", types.ModuleType("odoo"))
    sys.modules.setdefault("odoo.addons", types.ModuleType("odoo.addons"))
    smart_core_pkg = sys.modules.setdefault("odoo.addons.smart_core", types.ModuleType("odoo.addons.smart_core"))
    smart_core_pkg.__path__ = [str(SMART_CORE_DIR)]
    core_pkg = sys.modules.setdefault("odoo.addons.smart_core.core", types.ModuleType("odoo.addons.smart_core.core"))
    core_pkg.__path__ = [str(SMART_CORE_DIR / "core")]
    for module_name in (
        "odoo.addons.smart_core.core.source_authority",
        "odoo.addons.smart_core.core.delivery_menu_defaults",
    ):
        sys.modules.pop(module_name, None)
    source_spec = importlib.util.spec_from_file_location(
        "odoo.addons.smart_core.core.source_authority",
        SMART_CORE_DIR / "core" / "source_authority.py",
    )
    source_module = importlib.util.module_from_spec(source_spec)
    assert source_spec and source_spec.loader
    sys.modules["odoo.addons.smart_core.core.source_authority"] = source_module
    source_spec.loader.exec_module(source_module)
    spec = importlib.util.spec_from_file_location(
        "odoo.addons.smart_core.core.delivery_menu_defaults",
        SMART_CORE_DIR / "core" / "delivery_menu_defaults.py",
    )
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    sys.modules["odoo.addons.smart_core.core.delivery_menu_defaults"] = module
    spec.loader.exec_module(module)
    return module


class DeliveryMenuScopeRegistryTests(unittest.TestCase):
    def setUp(self):
        self.delivery_menu_defaults = _load_delivery_menu_defaults()

    def test_core_has_no_default_current_project_scope_models(self):
        self.assertEqual(self.delivery_menu_defaults._CURRENT_PROJECT_SCOPE_MODELS, set())
        self.assertIs(
            self.delivery_menu_defaults._CURRENT_RECORD_SCOPE_MODELS,
            self.delivery_menu_defaults._CURRENT_PROJECT_SCOPE_MODELS,
        )

    def test_project_model_query_is_global_until_scope_model_is_registered(self):
        node = self.delivery_menu_defaults.build_delivery_menu_child(
            {
                "menu_key": "system.menu_379",
                "label": "项目台账",
                "menu_id": 379,
                "action_id": 506,
                "model": "project.project",
                "entry_intent": "query",
            }
        )

        self.assertEqual(node["meta"]["project_scope_policy"], "global")
        self.assertEqual(node["meta"]["record_scope_policy"], "global")

    def test_current_project_scope_model_must_be_registered_explicitly(self):
        self.delivery_menu_defaults.register_current_record_scope_model("project.project")

        node = self.delivery_menu_defaults.build_delivery_menu_child(
            {
                "menu_key": "system.menu_379",
                "label": "项目台账",
                "menu_id": 379,
                "action_id": 506,
                "model": "project.project",
                "entry_intent": "query",
            }
        )

        self.assertEqual(node["meta"]["project_scope_policy"], "current_project")
        self.assertEqual(node["meta"]["record_scope_policy"], "current_record")

    def test_record_scope_policy_is_primary_and_writes_project_alias(self):
        node = self.delivery_menu_defaults.build_delivery_menu_child(
            {
                "menu_key": "system.menu_record_scoped",
                "label": "记录上下文入口",
                "menu_id": 700,
                "action_id": 800,
                "model": "x.record",
                "record_scope_policy": "current_record",
            }
        )

        self.assertEqual(node["meta"]["record_scope_policy"], "current_record")
        self.assertEqual(node["meta"]["project_scope_policy"], "current_project")

    def test_project_scope_policy_legacy_alias_writes_record_scope_policy(self):
        node = self.delivery_menu_defaults.build_delivery_menu_child(
            {
                "menu_key": "system.menu_legacy_project_scoped",
                "label": "旧项目上下文入口",
                "menu_id": 701,
                "action_id": 801,
                "model": "x.record",
                "project_scope_policy": "current_project",
            }
        )

        self.assertEqual(node["meta"]["record_scope_policy"], "current_record")
        self.assertEqual(node["meta"]["project_scope_policy"], "current_project")


if __name__ == "__main__":
    unittest.main()
