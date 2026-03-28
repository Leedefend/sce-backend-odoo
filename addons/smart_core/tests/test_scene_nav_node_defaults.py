# -*- coding: utf-8 -*-
import importlib.util
import unittest
from pathlib import Path


MODULE_PATH = Path(__file__).resolve().parents[1] / "core" / "scene_nav_node_defaults.py"


def _load_target_module():
    spec = importlib.util.spec_from_file_location("scene_nav_node_defaults_under_test", MODULE_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


TARGET = _load_target_module()
build_scene_nav_group_node = TARGET.build_scene_nav_group_node
build_scene_nav_leaf = TARGET.build_scene_nav_leaf
build_scene_nav_root = TARGET.build_scene_nav_root
synthetic_scene_nav_menu_id = TARGET.synthetic_scene_nav_menu_id


class TestSceneNavNodeDefaults(unittest.TestCase):
    def test_synthetic_scene_nav_menu_id_stable(self):
        self.assertEqual(synthetic_scene_nav_menu_id("scene:projects.list"), synthetic_scene_nav_menu_id("scene:projects.list"))

    def test_build_scene_nav_leaf(self):
        payload = build_scene_nav_leaf({"code": "projects.list", "name": "项目列表"})
        self.assertEqual(payload["key"], "scene:projects.list")
        self.assertEqual(payload["meta"]["menu_xmlid"], "scene.contract.projects_list")

    def test_build_scene_nav_group_and_root(self):
        leaf = build_scene_nav_leaf({"code": "projects.list", "name": "项目列表"})
        group = build_scene_nav_group_node("projects", "项目", [leaf])
        root = build_scene_nav_root([group])
        self.assertEqual(group["key"], "group:projects")
        self.assertEqual(root["key"], "root:scene_contract")
        self.assertEqual(root["children"][0]["children"][0]["scene_key"], "projects.list")


if __name__ == "__main__":
    unittest.main()
