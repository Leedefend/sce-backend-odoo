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
core_pkg = sys.modules.setdefault("odoo.addons.smart_core.core", types.ModuleType("odoo.addons.smart_core.core"))
core_pkg.__path__ = [str(SMART_CORE_DIR / "core")]

navigation_entry_target = _load_module(
    "odoo.addons.smart_core.core.navigation_entry_target",
    SMART_CORE_DIR / "core" / "navigation_entry_target.py",
)


class TestNavigationEntryTarget(unittest.TestCase):
    def test_scene_entry_target_carries_native_refs(self):
        entry = navigation_entry_target.normalize_entry_target(
            scene_key="projects.list",
            menu_id=379,
            action_id=506,
            model="project.project",
            view_modes=["tree", "form"],
        )

        self.assertEqual(entry["type"], "scene")
        self.assertEqual(entry["scene_key"], "projects.list")
        self.assertEqual(entry["route"], "/s/projects.list")
        self.assertEqual(
            entry["compatibility_refs"],
            {
                "menu_id": 379,
                "action_id": 506,
                "model": "project.project",
                "view_modes": ["tree", "form"],
            },
        )

    def test_action_result_is_wrapped_as_compatibility_entry_target(self):
        action = navigation_entry_target.normalize_odoo_action_result(
            None,
            {
                "type": "ir.actions.act_window",
                "id": 601,
                "res_model": "res.partner",
                "view_mode": "tree,form",
            },
        )

        self.assertEqual(action["entry_target"]["type"], "compatibility")
        self.assertEqual(action["entry_target"]["route"], "/a/601")
        self.assertEqual(
            action["entry_target"]["compatibility_refs"],
            {
                "action_id": 601,
                "model": "res.partner",
                "view_modes": ["tree", "form"],
                "target_type": "action",
                "delivery_mode": "odoo_action_result",
            },
        )

    def test_client_action_next_is_wrapped_and_promoted_to_entry_target(self):
        action = navigation_entry_target.normalize_odoo_action_result(
            None,
            {
                "type": "ir.actions.client",
                "tag": "display_notification",
                "params": {
                    "message": "ok",
                    "next": {
                        "type": "ir.actions.act_window",
                        "id": 77,
                        "res_model": "project.project",
                        "view_mode": "form",
                    },
                },
            },
        )

        self.assertEqual(action["entry_target"]["type"], "compatibility")
        self.assertEqual(action["entry_target"]["compatibility_refs"]["action_id"], 77)
        self.assertEqual(action["params"]["next"]["entry_target"], action["entry_target"])


if __name__ == "__main__":
    unittest.main()
