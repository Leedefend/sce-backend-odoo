# -*- coding: utf-8 -*-
import importlib.util
import sys
import types
import unittest
from pathlib import Path


SMART_CORE_DIR = Path(__file__).resolve().parents[1]


def _load_module(module_name: str, path: Path):
    spec = importlib.util.spec_from_file_location(module_name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


sys.modules.setdefault("odoo", types.ModuleType("odoo"))
sys.modules.setdefault("odoo.addons", types.ModuleType("odoo.addons"))
smart_core_pkg = sys.modules.setdefault("odoo.addons.smart_core", types.ModuleType("odoo.addons.smart_core"))
smart_core_pkg.__path__ = [str(SMART_CORE_DIR)]
delivery_pkg = sys.modules.setdefault("odoo.addons.smart_core.delivery", types.ModuleType("odoo.addons.smart_core.delivery"))
delivery_pkg.__path__ = [str(SMART_CORE_DIR / "delivery")]

menu_target_interpreter_service = _load_module(
    "odoo.addons.smart_core.delivery.menu_target_interpreter_service",
    SMART_CORE_DIR / "delivery" / "menu_target_interpreter_service.py",
)

MenuTargetInterpreterService = menu_target_interpreter_service.MenuTargetInterpreterService


class TestMenuTargetInterpreterEntryTarget(unittest.TestCase):
    def test_scene_node_exposes_formal_entry_target(self):
        service = MenuTargetInterpreterService(env=None)
        nav_fact = {
            "flat": [
                {
                    "menu_id": 11,
                    "key": "menu:11",
                    "name": "项目台账",
                    "has_children": False,
                    "action_raw": "ir.actions.act_window,484",
                    "action_type": "ir.actions.act_window",
                    "action_id": 484,
                    "action_exists": True,
                    "action_meta": {},
                }
            ],
            "tree": [],
        }

        explained = service.interpret(
            nav_fact,
            scene_map={"menu_id_to_scene": {"11": "projects.list"}},
            policy={},
        )
        row = explained["flat"][0]

        self.assertEqual(row["target_type"], "scene")
        self.assertEqual(row["scene_key"], "projects.list")
        self.assertEqual(row["native_action_id"], 484)
        self.assertIsNone(row["native_model"])
        self.assertIsNone(row["native_view_mode"])
        self.assertEqual(row["confidence"], "high")
        self.assertFalse(row["compatibility_used"])
        self.assertEqual(row["route"], "/s/projects.list")
        self.assertEqual(
            row["entry_target"],
            {
                "type": "scene",
                "scene_key": "projects.list",
                "route": "/s/projects.list",
            },
        )

    def test_native_node_exposes_compatibility_entry_target(self):
        service = MenuTargetInterpreterService(env=None)
        nav_fact = {
            "flat": [
                {
                    "menu_id": 12,
                    "key": "menu:12",
                    "name": "原生动作",
                    "has_children": False,
                    "action_raw": "ir.actions.server,501",
                    "action_type": "ir.actions.server",
                    "action_id": 501,
                    "action_exists": True,
                    "action_meta": {},
                }
            ],
            "tree": [],
        }

        explained = service.interpret(nav_fact, scene_map={}, policy={})
        row = explained["flat"][0]

        self.assertEqual(row["target_type"], "native")
        self.assertIsNone(row["scene_key"])
        self.assertEqual(row["native_action_id"], 501)
        self.assertIsNone(row["native_model"])
        self.assertIsNone(row["native_view_mode"])
        self.assertEqual(row["confidence"], "medium")
        self.assertTrue(row["compatibility_used"])
        self.assertEqual(row["route"], "/native/action/501?menu_id=12")
        self.assertEqual(
            row["entry_target"],
            {
                "type": "compatibility",
                "route": "/native/action/501?menu_id=12",
                "compatibility_refs": {
                    "menu_id": 12,
                    "action_id": 501,
                    "target_type": "native",
                    "delivery_mode": "native_bridge",
                },
            },
        )

    def test_scene_node_prefers_registry_route_when_supplied(self):
        service = MenuTargetInterpreterService(env=None)
        nav_fact = {
            "flat": [
                {
                    "menu_id": 21,
                    "key": "menu:21",
                    "name": "财务中心",
                    "has_children": False,
                    "action_raw": "ir.actions.act_window,621",
                    "action_type": "ir.actions.act_window",
                    "action_id": 621,
                    "action_exists": True,
                    "action_meta": {},
                }
            ],
            "tree": [],
        }

        explained = service.interpret(
            nav_fact,
            scene_map={
                "entries": [
                    {
                        "code": "finance.center",
                        "target": {
                            "route": "/s/finance.workspace",
                            "menu_id": 21,
                            "action_id": 621,
                        },
                    }
                ]
            },
            policy={},
        )
        row = explained["flat"][0]

        self.assertEqual(row["target_type"], "scene")
        self.assertEqual(row["route"], "/s/finance.workspace")
        self.assertEqual(row["entry_target"]["route"], "/s/finance.workspace")

    def test_custom_action_node_with_model_view_scene_map_exposes_scene_entry_target(self):
        service = MenuTargetInterpreterService(env=None)
        nav_fact = {
            "flat": [
                {
                    "menu_id": 31,
                    "key": "menu:31",
                    "name": "企业信息",
                    "has_children": False,
                    "action_raw": "ir.actions.act_window,246",
                    "action_type": "ir.actions.act_window",
                    "action_id": 246,
                    "action_exists": True,
                    "action_meta": {
                        "res_model": "res.company",
                        "view_mode": "form",
                    },
                }
            ],
            "tree": [],
        }

        explained = service.interpret(
            nav_fact,
            scene_map={
                "entries": [
                    {
                        "code": "enterprise.company",
                        "target": {
                            "route": "/s/enterprise.company",
                            "model": "res.company",
                            "view_type": "form",
                        },
                    }
                ]
            },
            policy={},
        )
        row = explained["flat"][0]

        self.assertEqual(row["target_type"], "scene")
        self.assertEqual(row["delivery_mode"], "custom_scene")
        self.assertEqual(row["scene_key"], "enterprise.company")
        self.assertEqual(row["native_action_id"], 246)
        self.assertEqual(row["native_model"], "res.company")
        self.assertEqual(row["native_view_mode"], "form")
        self.assertEqual(row["confidence"], "high")
        self.assertFalse(row["compatibility_used"])
        self.assertEqual(row["route"], "/s/enterprise.company")
        self.assertEqual(
            row["entry_target"],
            {
                "type": "scene",
                "scene_key": "enterprise.company",
                "route": "/s/enterprise.company",
            },
        )

    def test_scene_node_does_not_leak_source_menu_action_query_identity(self):
        service = MenuTargetInterpreterService(env=None)
        nav_fact = {
            "flat": [
                {
                    "menu_id": 289,
                    "key": "menu:289",
                    "name": "脏菜单入口",
                    "has_children": False,
                    "action_raw": "ir.actions.act_window,486",
                    "action_type": "ir.actions.act_window",
                    "action_id": 486,
                    "action_exists": True,
                    "action_meta": {},
                }
            ],
            "tree": [],
        }

        explained = service.interpret(
            nav_fact,
            scene_map={"menu_id_to_scene": {"289": "contract.center"}},
            policy={},
        )
        row = explained["flat"][0]

        self.assertEqual(row["target_type"], "scene")
        self.assertEqual(row["route"], "/s/contract.center")
        self.assertEqual(row["scene_key"], "contract.center")
        self.assertEqual(row["native_action_id"], 486)
        self.assertEqual(row["confidence"], "high")
        self.assertFalse(row["compatibility_used"])
        self.assertEqual(
            row["entry_target"],
            {
                "type": "scene",
                "scene_key": "contract.center",
                "route": "/s/contract.center",
            },
        )

    def test_custom_action_node_exposes_native_fact_and_compatibility_marker(self):
        service = MenuTargetInterpreterService(env=None)
        nav_fact = {
            "flat": [
                {
                    "menu_id": 41,
                    "key": "menu:41",
                    "name": "原生列表",
                    "has_children": False,
                    "action_raw": "ir.actions.act_window,601",
                    "action_type": "ir.actions.act_window",
                    "action_id": 601,
                    "action_exists": True,
                    "action_meta": {
                        "res_model": "project.task",
                        "view_mode": "tree,form",
                    },
                }
            ],
            "tree": [],
        }

        explained = service.interpret(nav_fact, scene_map={}, policy={})
        row = explained["flat"][0]

        self.assertEqual(row["target_type"], "action")
        self.assertIsNone(row["scene_key"])
        self.assertEqual(row["native_action_id"], 601)
        self.assertEqual(row["native_model"], "project.task")
        self.assertEqual(row["native_view_mode"], "tree,form")
        self.assertEqual(row["confidence"], "medium")
        self.assertTrue(row["compatibility_used"])
        self.assertEqual(row["route"], "/a/601?menu_id=41")
        self.assertEqual(row["entry_target"]["type"], "compatibility")


if __name__ == "__main__":
    unittest.main()
