# -*- coding: utf-8 -*-
import copy
import importlib.util
import sys
import types
import unittest
from pathlib import Path


DELIVERY_DIR = Path(__file__).resolve().parents[1] / "delivery"
CORE_DIR = Path(__file__).resolve().parents[1] / "core"


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
smart_core_pkg.__path__ = [str(DELIVERY_DIR.parent)]
core_pkg = sys.modules.setdefault("odoo.addons.smart_core.core", types.ModuleType("odoo.addons.smart_core.core"))
core_pkg.__path__ = [str(CORE_DIR)]
delivery_pkg = sys.modules.setdefault("odoo.addons.smart_core.delivery", types.ModuleType("odoo.addons.smart_core.delivery"))
delivery_pkg.__path__ = [str(DELIVERY_DIR)]
smart_core_pkg.core = core_pkg
smart_core_pkg.delivery = delivery_pkg

delivery_menu_defaults = _load_module(
    "odoo.addons.smart_core.core.delivery_menu_defaults",
    CORE_DIR / "delivery_menu_defaults.py",
)
core_pkg.delivery_menu_defaults = delivery_menu_defaults

target = _load_module(
    "odoo.addons.smart_core.delivery.menu_service",
    DELIVERY_DIR / "menu_service.py",
)


class TestDeliveryMenuServiceNativePreview(unittest.TestCase):
    def setUp(self):
        self.service = target.MenuService()
        self.policy = {
            "menu_groups": [
                {
                    "group_key": "released_products",
                    "group_label": "已发布产品",
                    "menus": [
                        {
                            "menu_key": "release.fr1.project_intake",
                            "label": "FR-1 项目立项",
                            "route": "/s/projects.intake",
                            "scene_key": "projects.intake",
                            "product_key": "fr1",
                            "capability_key": "delivery.fr1.project_intake",
                        }
                    ],
                },
                {
                    "group_key": "released_utilities",
                    "group_label": "工作辅助",
                    "menus": [
                        {
                            "menu_key": "release.my_work",
                            "label": "我的工作",
                            "route": "/my-work",
                            "scene_key": "my_work.workspace",
                            "product_key": "my_work",
                            "capability_key": "delivery.my_work.workspace",
                        }
                    ],
                },
            ]
        }

    def test_build_nav_appends_native_preview_group_for_raw_native_menu_leaves(self):
        native_nav = [
            {
                "key": "menu:100",
                "children": [
                    {
                        "key": "menu:200",
                        "menu_id": 200,
                        "label": "项目中心",
                        "children": [
                            {
                                "key": "menu:201",
                                "menu_id": 201,
                                "label": "项目立项",
                                "scene_key": "projects.intake",
                                "children": [],
                                "meta": {"scene_key": "projects.intake", "menu_xmlid": "smart_construction_core.menu_sc_project_center", "scene_source": "native_nav", "action_id": 501, "route": "/s/projects.intake"},
                            },
                            {
                                "key": "menu:202",
                                "menu_id": 202,
                                "label": "项目列表",
                                "scene_key": "projects.list",
                                "children": [],
                                "meta": {"scene_key": "projects.list", "menu_xmlid": "smart_construction_core.menu_sc_project_list", "scene_source": "native_nav", "action_id": 502},
                            },
                            {
                                "key": "menu:203",
                                "menu_id": 203,
                                "label": "我的工作",
                                "scene_key": "my_work.workspace",
                                "children": [],
                                "meta": {"scene_key": "my_work.workspace", "menu_xmlid": "smart_construction_core.menu_sc_my_work", "scene_source": "native_nav", "action_id": 503},
                            },
                            {
                                "key": "menu:204",
                                "menu_id": 204,
                                "label": "合同台账",
                                "children": [],
                                "meta": {"menu_xmlid": "smart_construction_core.menu_sc_contract_ledger", "scene_source": "native_nav", "action_id": 504, "model": "construction.contract"},
                            },
                        ],
                    }
                ],
            }
        ]

        nav = self.service.build_nav(policy=self.policy, role_surface={"role_code": "pm"}, native_nav=native_nav)

        root = nav[0]
        self.assertEqual(root["key"], "root:system_menu")
        self.assertEqual(root["label"], "系统菜单")
        groups = root["children"]
        self.assertEqual(len(groups), 1)
        self.assertEqual(groups[0]["label"], "项目中心")
        merged_children = groups[0]["children"]
        self.assertEqual(len(merged_children), 4)
        self.assertEqual(merged_children[0]["menu_id"], 201)
        self.assertEqual(merged_children[1]["label"], "项目列表")
        self.assertEqual(merged_children[1]["menu_id"], 202)
        self.assertEqual(merged_children[3]["label"], "合同台账")
        self.assertEqual(merged_children[3]["meta"]["action_id"], 504)
        self.assertEqual(merged_children[3]["meta"]["model"], "construction.contract")
        self.assertEqual(merged_children[0]["meta"]["route"], "/s/projects.intake")
        self.assertNotIn("release_state", merged_children[0]["meta"])
        self.assertNotIn("release_state", groups[0]["meta"])

    def test_native_preview_projection_respects_role_pruned_native_nav(self):
        native_nav = [
            {
                "key": "root:scene_contract",
                "children": [
                    {
                        "key": "group:role_primary",
                        "children": [
                            {
                                "key": "menu:202",
                                "menu_id": 202,
                                "label": "项目列表",
                                "scene_key": "projects.list",
                                "children": [],
                                "meta": {"scene_key": "projects.list", "menu_xmlid": "smart_construction_core.menu_sc_project_list", "scene_source": "native_nav", "action_id": 502},
                            }
                        ],
                    }
                ],
            }
        ]

        nav = self.service.build_nav(policy=self.policy, role_surface={"role_code": "guest"}, native_nav=native_nav)

        root = nav[0]
        groups = root["children"]
        self.assertEqual(len(groups), 1)
        children = groups[0]["children"]
        self.assertEqual(len(children), 2)
        self.assertEqual(children[0]["meta"]["scene_key"], "projects.list")
        self.assertEqual(children[1]["meta"]["scene_key"], "my_work.workspace")

    def test_native_preview_projection_falls_back_to_policy_scene_route(self):
        policy = copy.deepcopy(self.policy)
        policy["scenes"] = [
            {
                "scene_key": "project.management",
                "route": "/s/project.management",
            }
        ]
        native_nav = [
            {
                "key": "root:scene_contract",
                "children": [
                    {
                        "key": "group:role_primary",
                        "children": [
                            {
                                "key": "menu:212",
                                "menu_id": 212,
                                "label": "项目驾驶舱",
                                "scene_key": "project.management",
                                "children": [],
                                "meta": {
                                    "scene_key": "project.management",
                                    "menu_xmlid": "smart_construction_core.menu_sc_project_management_scene",
                                    "scene_source": "native_nav",
                                },
                            }
                        ],
                    }
                ],
            }
        ]

        nav = self.service.build_nav(policy=policy, role_surface={"role_code": "pm"}, native_nav=native_nav)
        preview_children = nav[0]["children"][0]["children"]

        self.assertEqual(preview_children[0]["label"], "项目驾驶舱")
        self.assertEqual(preview_children[0]["meta"]["scene_key"], "project.management")
        self.assertEqual(preview_children[0]["meta"]["route"], "/s/project.management")

    def test_native_preview_projection_uses_leaf_level_action_context(self):
        native_nav = [
            {
                "key": "root:scene_contract",
                "children": [
                    {
                        "key": "group:role_primary",
                        "children": [
                            {
                                "key": "menu:260",
                                "menu_id": 260,
                                "label": "合同看板",
                                "children": [],
                                "action_id": 860,
                                "action_xmlid": "smart_construction_core.action_contract_board",
                                "model": "construction.contract",
                                "view_modes": ["kanban", "tree"],
                                "meta": {"menu_xmlid": "smart_construction_core.menu_contract_board", "scene_source": "native_nav"},
                            }
                        ],
                    }
                ],
            }
        ]

        nav = self.service.build_nav(policy=self.policy, role_surface={"role_code": "pm"}, native_nav=native_nav)
        child = nav[0]["children"][0]["children"][0]

        self.assertEqual(child["meta"]["action_id"], 860)
        self.assertEqual(child["meta"]["action_xmlid"], "smart_construction_core.action_contract_board")
        self.assertEqual(child["meta"]["model"], "construction.contract")
        self.assertEqual(child["meta"]["view_modes"], ["kanban", "tree"])

    def test_describe_nav_exposes_stable_and_preview_counts(self):
        native_nav = [
            {
                "key": "root:scene_contract",
                "children": [
                    {
                        "key": "group:role_primary",
                        "children": [
                            {
                                "key": "menu:202",
                                "menu_id": 202,
                                "label": "项目列表",
                                "scene_key": "projects.list",
                                "children": [],
                                "meta": {"scene_key": "projects.list", "menu_xmlid": "smart_construction_core.menu_sc_project_list", "scene_source": "native_nav", "action_id": 502},
                            },
                            {
                                "key": "menu:205",
                                "menu_id": 205,
                                "label": "工作台",
                                "scene_key": "workspace.home",
                                "children": [],
                                "meta": {"scene_key": "workspace.home", "menu_xmlid": "smart_construction_core.menu_sc_workspace", "scene_source": "native_nav", "action_id": 505},
                            }
                        ],
                    }
                ],
            }
        ]

        nav = self.service.build_nav(policy=self.policy, role_surface={"role_code": "pm"}, native_nav=native_nav)
        meta = self.service.describe_nav(nav)

        self.assertEqual(meta["group_count"], 1)
        self.assertEqual(meta["stable_group_count"], 1)
        self.assertEqual(meta["native_preview_group_count"], 0)
        self.assertEqual(meta["stable_leaf_count"], 3)
        self.assertEqual(meta["native_preview_leaf_count"], 0)
        self.assertEqual(meta["native_preview_group_key"], "")
        self.assertEqual(meta["group_keys"], ["system.ungrouped"])


if __name__ == "__main__":
    unittest.main()
