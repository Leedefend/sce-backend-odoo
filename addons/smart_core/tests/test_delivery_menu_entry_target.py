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
    def _native_leaf(self, **overrides):
        row = {
            "label": overrides.get("label", "项目台账"),
            "menu_id": overrides.get("menu_id", 379),
            "route": overrides.get("route", "/a/506?menu_id=379"),
            "scene_key": overrides.get("scene_key", ""),
            "meta": {
                "menu_id": overrides.get("menu_id", 379),
                "menu_xmlid": overrides.get("menu_xmlid", ""),
                "route": overrides.get("route", "/a/506?menu_id=379"),
                "scene_key": overrides.get("scene_key", ""),
                "action_id": overrides.get("action_id", 506),
                "model": overrides.get("model", "project.project"),
            },
        }
        return row

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
            native_nav=[
                {
                    "label": "项目中心",
                    "children": [
                        self._native_leaf(
                            label="项目台账",
                            menu_id=379,
                            route="/a/506?menu_id=379",
                            action_id=506,
                            model="project.project",
                        )
                    ],
                }
            ],
        )

        groups = (nav[0].get("children") or []) if nav else []
        self.assertEqual([group.get("label") for group in groups], ["项目中心"])
        self.assertEqual(groups[0]["children"][0]["label"], "项目台账")

    def test_policy_menu_convergence_honors_business_config_admin_flag(self):
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
                    }
                ]
            },
            role_surface={"role_code": "employee", "is_business_config_admin": True},
            native_nav=[
                {
                    "label": "基础设置",
                    "children": [
                        self._native_leaf(
                            label="客户",
                            menu_id=598,
                            route="/a/786?menu_id=598",
                            action_id=786,
                            model="res.partner",
                        )
                    ],
                }
            ],
        )

        groups = (nav[0].get("children") or []) if nav else []
        self.assertEqual([group.get("label") for group in groups], ["基础设置"])
        self.assertEqual(groups[0]["children"][0]["label"], "客户")

    def test_policy_menu_surface_is_filtered_by_native_authorized_menu_fact(self):
        nav = menu_service.MenuService().build_nav(
            policy={
                "menu_groups": [
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
                            },
                            {
                                "menu_key": "finance",
                                "label": "付款申请",
                                "menu_id": 600,
                                "route": "/a/700?menu_id=600",
                                "action_id": 700,
                                "res_model": "payment.request",
                            },
                        ],
                    }
                ]
            },
            role_surface={"role_code": "employee"},
            native_nav=[
                {
                    "label": "项目中心",
                    "children": [
                        self._native_leaf(
                            label="项目台账",
                            menu_id=379,
                            route="/a/506?menu_id=379",
                            action_id=506,
                            model="project.project",
                        )
                    ],
                }
            ],
        )

        groups = (nav[0].get("children") or []) if nav else []
        labels = [child.get("label") for group in groups for child in group.get("children") or []]
        self.assertEqual(labels, ["项目台账"])

    def test_user_acceptance_container_is_not_used_as_native_preview_group(self):
        groups = menu_service.MenuService()._native_preview_menus(
            native_nav=[
                {
                    "label": "系统菜单",
                    "children": [
                        {
                            "label": "用户核对菜单",
                            "menu_id": 100,
                            "children": [
                                {
                                    "label": "基础资料",
                                    "menu_id": 101,
                                    "children": [
                                        self._native_leaf(
                                            label="供应商/合作单位",
                                            menu_id=652,
                                            route="/a/900?menu_id=652",
                                            action_id=900,
                                            model="res.partner",
                                        )
                                    ],
                                },
                                {
                                    "label": "发票税务",
                                    "menu_id": 102,
                                    "children": [
                                        self._native_leaf(
                                            label="预缴税款",
                                            menu_id=709,
                                            route="/a/901?menu_id=709",
                                            action_id=901,
                                            model="sc.prepaid.tax",
                                        )
                                    ],
                                },
                            ],
                        }
                    ],
                }
            ],
            policy={},
        )

        self.assertEqual([group.get("group_label") for group in groups], ["基础资料", "发票税务"])
        self.assertEqual([group["menus"][0]["label"] for group in groups], ["供应商/合作单位", "预缴税款"])

    def test_user_acceptance_policy_menu_keeps_legacy_subgroups(self):
        nav = menu_service.MenuService().build_nav(
            policy={
                "menu_groups": [
                    {
                        "group_key": "construction.用户核对菜单",
                        "group_label": "用户核对菜单",
                        "menus": [
                            {
                                "menu_key": "supplier",
                                "label": "供应商/合作单位",
                                "menu_id": 652,
                                "route": "/a/706?menu_id=652",
                                "action_id": 706,
                                "res_model": "res.partner",
                                "release_state": "released",
                                "enabled": True,
                                "visible_menu_path": "智慧施工管理平台 / 用户核对菜单 / 基础资料 / 供应商/合作单位",
                            },
                            {
                                "menu_key": "tax",
                                "label": "预缴税款",
                                "menu_id": 709,
                                "route": "/a/715?menu_id=709",
                                "action_id": 715,
                                "res_model": "sc.prepaid.tax",
                                "release_state": "released",
                                "enabled": True,
                                "visible_menu_path": "智慧施工管理平台 / 用户核对菜单 / 发票税务 / 预缴税款",
                            },
                        ],
                    }
                ]
            },
            role_surface={"role_code": "employee", "is_platform_admin": True},
            native_nav=[],
        )

        root_groups = nav[0].get("children") or []
        acceptance = next(group for group in root_groups if group.get("label") == "用户核对菜单")
        subgroup_labels = [group.get("label") for group in acceptance.get("children") or []]
        leaf_labels = [
            child.get("label")
            for group in acceptance.get("children") or []
            for child in group.get("children") or []
        ]
        self.assertEqual(subgroup_labels, ["基础资料", "发票税务"])
        self.assertEqual(leaf_labels, ["供应商/合作单位", "预缴税款"])


if __name__ == "__main__":
    unittest.main()
