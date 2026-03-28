# -*- coding: utf-8 -*-
import importlib.util
import sys
import types
import unittest
from pathlib import Path


VIEW_DIR = Path(__file__).resolve().parents[1] / "view"


def _load_module(module_name: str, path: Path):
    spec = importlib.util.spec_from_file_location(module_name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


sys.modules.setdefault("odoo", types.ModuleType("odoo"))
sys.modules.setdefault("odoo.addons", types.ModuleType("odoo.addons"))
sys.modules.setdefault("odoo.addons.smart_core", types.ModuleType("odoo.addons.smart_core"))
view_pkg = sys.modules.setdefault("odoo.addons.smart_core.view", types.ModuleType("odoo.addons.smart_core.view"))
view_pkg.__path__ = [str(VIEW_DIR)]

schema_module = _load_module("odoo.addons.smart_core.view.native_view_node_schema", VIEW_DIR / "native_view_node_schema.py")


class TestNativeViewNodeSchema(unittest.TestCase):
    def test_build_field_node_has_stable_keys(self):
        node = schema_module.build_field_node(name="name", string="Name", widget="char")
        self.assertEqual(node["name"], "name")
        self.assertEqual(node["string"], "Name")
        self.assertIn("visible", node)
        self.assertIn("editable", node)
        self.assertIn("options", node)

    def test_build_action_node_has_stable_defaults(self):
        node = schema_module.build_action_node(name="open_record", action_type="object")
        self.assertEqual(node["type"], "object")
        self.assertEqual(node["context"], {})
        self.assertEqual(node["groups"], [])

    def test_build_filter_and_group_by_nodes_keep_context(self):
        filter_node = schema_module.build_filter_node(name="late", context={"default": True})
        group_node = schema_module.build_group_by_node(name="by_stage", group_by="stage_id", context={"group_by": "stage_id"})
        self.assertEqual(filter_node["context"]["default"], True)
        self.assertEqual(group_node["group_by"], "stage_id")


if __name__ == "__main__":
    unittest.main()
