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

delivery_menu_defaults = _load_module(
    "odoo.addons.smart_core.core.delivery_menu_defaults",
    SMART_CORE_DIR / "core" / "delivery_menu_defaults.py",
)
_load_module(
    "odoo.addons.smart_core.core.source_authority",
    SMART_CORE_DIR / "core" / "source_authority.py",
)
_load_module(
    "odoo.addons.smart_core.delivery.menu_delivery_convergence_service",
    SMART_CORE_DIR / "delivery" / "menu_delivery_convergence_service.py",
)
menu_service = _load_module(
    "odoo.addons.smart_core.delivery.menu_service",
    SMART_CORE_DIR / "delivery" / "menu_service.py",
)


class TestDeliveryMenuEntryTarget(unittest.TestCase):
    def test_scene_menu_child_exposes_formal_entry_target_with_native_refs(self):
        node = delivery_menu_defaults.build_delivery_menu_child(
            {
                "menu_key": "system.menu_379",
                "label": "项目台账",
                "menu_id": 379,
                "action_id": 506,
                "route": "/s/projects.list",
                "scene_key": "projects.list",
            }
        )

        meta = node["meta"]
        self.assertEqual(meta["scene_key"], "projects.list")
        self.assertEqual(
            meta["entry_target"],
            {
                "type": "scene",
                "scene_key": "projects.list",
                "route": "/s/projects.list",
                "compatibility_refs": {
                    "menu_id": 379,
                    "action_id": 506,
                },
            },
        )

    def test_existing_entry_target_is_preserved_as_backend_authority(self):
        entry_target = {
            "type": "scene",
            "scene_key": "finance.payment_requests",
            "route": "/s/finance.payment_requests",
        }
        node = delivery_menu_defaults.build_delivery_menu_child(
            {
                "menu_key": "system.menu_payment",
                "label": "付款申请",
                "menu_id": 500,
                "action_id": 600,
                "route": "/s/finance.payment_requests",
                "scene_key": "finance.payment_requests",
                "entry_target": entry_target,
            }
        )

        self.assertEqual(node["meta"]["entry_target"], entry_target)

    def test_native_action_menu_child_exposes_compatibility_entry_target(self):
        node = delivery_menu_defaults.build_delivery_menu_child(
            {
                "menu_key": "system.menu_500",
                "label": "原生动作",
                "menu_id": 500,
                "action_id": 600,
                "model": "res.partner",
                "view_modes": ["tree", "form"],
            }
        )

        self.assertEqual(
            node["meta"]["entry_target"],
            {
                "type": "compatibility",
                "route": "/a/600",
                "compatibility_refs": {
                    "menu_id": 500,
                    "action_id": 600,
                    "model": "res.partner",
                    "view_modes": ["tree", "form"],
                },
            },
        )

    def test_policy_menu_convergence_uses_each_policy_group_label(self):
        nav = menu_service.MenuService().build_nav(
            policy={
                "menu_groups": [
                    {
                        "group_key": "construction.basic_setup",
                        "group_label": "基础设置",
                        "menus": [
                            {
                                "menu_key": "customer",
                                "label": "客户",
                                "menu_id": 598,
                                "route": "/a/786?menu_id=598",
                                "action_id": 786,
                                "res_model": "res.partner",
                            }
                        ],
                    },
                    {
                        "group_key": "construction.project_center",
                        "group_label": "项目中心",
                        "menus": [
                            {
                                "menu_key": "project",
                                "label": "项目台账",
                                "menu_id": 379,
                                "route": "/a/506?menu_id=379",
                                "action_id": 506,
                                "res_model": "project.project",
                            }
                        ],
                    },
                ]
            },
            role_surface={"role_code": "employee"},
        )

        groups = (nav[0].get("children") or []) if nav else []
        self.assertEqual([group.get("label") for group in groups], ["项目中心"])
        self.assertEqual(groups[0]["children"][0]["label"], "项目台账")


if __name__ == "__main__":
    unittest.main()
