# -*- coding: utf-8 -*-
import importlib.util
import sys
import types
import unittest
from pathlib import Path


CORE_DIR = Path(__file__).resolve().parents[1] / "core"
NODE_MODULE_PATH = CORE_DIR / "scene_nav_node_defaults.py"
GROUP_MODULE_PATH = CORE_DIR / "scene_nav_grouping_helper.py"


def _load_module(module_name: str, module_path: Path):
    spec = importlib.util.spec_from_file_location(module_name, module_path)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


node_module = _load_module("odoo.addons.smart_core.core.scene_nav_node_defaults", NODE_MODULE_PATH)
sys.modules.setdefault("odoo", types.ModuleType("odoo"))
sys.modules.setdefault("odoo.addons", types.ModuleType("odoo.addons"))
sys.modules.setdefault("odoo.addons.smart_core", types.ModuleType("odoo.addons.smart_core"))
core_pkg = sys.modules.setdefault("odoo.addons.smart_core.core", types.ModuleType("odoo.addons.smart_core.core"))
core_pkg.__path__ = [str(CORE_DIR)]
sys.modules["odoo.addons.smart_core.core.scene_nav_node_defaults"] = node_module

TARGET = _load_module("odoo.addons.smart_core.core.scene_nav_grouping_helper", GROUP_MODULE_PATH)
build_scene_nav_grouped_nodes = TARGET.build_scene_nav_grouped_nodes
resolve_scene_nav_group_key = TARGET.resolve_scene_nav_group_key


class TestSceneNavGroupingHelper(unittest.TestCase):
    def test_resolve_scene_nav_group_key_uses_alias(self):
        self.assertEqual(resolve_scene_nav_group_key("project.management", {"project": "projects"}), "projects")
        self.assertEqual(resolve_scene_nav_group_key("", {"project": "projects"}), "others")

    def test_build_scene_nav_grouped_nodes(self):
        leaves = [
            {"scene_key": "projects.list", "label": "项目列表"},
            {"scene_key": "project.management", "label": "项目驾驶舱"},
            {"scene_key": "workspace.home", "label": "工作台"},
        ]
        grouped = build_scene_nav_grouped_nodes(
            leaves,
            group_labels={"projects": "项目", "workspace": "工作台"},
            group_order={"projects": 1, "workspace": 2},
            group_aliases={"project": "projects"},
        )
        self.assertEqual(grouped[0]["key"], "group:projects")
        self.assertEqual(grouped[0]["children"][0]["label"], "项目列表")
        self.assertEqual(grouped[0]["children"][1]["label"], "项目驾驶舱")
        self.assertEqual(grouped[1]["key"], "group:workspace")


if __name__ == "__main__":
    unittest.main()
