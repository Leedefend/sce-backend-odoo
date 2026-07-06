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
    def _register_acceptance_menu_labels(self):
        for label in ("用户核对菜单", "用户验收"):
            menu_service.register_customer_acceptance_group_label(label)
            menu_service.register_preview_group_anchor_skipped_label(label)

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

    def test_project_ledger_query_menu_uses_current_project_scope(self):
        delivery_menu_defaults.register_current_project_scope_model("project.project")

        node = delivery_menu_defaults.build_delivery_menu_child(
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

    def test_non_project_query_menu_stays_global_scope(self):
        node = delivery_menu_defaults.build_delivery_menu_child(
            {
                "menu_key": "system.menu_598",
                "label": "客户",
                "menu_id": 598,
                "action_id": 786,
                "model": "res.partner",
                "entry_intent": "query",
            }
        )

        self.assertEqual(node["meta"]["project_scope_policy"], "global")
        self.assertEqual(node["meta"]["record_scope_policy"], "global")

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

    def test_policy_meta_fields_do_not_overwrite_node_key(self):
        node = delivery_menu_defaults.build_delivery_menu_child(
            {
                "menu_key": "system.policy.smart_construction_core_menu_sc_tax_certificate_registration_user",
                "label": "外经证登记",
                "action_id": 762,
                "model": "sc.legacy.payment.residual.fact",
                "route": "/a/762",
                "project_scope_policy": "current_project",
            }
        )

        self.assertEqual(
            node.get("key"),
            "system.policy.smart_construction_core_menu_sc_tax_certificate_registration_user",
        )
        self.assertNotEqual(node.get("key"), "project_scope_policy")
        self.assertEqual(node["meta"]["record_scope_policy"], "current_record")

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

    def test_business_config_role_builds_policy_menu_without_native_fact_for_release_snapshot(self):
        nav = menu_service.MenuService().build_nav(
            policy={
                "menu_groups": [
                    {
                        "group_key": "construction.master_data",
                        "group_label": "基础资料",
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
            role_surface={"role_code": "business_config_admin"},
            native_nav=[],
        )

        groups = (nav[0].get("children") or []) if nav else []
        self.assertEqual([group.get("label") for group in groups], ["基础资料"])
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

    def test_policy_menu_without_native_fact_is_not_authorized_by_env_fallback(self):
        class _Model:
            def check_access_rights(self, *_args, **_kwargs):
                return True

        class _Env:
            user = types.SimpleNamespace(groups_id=types.SimpleNamespace(ids=[]))

            def __contains__(self, key):
                return key == "project.project"

            def __getitem__(self, key):
                if key == "project.project":
                    return _Model()
                raise KeyError(key)

            def ref(self, *_args, **_kwargs):
                return types.SimpleNamespace(
                    active=True,
                    groups_id=types.SimpleNamespace(ids=[]),
                    action=types.SimpleNamespace(res_model="project.project"),
                )

        allowed = menu_service.MenuService(_Env())._policy_menu_user_authorized(
            {
                "menu_key": "project",
                "label": "项目台账",
                "menu_xmlid": "smart_construction_core.menu_project",
                "menu_id": 379,
                "route": "/a/506?menu_id=379",
                "res_model": "project.project",
            },
            {"ids": set(), "xmlids": set(), "scenes": set(), "routes": set()},
            is_admin=False,
        )

        self.assertFalse(allowed)

    def test_policy_scene_route_menu_is_allowed_when_authorized_by_route(self):
        nav = menu_service.MenuService().build_nav(
            policy={
                "menu_groups": [
                    {
                        "group_key": "construction.finance",
                        "group_label": "财务中心",
                        "menus": [
                            {
                                "menu_key": "finance_workspace",
                                "label": "财务综合办理",
                                "route": "/s/finance.workspace",
                                "scene_key": "finance.workspace",
                                "release_state": "released",
                                "enabled": True,
                            }
                        ],
                    }
                ]
            },
            role_surface={"role_code": "employee"},
            native_nav=[
                {
                    "label": "财务中心",
                    "children": [
                        self._native_leaf(
                            label="财务综合办理",
                            menu_id=540,
                            route="/s/finance.workspace",
                            scene_key="finance.workspace",
                            action_id=0,
                            model="",
                        )
                    ],
                }
            ],
        )

        groups = (nav[0].get("children") or []) if nav else []
        self.assertEqual([group.get("label") for group in groups], ["财务中心"])
        child = groups[0]["children"][0]
        self.assertEqual(child["label"], "财务综合办理")
        self.assertEqual(child["meta"]["entry_target"]["scene_key"], "finance.workspace")

    def test_user_acceptance_container_is_not_used_as_native_preview_group(self):
        self._register_acceptance_menu_labels()

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

    def test_empty_policy_native_preview_is_marked_outside_stable_menu_authority(self):
        nav = menu_service.MenuService().build_nav(
            policy={},
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

        service = menu_service.MenuService()
        meta = service.describe_nav(nav)
        group = nav[0]["children"][0]
        child = group["children"][0]

        self.assertTrue(group["meta"]["native_preview"])
        self.assertEqual(group["meta"]["runtime_authority"], "native_preview_only")
        self.assertEqual(child["meta"]["scene_source"], "native_preview")
        self.assertEqual(meta["stable_group_count"], 0)
        self.assertEqual(meta["native_preview_group_count"], 1)
        self.assertEqual(meta["stable_leaf_count"], 0)
        self.assertEqual(meta["native_preview_leaf_count"], 1)

    def test_user_acceptance_policy_menu_keeps_legacy_subgroups(self):
        self._register_acceptance_menu_labels()

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

    def test_merge_by_category_preserves_distinct_business_entry_targets(self):
        common = {
            "res_model": "sc.expense.claim",
            "integration_model": "sc.expense.claim",
            "integration_action_id": 626,
            "integration_action_xmlid": "smart_construction_core.action_sc_expense_claim",
            "integration_view_modes": ["tree", "form"],
            "integration_entry_target": {
                "type": "compatibility",
                "route": "/a/626",
                "compatibility_refs": {"action_id": 626, "model": "sc.expense.claim"},
            },
            "entry_intent": "handling",
            "entry_intent_label": "办理",
            "disposition_policy": "merge_by_category",
            "release_state": "released",
            "enabled": True,
        }
        nav = menu_service.MenuService().build_nav(
            policy={
                "menu_groups": [
                    {
                        "group_key": "construction.finance",
                        "group_label": "财务中心",
                        "menus": [
                            {
                                **common,
                                "menu_key": "expense",
                                "label": "费用/保证金申请",
                                "menu_id": 700,
                                "route": "/a/626?menu_id=700",
                                "action_id": 626,
                                "menu_xmlid": "smart_construction_core.menu_sc_expense_claim",
                                "integration_target": "sc.expense.claim 费用/保证金申请",
                                "default_business_category_code": "finance.expense.reimbursement",
                                "allowed_business_category_codes": ["finance.expense.reimbursement"],
                            },
                            {
                                **common,
                                "menu_key": "deposit_refund",
                                "label": "保证金退回",
                                "menu_id": 732,
                                "route": "/a/813?menu_id=732",
                                "action_id": 813,
                                "menu_xmlid": "smart_construction_core.menu_sc_deposit_refund",
                                "integration_target": "sc.expense.claim 保证金退回",
                                "default_business_category_code": "finance.deposit.bid.return",
                                "allowed_business_category_codes": ["finance.deposit.bid.return"],
                            },
                        ],
                    }
                ]
            },
            role_surface={"role_code": "employee"},
            native_nav=[
                {
                    "label": "财务中心",
                    "children": [
                        self._native_leaf(
                            label="费用/保证金申请",
                            menu_id=700,
                            route="/a/626?menu_id=700",
                            action_id=626,
                            model="sc.expense.claim",
                            menu_xmlid="smart_construction_core.menu_sc_expense_claim",
                        ),
                        self._native_leaf(
                            label="保证金退回",
                            menu_id=732,
                            route="/a/813?menu_id=732",
                            action_id=813,
                            model="sc.expense.claim",
                            menu_xmlid="smart_construction_core.menu_sc_deposit_refund",
                        ),
                    ],
                }
            ],
        )

        labels = [
            child.get("label")
            for group in (nav[0].get("children") or [])
            for child in (group.get("children") or [])
        ]
        self.assertIn("费用/保证金申请", labels)
        self.assertIn("保证金退回", labels)
        expense_node = next(
            child
            for group in (nav[0].get("children") or [])
            for child in (group.get("children") or [])
            if child.get("label") == "费用/保证金申请"
        )
        self.assertEqual(expense_node.get("route"), "/a/626")
        self.assertEqual(expense_node.get("action_id"), 626)
        self.assertEqual(expense_node.get("model"), "sc.expense.claim")
        self.assertEqual((expense_node.get("meta") or {}).get("record_scope_policy"), "current_record")
        self.assertEqual((expense_node.get("meta") or {}).get("project_scope_policy"), "current_project")
        self.assertEqual((expense_node.get("entry_target") or {}).get("type"), "compatibility")
        self.assertEqual(
            ((expense_node.get("entry_target") or {}).get("compatibility_refs") or {}).get("model"),
            "sc.expense.claim",
        )

    def test_explicit_menu_path_group_stays_directory_not_handling_entry(self):
        common = {
            "res_model": "sc.receipt.income",
            "integration_model": "sc.receipt.income",
            "integration_action_id": 778,
            "integration_action_xmlid": "smart_construction_core.action_sc_receipt_income",
            "integration_view_modes": ["tree", "form"],
            "integration_entry_target": {
                "type": "compatibility",
                "route": "/a/778",
                "compatibility_refs": {"action_id": 778, "model": "sc.receipt.income"},
            },
            "entry_intent": "handling",
            "entry_intent_label": "办理",
            "disposition_policy": "merge_by_category",
            "integration_target": "sc.receipt.income 收款登记",
            "release_state": "released",
            "enabled": True,
        }
        nav = menu_service.MenuService().build_nav(
            policy={
                "menu_groups": [
                    {
                        "group_key": "construction.finance",
                        "group_label": "财务中心",
                        "menus": [
                            {
                                **common,
                                "menu_key": "receipt",
                                "label": "收入",
                                "menu_id": 539,
                                "route": "/a/778?menu_id=539",
                                "action_id": 778,
                                "menu_xmlid": "smart_construction_core.menu_sc_user_income",
                                "visible_menu_path": "智慧施工管理平台 / 财务中心 / 收款管理 / 收入",
                                "default_business_category_code": "finance.receipt.income.project",
                                "allowed_business_category_codes": ["finance.receipt.income.project"],
                            }
                        ],
                    }
                ]
            },
            role_surface={"role_code": "business_config_admin"},
            native_nav=[],
        )

        finance = next(group for group in (nav[0].get("children") or []) if group.get("label") == "财务中心")
        receipt_group = next(child for child in finance.get("children") or [] if child.get("label") == "收款管理")
        receipt_meta = receipt_group.get("meta") or {}
        self.assertTrue(receipt_meta.get("explicit_menu_path_group"))
        self.assertNotIn("entry_intent", receipt_meta)
        self.assertNotIn("entry_target", receipt_meta)
        self.assertNotIn("business_entry_group", receipt_meta)
        leaf = receipt_group["children"][0]
        self.assertEqual(leaf.get("label"), "收款登记")
        self.assertEqual((leaf.get("meta") or {}).get("entry_intent"), "handling")


if __name__ == "__main__":
    unittest.main()
