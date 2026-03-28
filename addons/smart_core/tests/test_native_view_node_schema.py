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
        node = schema_module.build_field_node(name="name", string="Name", widget="char", semantic_role="tree_column", source_view="tree", semantic_meta={"has_widget": True})
        self.assertEqual(node["name"], "name")
        self.assertEqual(node["string"], "Name")
        self.assertEqual(node["kind"], "field")
        self.assertIn("visible", node)
        self.assertIn("editable", node)
        self.assertIn("options", node)
        self.assertEqual(node["semantic_role"], "tree_column")
        self.assertEqual(node["source_view"], "tree")
        self.assertEqual(node["semantic_meta"]["has_widget"], True)

    def test_build_action_node_has_stable_defaults(self):
        node = schema_module.build_action_node(name="open_record", action_type="object", semantic_role="kanban_card_action", source_view="kanban", semantic_meta={"target_scope": "card"})
        self.assertEqual(node["kind"], "action")
        self.assertEqual(node["type"], "object")
        self.assertEqual(node["context"], {})
        self.assertEqual(node["groups"], [])
        self.assertEqual(node["semantic_role"], "kanban_card_action")
        self.assertEqual(node["semantic_meta"]["target_scope"], "card")

    def test_build_filter_and_group_by_nodes_keep_context(self):
        filter_node = schema_module.build_filter_node(name="late", context={"default": True}, semantic_role="search_filter", source_view="search", semantic_meta={"has_context": True})
        group_node = schema_module.build_group_by_node(name="by_stage", group_by="stage_id", context={"group_by": "stage_id"}, semantic_role="search_group_by", source_view="search", semantic_meta={"context_keys": ["group_by"]})
        self.assertEqual(filter_node["kind"], "filter")
        self.assertEqual(group_node["kind"], "group_by")
        self.assertEqual(filter_node["context"]["default"], True)
        self.assertEqual(group_node["group_by"], "stage_id")
        self.assertEqual(group_node["semantic_role"], "search_group_by")
        self.assertEqual(filter_node["semantic_meta"]["has_context"], True)
        self.assertEqual(group_node["semantic_meta"]["context_keys"], ["group_by"])

    def test_build_form_container_nodes_have_stable_kinds(self):
        group_node = schema_module.build_group_node(fields=[{"name": "name"}])
        page_node = schema_module.build_page_node(title="Details")
        notebook_node = schema_module.build_notebook_node(pages=[page_node])
        self.assertEqual(group_node["kind"], "group")
        self.assertEqual(page_node["kind"], "page")
        self.assertEqual(notebook_node["kind"], "notebook")

    def test_build_form_semantic_nodes_have_stable_kinds(self):
        ribbon_node = schema_module.build_ribbon_node(title="Archived")
        chatter_node = schema_module.build_chatter_node(followers="message_follower_ids")
        self.assertEqual(ribbon_node["kind"], "ribbon")
        self.assertEqual(chatter_node["kind"], "chatter")


if __name__ == "__main__":
    unittest.main()
